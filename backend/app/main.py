from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import re
import time
import threading
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chainscope")

app = FastAPI(title="ChainScope AI")

# Allow frontend(s) to call this API. Tighten allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
if not ETHERSCAN_API_KEY:
    logger.warning(
        "ETHERSCAN_API_KEY is not set. /api/wallet and /api/whales will fail until it is configured."
    )

ETHERSCAN_URL = "https://api.etherscan.io/v2/api"
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/{}"

WALLET_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# ---------------- COINGECKO CACHE ----------------
# CoinGecko's free tier has a very low, shared rate limit. Token Analytics,
# AI Insights, and Risk Assessment all request the same token independently,
# and a Streamlit rerun can re-trigger all three at once, so we cache
# successful lookups briefly and reuse them across all three endpoints.
_COINGECKO_CACHE_TTL = 45  # seconds
_coingecko_cache: dict[str, dict] = {}
_coingecko_cache_lock = threading.Lock()


def _get_cached_coingecko(token_id: str):
    with _coingecko_cache_lock:
        entry = _coingecko_cache.get(token_id)
    if entry and (time.time() - entry["ts"]) < _COINGECKO_CACHE_TTL:
        return entry["data"]
    return None


def _get_stale_coingecko(token_id: str):
    """Return cached data regardless of age, used as a rate-limit fallback."""
    with _coingecko_cache_lock:
        entry = _coingecko_cache.get(token_id)
    return entry["data"] if entry else None


def _set_cached_coingecko(token_id: str, data: dict):
    with _coingecko_cache_lock:
        _coingecko_cache[token_id] = {"data": data, "ts": time.time()}


# ---------------- ETHERSCAN CACHE ----------------
# Etherscan's free tier allows ~5 calls/sec, and the Whale Tracker in
# particular hits the same fixed address on every Streamlit rerun, so we
# cache successful txlist lookups briefly per (address, offset) and fall
# back to stale data if a fresh call gets rate-limited.
_ETHERSCAN_CACHE_TTL = 20  # seconds
_etherscan_cache: dict[tuple, dict] = {}
_etherscan_cache_lock = threading.Lock()


def _get_cached_etherscan(key: tuple):
    with _etherscan_cache_lock:
        entry = _etherscan_cache.get(key)
    if entry and (time.time() - entry["ts"]) < _ETHERSCAN_CACHE_TTL:
        return entry["data"]
    return None


def _get_stale_etherscan(key: tuple):
    """Return cached data regardless of age, used as a rate-limit fallback."""
    with _etherscan_cache_lock:
        entry = _etherscan_cache.get(key)
    return entry["data"] if entry else None


def _set_cached_etherscan(key: tuple, data: dict):
    with _etherscan_cache_lock:
        _etherscan_cache[key] = {"data": data, "ts": time.time()}


# ---------------- HELPERS ----------------

def fetch_etherscan_txlist(address: str, offset: int = 10):
    """Call Etherscan txlist endpoint with caching and proper error handling."""
    if not ETHERSCAN_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: ETHERSCAN_API_KEY is not set."
        )

    cache_key = (address.lower(), offset)
    cached = _get_cached_etherscan(cache_key)
    if cached is not None:
        return cached

    params = {
        "chainid": 1,
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": offset,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY,
    }

    try:
        response = requests.get(ETHERSCAN_URL, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        stale = _get_stale_etherscan(cache_key)
        if stale is not None:
            logger.warning(f"Etherscan unreachable; serving stale cache for {address}.")
            return stale
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach Etherscan: {str(e)}"
        )

    if response.status_code == 429:
        stale = _get_stale_etherscan(cache_key)
        if stale is not None:
            logger.warning(f"Etherscan rate-limited; serving stale cache for {address}.")
            return stale
        raise HTTPException(
            status_code=429,
            detail="Etherscan rate limit exceeded. Please try again in a moment."
        )

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        stale = _get_stale_etherscan(cache_key)
        if stale is not None:
            logger.warning(f"Etherscan error; serving stale cache for {address}.")
            return stale
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach Etherscan: {str(e)}"
        )

    data = response.json()

    # Etherscan returns HTTP 200 with status "0" on both real errors and
    # its own rate-limit message ("Max rate limit reached"), so we check
    # the message body itself rather than the status code.
    if isinstance(data, dict) and data.get("status") == "0":
        message = data.get("message", "")

        if message == "No transactions found":
            _set_cached_etherscan(cache_key, data)
            return data

        if "rate limit" in message.lower():
            stale = _get_stale_etherscan(cache_key)
            if stale is not None:
                logger.warning(f"Etherscan rate-limited; serving stale cache for {address}.")
                return stale
            raise HTTPException(
                status_code=429,
                detail="Etherscan rate limit exceeded. Please try again in a moment."
            )

        raise HTTPException(
            status_code=502,
            detail=f"Etherscan error: {message or 'Unknown error'}"
        )

    _set_cached_etherscan(cache_key, data)
    return data


def fetch_coingecko_token(token_id: str):
    """Call CoinGecko coin endpoint with caching and proper error handling."""
    cached = _get_cached_coingecko(token_id)
    if cached is not None:
        return cached

    url = COINGECKO_URL.format(token_id)

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach CoinGecko: {str(e)}"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"Token '{token_id}' not found on CoinGecko."
        )

    if response.status_code == 429:
        stale = _get_stale_coingecko(token_id)
        if stale is not None:
            logger.warning(f"CoinGecko rate-limited; serving stale cache for '{token_id}'.")
            return stale
        raise HTTPException(
            status_code=429,
            detail="CoinGecko rate limit exceeded. Please try again in a moment."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"CoinGecko returned status {response.status_code}."
        )

    data = response.json()

    if "status" in data:
        stale = _get_stale_coingecko(token_id)
        if stale is not None:
            logger.warning(f"CoinGecko rate-limited; serving stale cache for '{token_id}'.")
            return stale
        raise HTTPException(
            status_code=429,
            detail=data["status"].get(
                "error_message",
                "CoinGecko rate limit exceeded."
            )
        )

    if "market_data" not in data:
        raise HTTPException(
            status_code=502,
            detail=f"CoinGecko response missing market data for '{token_id}'."
        )

    _set_cached_coingecko(token_id, data)
    return data


# ---------------- HOME ----------------

@app.get("/")
def home():
    return {
        "message": "ChainScope AI Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ChainScope AI",
        "version": "1.0.0"
    }


# ---------------- CRYPTO PRICES ----------------

@app.get("/api/prices")
def get_prices():
    try:
        btc_response = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=10
        )
        eth_response = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
            timeout=10
        )
        btc_data = btc_response.json()
        eth_data = eth_response.json()

        if "price" not in btc_data or "price" not in eth_data:
            return {
                "success": False,
                "message": "Unable to fetch live market prices.",
                "provider_response": {
                    "bitcoin": btc_data,
                    "ethereum": eth_data
                }
            }

        return {
            "success": True,
            "bitcoin": {"usd": round(float(btc_data["price"]), 2)},
            "ethereum": {"usd": round(float(eth_data["price"]), 2)}
        }

    except Exception as e:
        logger.error(f"get_prices failed: {e}")
        return {
            "success": False,
            "bitcoin": {"usd": 0},
            "ethereum": {"usd": 0},
            "error": str(e)
        }


# ---------------- WALLET ANALYZER ----------------

@app.get("/api/wallet/{wallet_address}")
def wallet_analysis(wallet_address: str):
    if not WALLET_ADDRESS_RE.match(wallet_address):
        raise HTTPException(
            status_code=400,
            detail="Invalid Ethereum wallet address format. Expected 0x followed by 40 hex characters."
        )

    return {
        "success": True,
        "wallet": wallet_address,
        "transactions": fetch_etherscan_txlist(wallet_address, 10)
    }


# ---------------- TOKEN ANALYTICS ----------------

@app.get("/api/token/{token_id}")
def token_analytics(token_id: str):
    try:
        data = fetch_coingecko_token(token_id)
        market = data["market_data"]

        return {
            "success": True,
            "name": data.get("name"),
            "symbol": data.get("symbol", "").upper(),
            "current_price": market.get("current_price", {}).get("usd"),
            "market_cap": market.get("market_cap", {}).get("usd"),
            "total_volume": market.get("total_volume", {}).get("usd"),
            "high_24h": market.get("high_24h", {}).get("usd"),
            "low_24h": market.get("low_24h", {}).get("usd")
        }
    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail,
            "status_code": e.status_code
        }
    except Exception as e:
        logger.error(f"token_analytics failed for {token_id}: {e}")
        return {
            "success": False,
            "message": "Server error while fetching token analytics.",
            "error": str(e)
        }


# ---------------- WHALE TRACKER ----------------

@app.get("/api/whales")
def whale_tracker():
    whale_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"
    return {
        "success": True,
        "wallet": whale_wallet,
        "transactions": fetch_etherscan_txlist(whale_wallet, offset=15)
    }


# ---------------- TOKEN INSIGHTS ----------------

@app.get("/api/insights/{token_id}")
def token_insights(token_id: str):
    data = fetch_coingecko_token(token_id)

    market = data["market_data"]
    volume = market.get("total_volume", {}).get("usd")

    if volume is None:
        raise HTTPException(
            status_code=502,
            detail=f"Volume data unavailable for '{token_id}'."
        )

    if volume > 1_000_000_000:
        insight = "High trading activity detected. Market participation is strong."
    elif volume > 100_000_000:
        insight = "Moderate trading activity observed."
    else:
        insight = "Relatively low trading activity."

    return {
        "token": data.get("name"),
        "insight": insight
    }


# ---------------- RISK SCORE ----------------

@app.get("/api/risk/{token_id}")
def risk_score(token_id: str):
    data = fetch_coingecko_token(token_id)

    market = data["market_data"]
    market_cap = market.get("market_cap", {}).get("usd")
    volume = market.get("total_volume", {}).get("usd")

    if market_cap is None or volume is None:
        raise HTTPException(
            status_code=502,
            detail=f"Market cap or volume data unavailable for '{token_id}'."
        )

    if market_cap > 10_000_000_000 and volume > 1_000_000_000:
        risk = "Low Risk"
    elif market_cap > 1_000_000_000:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    return {
        "token": data.get("name"),
        "risk": risk,
        "market_cap": market_cap,
        "volume": volume
    }
