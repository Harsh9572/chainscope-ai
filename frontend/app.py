import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="ChainScope AI",
    page_icon="🚀",
    layout="wide"
)

# ---------------- SIDEBAR ----------------

st.sidebar.title("🚀 ChainScope AI")

st.sidebar.success("Connected to Blockchain APIs")

st.sidebar.markdown("---")

st.sidebar.subheader("Platform Features")

st.sidebar.write("✅ Real-Time Market Prices")
st.sidebar.write("✅ Blockchain Analytics")
st.sidebar.write("✅ Whale Tracking")
st.sidebar.write("✅ Wallet Intelligence")
st.sidebar.write("✅ AI Insights")

st.sidebar.markdown("---")

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.sidebar.caption(f"Last Updated: {current_time}")

# ---------------- TITLE ----------------

st.title("🚀 ChainScope AI")

st.subheader("Real-Time Blockchain Intelligence Platform")

st.info("Live crypto market tracking enabled")

# ---------------- REFRESH BUTTON ----------------

if st.button("🔄 Refresh Data"):
    st.rerun()

# ---------------- FETCH DATA ----------------

backend_url = "http://127.0.0.1:8000/api/prices"

response = requests.get(backend_url)

data = response.json()

btc_price = data["bitcoin"]["usd"]
eth_price = data["ethereum"]["usd"]

# ---------------- METRICS ----------------

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Bitcoin Price",
        value=f"${btc_price}"
    )

with col2:
    st.metric(
        label="Ethereum Price",
        value=f"${eth_price}"
    )

# ---------------- CHART DATA ----------------

chart_data = pd.DataFrame({
    "Coin": ["Bitcoin", "Ethereum"],
    "Price": [btc_price, eth_price]
})

# ---------------- BAR CHART ----------------

fig = px.bar(
    chart_data,
    x="Coin",
    y="Price",
    title="Crypto Market Prices",
    text="Price"
)

fig.update_traces(textposition="outside")

st.plotly_chart(fig, width="stretch")

# ---------------- MARKET TABLE ----------------

st.subheader("📊 Market Overview")

table_data = pd.DataFrame({
    "Coin": ["Bitcoin", "Ethereum"],
    "Price (USD)": [btc_price, eth_price]
})

st.dataframe(table_data, width="stretch")
# ---------------- WALLET ANALYZER ----------------

st.markdown("---")

st.header("🧠 Wallet Intelligence Analyzer")

wallet_address = st.text_input(
    "Enter Ethereum Wallet Address"
)

if wallet_address:

    wallet_api = f"http://127.0.0.1:8000/api/wallet/{wallet_address}"

    wallet_response = requests.get(wallet_api)

    wallet_data = wallet_response.json()

    transactions = wallet_data.get("result", [])

    if transactions:

        st.success("Wallet data fetched successfully")

        tx_table = []

        for tx in transactions[:10]:

            tx_table.append({
                "Hash": tx["hash"][:12] + "...",
                "From": tx["from"][:10] + "...",
                "To": tx["to"][:10] + "...",
                "Value (ETH)": round(
                    int(tx["value"]) / 10**18,
                    5
                )
            })

        tx_df = pd.DataFrame(tx_table)

        st.dataframe(
            tx_df,
            width="stretch"
        )

    else:
        st.warning("No transactions found")
# ---------------- TOKEN ANALYTICS ----------------

st.markdown("---")

st.header("📈 Token Analytics")

token_input = st.text_input(
    "Enter Token ID (example: bitcoin, ethereum, solana)"
)

if token_input:

    token_api = f"http://127.0.0.1:8000/api/token/{token_input}"

    token_response = requests.get(token_api)

    token_data = token_response.json()

    st.success(f"Showing analytics for {token_data['name']}")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Current Price",
            f"${token_data['current_price']:,}"
        )

        st.metric(
            "24H High",
            f"${token_data['high_24h']:,}"
        )

    with col2:
        st.metric(
            "Market Cap",
            f"${token_data['market_cap']:,}"
        )

        st.metric(
            "24H Low",
            f"${token_data['low_24h']:,}"
        )

    st.metric(
        "Total Volume",
        f"${token_data['total_volume']:,}"
    )

    token_chart = pd.DataFrame({
        "Metric": [
            "Market Cap",
            "Volume"
        ],
        "Value": [
            token_data["market_cap"],
            token_data["total_volume"]
        ]
    })

    fig2 = px.bar(
        token_chart,
        x="Metric",
        y="Value",
        title=f"{token_data['name']} Analytics"
    )

    st.plotly_chart(
        fig2,
        width="stretch"
    )
st.caption("Built with FastAPI + Streamlit + Blockchain APIs")        
# ---------------- WHALE TRACKER ----------------

st.markdown("---")

st.header("🐋 Whale Tracker")

st.write("Tracking large Ethereum wallet activity")

whale_api = "http://127.0.0.1:8000/api/whales"

whale_response = requests.get(whale_api)

whale_data = whale_response.json()

whale_transactions = whale_data.get("result", [])

if whale_transactions:

    whale_table = []

    for tx in whale_transactions[:10]:

        whale_table.append({
            "Hash": tx["hash"][:12] + "...",
            "From": tx["from"][:10] + "...",
            "To": tx["to"][:10] + "...",
            "Value (ETH)": round(
                int(tx["value"]) / 10**18,
                4
            )
        })

    whale_df = pd.DataFrame(whale_table)

    st.dataframe(
        whale_df,
        width="stretch"
    )

    whale_chart = pd.DataFrame({
        "Transaction": range(1, len(whale_table)+1),
        "ETH Value": [
            row["Value (ETH)"]
            for row in whale_table
        ]
    })

    fig3 = px.line(
        whale_chart,
        x="Transaction",
        y="ETH Value",
        title="Whale Transaction Activity"
    )

    st.plotly_chart(
        fig3,
        width="stretch"
    )

else:
    st.warning("No whale activity found")
# ---------------- AI INSIGHTS ----------------

st.markdown("---")

st.header("🧠 AI Blockchain Insights")

ai_token = st.text_input(
    "Enter Token For AI Insight"
)

if ai_token:

    insight_api = (
        f"http://127.0.0.1:8000/api/insights/{ai_token}"
    )

    insight_response = requests.get(insight_api)

    insight_data = insight_response.json()

    st.success(
        f"Insight for {insight_data['token']}"
    )

    st.info(
        insight_data["insight"]
    ) 
# ---------------- RISK ASSESSMENT ----------------

st.markdown("---")

st.header("🛡️ Token Risk Assessment")

risk_token = st.text_input(
    "Enter Token For Risk Analysis",
    key="risk_token"
)

if risk_token:

    try:

        risk_api = (
            f"http://127.0.0.1:8000/api/risk/{risk_token}"
        )

        risk_response = requests.get(risk_api)

        risk_data = risk_response.json()

        st.success(
            f"Risk Analysis for {risk_data['token']}"
        )

        risk = risk_data["risk"]

        if risk == "Low Risk":
            st.success(f"Risk Level: {risk}")

        elif risk == "Medium Risk":
            st.warning(f"Risk Level: {risk}")

        else:
            st.error(f"Risk Level: {risk}")

    except Exception as e:

        st.error(
            f"Unable to perform risk analysis: {e}"
        )       
# ---------------- FOOTER ----------------

st.markdown("---")
st.caption("Built with FastAPI + Streamlit + Blockchain APIs")
