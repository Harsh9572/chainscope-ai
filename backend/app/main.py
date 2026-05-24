from fastapi import FastAPI
import requests

app = FastAPI(title="ChainScope AI")

@app.get("/")
def home():
    return {"message": "ChainScope AI Backend Running"}

@app.get("/api/prices")
def get_prices():

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd"
    }

    response = requests.get(url, params=params)

    return response.json()