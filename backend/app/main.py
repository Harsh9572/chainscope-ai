from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="ChainScope AI")

# API Key
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

# ---------------- HOME ----------------

@app.get("/")
def home():
    return {
        "message": "ChainScope AI Backend Running"
    }

# ---------------- CRYPTO PRICES ----------------

@app.get("/api/prices")
def get_prices():

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum&vs_currencies=usd"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return {
                "bitcoin": {"usd": 0},
                "ethereum": {"usd": 0},
                "message": "Rate limit reached"
            }

        data = response.json()

        if "status" in data and "error_code" in data["status"]:
            return {
                "bitcoin": {"usd": 0},
                "ethereum": {"usd": 0},
                "message": "Rate limit reached"
            }

        return data

    except Exception:
        return {
            "bitcoin": {"usd": 0},
            "ethereum": {"usd": 0},
            "message": "API unavailable"
        }

# ---------------- WALLET ANALYZER ----------------

@app.get("/api/wallet/{wallet_address}")
def wallet_analysis(wallet_address: str):

    url = "https://api.etherscan.io/v2/api"

    params = {
        "chainid": 1,
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params)

    return response.json()
# ---------------- TOKEN ANALYTICS ----------------

@app.get("/api/token/{token_id}")
def token_analytics(token_id: str):

    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"

    response = requests.get(url)

    data = response.json()

    return {
        "name": data["name"],
        "symbol": data["symbol"],
        "current_price": data["market_data"]["current_price"]["usd"],
        "market_cap": data["market_data"]["market_cap"]["usd"],
        "total_volume": data["market_data"]["total_volume"]["usd"],
        "high_24h": data["market_data"]["high_24h"]["usd"],
        "low_24h": data["market_data"]["low_24h"]["usd"]
    }
# ---------------- WHALE TRACKER ----------------

@app.get("/api/whales")
def whale_tracker():

    whale_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"

    url = "https://api.etherscan.io/v2/api"

    params = {
        "chainid": 1,
        "module": "account",
        "action": "txlist",
        "address": whale_wallet,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 15,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params)

    return response.json()
@app.get("/api/insights/{token_id}")
def token_insights(token_id: str):

    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"

    response = requests.get(url)

    data = response.json()

    market_cap = data["market_data"]["market_cap"]["usd"]
    volume = data["market_data"]["total_volume"]["usd"]

    if volume > 1000000000:
        insight = "High trading activity detected. Market participation is strong."

    elif volume > 100000000:
        insight = "Moderate trading activity observed."

    else:
        insight = "Relatively low trading activity."

    return {
        "token": data["name"],
        "insight": insight
    }
@app.get("/api/risk/{token_id}")
def risk_score(token_id: str):

    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"

    response = requests.get(url)

    data = response.json()

    market_cap = data["market_data"]["market_cap"]["usd"]
    volume = data["market_data"]["total_volume"]["usd"]

    if market_cap > 10000000000 and volume > 1000000000:
        risk = "Low Risk"

    elif market_cap > 1000000000:
        risk = "Medium Risk"

    else:
        risk = "High Risk"

    return {
        "token": data["name"],
        "risk": risk,
        "market_cap": market_cap,
        "volume": volume
    }