import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------- CONFIG ----------------

BASE_URL = "https://chainscope-ai-ljoa.onrender.com"
REQUEST_TIMEOUT = 15

st.set_page_config(
    page_title="ChainScope AI",
    page_icon="🚀",
    layout="wide"
)


# ---------------- HELPER ----------------

def api_get(path: str):
    """
    Call the backend and return (ok, data, error_message).
    Handles network failures and non-200 responses (which now carry
    a {"detail": "..."} body from FastAPI's HTTPException).
    """
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        return False, None, f"Could not reach backend: {e}"

    try:
        payload = response.json()
    except ValueError:
        return False, None, "Backend returned an invalid response."

    if response.status_code != 200:
        detail = payload.get("detail", "Request failed.") if isinstance(payload, dict) else "Request failed."
        return False, payload, detail

    return True, payload, None


@st.cache_data(ttl=30, show_spinner=False)
def cached_api_get(path: str):
    """
    Cached wrapper for token-lookup endpoints (analytics/insights/risk).
    Streamlit reruns the whole script on every widget interaction, so
    without this, typing in one box re-fetches every other section too —
    tripling calls to CoinGecko's low-rate-limit free tier. Not used for
    the live price ticker, which should always be fresh.
    """
    return api_get(path)


# ---------------- SIDEBAR ----------------

st.sidebar.title("🚀 ChainScope AI")

st.sidebar.success("Backend Connected")

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

# ---------------- FETCH DATA (PRICES) ----------------

ok, data, error = api_get("/api/prices")

if not ok:
    st.error(error or "Unable to fetch market data.")
    st.stop()

# The backend now wraps results in a "success" flag, including on a
# 200 response, since Binance failures (rate limit/geo-block) are
# reported this way rather than as an HTTP error.
if not data.get("success", False):
    st.error(data.get("message", "Unable to fetch live market prices."))
    with st.expander("Provider response details"):
        st.json(data.get("provider_response", data))
    st.stop()

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

    ok, wallet_payload, error = cached_api_get(f"/api/wallet/{wallet_address}")

    if not ok:
        # Covers both the 400 "invalid address format" case and any
        # 500/502 from a misconfigured or unreachable Etherscan call.
        st.error(error or "Unable to fetch wallet data.")
        st.stop()

    # New shape: {"success": True, "wallet": ..., "transactions": {<etherscan raw>}}
    etherscan_data = wallet_payload.get("transactions", {})

    if etherscan_data.get("status") == "0" and etherscan_data.get("message") != "No transactions found":
        st.warning("Invalid wallet address or no transactions found.")
        st.stop()

    transactions = etherscan_data.get("result", [])

    if transactions:

        st.success("Wallet data fetched successfully")

        tx_table = []

        for tx in transactions[:10]:
            try:
                tx_table.append({
                    "Hash": tx["hash"][:12] + "...",
                    "From": tx["from"][:10] + "...",
                    "To": tx["to"][:10] + "...",
                    "Value (ETH)": round(
                        int(tx["value"]) / 10**18,
                        5
                    )
                })
            except (KeyError, ValueError, TypeError):
                continue

        tx_df = pd.DataFrame(tx_table)

        st.dataframe(
            tx_df,
            width="stretch"
        )

    else:
        st.warning("No transactions found")

# ---------------- TOKEN ANALYTICS ---------------

st.markdown("---")

st.header("📈 Token Analytics")

token_input = st.text_input(
    "Enter Token ID (example: bitcoin, ethereum, solana)"
)

token_input = token_input.strip().lower()

if token_input:

    ok, token_data, error = cached_api_get(f"/api/token/{token_input}")

    if not ok:
        st.error(error or "Token not found. Try: bitcoin, ethereum, solana or dogecoin.")

    elif not token_data.get("success", False):
        st.error(token_data.get("message", "Token not found. Please check spelling."))

    else:

        st.success(
            f"Showing analytics for {token_data['name']}"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Current Price",
                f"${token_data.get('current_price', 0):,}"
            )

            st.metric(
                "24H High",
                f"${token_data.get('high_24h', 0):,}"
            )

        with col2:
            st.metric(
                "Market Cap",
                f"${token_data.get('market_cap', 0):,}"
            )

            st.metric(
                "24H Low",
                f"${token_data.get('low_24h', 0):,}"
            )

        st.metric(
            "Total Volume",
            f"${token_data.get('total_volume', 0):,}"
        )

        token_chart = pd.DataFrame({
            "Metric": ["Market Cap", "Volume"],
            "Value": [
                token_data.get("market_cap", 0),
                token_data.get("total_volume", 0)
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

# ---------------- WHALE TRACKER ----------------

st.markdown("---")

st.header("🐋 Whale Tracker")

st.write("Tracking large Ethereum wallet activity")

ok, whale_payload, error = cached_api_get("/api/whales")

if not ok:
    st.error(error or "Unable to fetch whale data.")

else:

    # New shape: {"success": True, "wallet": ..., "transactions": {<etherscan raw>}}
    whale_etherscan_data = whale_payload.get("transactions", {})
    whale_transactions = whale_etherscan_data.get("result", [])

    if whale_transactions:

        whale_table = []

        for tx in whale_transactions[:10]:
            try:
                whale_table.append({
                    "Hash": tx["hash"][:12] + "...",
                    "From": tx["from"][:10] + "...",
                    "To": tx["to"][:10] + "...",
                    "Value (ETH)": round(
                        int(tx["value"]) / 10**18,
                        4
                    )
                })
            except (KeyError, ValueError, TypeError):
                continue

        whale_df = pd.DataFrame(whale_table)

        st.dataframe(
            whale_df,
            width="stretch"
        )

        whale_chart = pd.DataFrame({
            "Transaction": range(1, len(whale_table) + 1),
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

ai_token = ai_token.strip().lower()

if ai_token:

    ok, insight_data, error = cached_api_get(f"/api/insights/{ai_token}")

    if not ok:
        # Backend now raises HTTPException directly for this endpoint
        # (404 unknown token, 429 rate limited, 502 missing data), so
        # the detail message from the backend is shown as-is.
        st.error(error or "Unable to generate insights. Check token name.")

    else:
        if "token" in insight_data and "insight" in insight_data:

            st.success(
                f"Insight for {insight_data['token']}"
            )

            st.info(
                insight_data["insight"]
            )

        else:

            st.error(
                insight_data.get(
                    "detail",
                    "Unable to generate AI insight."
                )
            )

# ---------------- RISK ASSESSMENT ----------------

st.markdown("---")

st.header("🛡️ Token Risk Assessment")

risk_token = st.text_input(
    "Enter Token For Risk Analysis",
    key="risk_token"
)
risk_token = risk_token.strip().lower()

if risk_token:

    ok, risk_data, error = cached_api_get(f"/api/risk/{risk_token}")

    if not ok:
        # Same as insights: this endpoint raises HTTPException on
        # not-found / rate-limit / missing-data cases.
        st.error(error or "Unable to perform risk analysis.")

    else:
        if "risk" not in risk_data:

            st.error(
                risk_data.get(
                    "detail",
                    "Unable to calculate risk."
                )
            )

        else:
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

# ---------------- FOOTER ----------------

st.markdown("---")
st.caption("Built with FastAPI + Streamlit + Blockchain APIs")
