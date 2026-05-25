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

st.plotly_chart(fig, use_container_width=True)

# ---------------- MARKET TABLE ----------------

st.subheader("📊 Market Overview")

table_data = pd.DataFrame({
    "Coin": ["Bitcoin", "Ethereum"],
    "Price (USD)": [btc_price, eth_price]
})

st.dataframe(table_data, use_container_width=True)

# ---------------- FOOTER ----------------

st.markdown("---")

st.caption("Built with FastAPI + Streamlit + Blockchain APIs")