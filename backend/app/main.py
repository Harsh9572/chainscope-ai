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

COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
if not COINMARKETCAP_API_KEY:
    logger.warning(
        "COINMARKETCAP_API_KEY is not set. /api/token, /api/insights, and /api/risk will fail until it is configured."
    )

ETHERSCAN_URL = "https://api.etherscan.io/v2/api"
CMC_QUOTES_URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
CMC_OHLCV_URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/latest"

WALLET_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# ---------------- CMC TOKEN CACHE ----------------
# CoinMarketCap's free/Basic tier has a limited request budget shared across
# Token Analytics, AI Insights, and Risk Assessment, which all look up the
# same token independently. We cache the normalized result briefly and
# reuse it across all three endpoints, falling back to stale data if a
# fresh call gets rate-limited.
_CMC_CACHE_TTL = 45  # seconds
_cmc_cache: dict[str, dict] = {}
_cmc_cache_lock = threading.Lock()


def _get_cached_cmc(token_id: str):
    with _cmc_cache_lock:
        entry = _cmc_cache.get(token_id)
    if entry and (time.time() - entry["ts"]) < _CMC_CACHE_TTL:
        return entry["data"]
    return None


def _get_stale_cmc(token_id: str):
    """Return cached data regardless of age, used as a rate-limit fallback."""
    with _cmc_cache_lock:
        entry = _cmc_cache.get(token_id)
    return entry["data"] if entry else None


def _set_cached_cmc(token_id: str, data: dict):
    with _cmc_cache_lock:
        _cmc_cache[token_id] = {"data": data, "ts": time.time()}


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


def _cmc_estimate_high_low(price, percent_change_24h):
    """
    CoinMarketCap's standard quotes/latest endpoint (Basic/free plan) does
    not return true intraday high/low like CoinGecko did — that requires
    the paid OHLCV endpoint. As a fallback, we approximate a 24h range
    using the current price and percent_change_24h (i.e. price vs. price
    24h ago), which is not the same as a true high/low but keeps the
    frontend populated with a reasonable range instead of $0.
    """
    if price is None or percent_change_24h is None:
        return None, None
    try:
        denom = 1 + (percent_change_24h / 100)
        if denom == 0:
            return price, price
        price_24h_ago = price / denom
        return max(price, price_24h_ago), min(price, price_24h_ago)
    except (TypeError, ZeroDivisionError):
        return None, None


def _cmc_fetch_ohlcv_high_low(cmc_id):
    """
    Attempt the true OHLCV latest endpoint for exact high/low. This is
    only available on some CMC plans, so any failure here is expected
    and the caller falls back to the percent-change estimate.
    """
    try:
        response = requests.get(
            CMC_OHLCV_URL,
            headers={"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY, "Accept": "application/json"},
            params={"id": cmc_id, "convert": "USD"},
            timeout=10
        )
        if response.status_code != 200:
            return None, None
        data = response.json()
        coin = data.get("data", {}).get(str(cmc_id))
        if not coin:
            return None, None
        quote = coin.get("quote", {}).get("USD", {})
        return quote.get("high"), quote.get("low")
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return None, None


def fetch_token_metadata(token_id: str):
    """
    Fetch normalized token metadata from CoinMarketCap, with caching and
    proper error handling. Returns a flat dict with the same field names
    the rest of the app already expects: name, symbol, current_price,
    market_cap, total_volume, high_24h, low_24h.
    """
    cached = _get_cached_cmc(token_id)
    if cached is not None:
        return cached

    if not COINMARKETCAP_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: COINMARKETCAP_API_KEY is not set."
        )

    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY, "Accept": "application/json"}
    # CMC's "slug" matches the lowercase token ids already used throughout
    # this app (e.g. "bitcoin", "ethereum", "solana"), so no frontend or
    # caller changes are needed here.
    params = {"slug": token_id, "convert": "USD"}

    try:
        response = requests.get(CMC_QUOTES_URL, headers=headers, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        stale = _get_stale_cmc(token_id)
        if stale is not None:
            logger.warning(f"CoinMarketCap unreachable; serving stale cache for '{token_id}'.")
            return stale
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach CoinMarketCap: {str(e)}"
        )

    if response.status_code == 429:
        stale = _get_stale_cmc(token_id)
        if stale is not None:
            logger.warning(f"CoinMarketCap rate-limited; serving stale cache for '{token_id}'.")
            return stale
        raise HTTPException(
            status_code=429,
            detail="CoinMarketCap rate limit exceeded. Please try again in a moment."
        )

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=500,
            detail="CoinMarketCap rejected the request. Check COINMARKETCAP_API_KEY."
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=404,
            detail=f"Token '{token_id}' not found on CoinMarketCap."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"CoinMarketCap returned status {response.status_code}."
        )

    body = response.json()
    status = body.get("status", {})

    if status.get("error_code"):
        error_code = status.get("error_code")
        error_message = status.get("error_message") or "Unknown CoinMarketCap error."

        if error_code == 400:
            raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found on CoinMarketCap.")

        if error_code == 1010:  # rate limit
            stale = _get_stale_cmc(token_id)
            if stale is not None:
                logger.warning(f"CoinMarketCap rate-limited; serving stale cache for '{token_id}'.")
                return stale
            raise HTTPException(status_code=429, detail="CoinMarketCap rate limit exceeded.")

        raise HTTPException(status_code=502, detail=f"CoinMarketCap error: {error_message}")

    coin_map = body.get("data", {})
    if not coin_map:
        raise HTTPException(
            status_code=404,
            detail=f"Token '{token_id}' not found on CoinMarketCap."
        )

    # Response is keyed by CMC's internal numeric id even when queried by slug.
    coin = next(iter(coin_map.values()))
    quote = coin.get("quote", {}).get("USD", {})

    price = quote.get("price")
    market_cap = quote.get("market_cap")
    total_volume = quote.get("volume_24h")
    percent_change_24h = quote.get("percent_change_24h")

    high_24h, low_24h = _cmc_fetch_ohlcv_high_low(coin.get("id"))
    if high_24h is None or low_24h is None:
        high_24h, low_24h = _cmc_estimate_high_low(price, percent_change_24h)

    normalized = {
        "name": coin.get("name"),
        "symbol": coin.get("symbol"),
        "current_price": price,
        "market_cap": market_cap,
        "total_volume": total_volume,
        "high_24h": high_24h,
        "low_24h": low_24h,
    }

    _set_cached_cmc(token_id, normalized)
    return normalized


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
        data = fetch_token_metadata(token_id)

        return {
            "success": True,
            "name": data.get("name"),
            "symbol": (data.get("symbol") or "").upper(),
            "current_price": data.get("current_price"),
            "market_cap": data.get("market_cap"),
            "total_volume": data.get("total_volume"),
            "high_24h": data.get("high_24h"),
            "low_24h": data.get("low_24h")
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
    data = fetch_token_metadata(token_id)

    volume = data.get("total_volume")

    if volume is None:
        raise HTTPException(
            status_code=502,
            detail=f"Volume data unavailable for '{token_id}'."
        )

    # AI Insights: own backend logic, independent of the metadata provider.
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
    data = fetch_token_metadata(token_id)

    market_cap = data.get("market_cap")
    volume = data.get("total_volume")

    if market_cap is None or volume is None:
        raise HTTPException(
            status_code=502,
            detail=f"Market cap or volume data unavailable for '{token_id}'."
        )

    # Risk Assessment: own backend logic, independent of the metadata provider.
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
