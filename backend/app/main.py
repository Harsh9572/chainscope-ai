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

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd"
    }

    response = requests.get(url, params=params)

    return response.json()

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