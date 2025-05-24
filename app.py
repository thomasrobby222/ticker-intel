
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Ticker Intel", layout="wide")

st.title("📈 Ticker Intel")
st.markdown("Get multi-timeframe sentiment and stock intelligence in real-time.")

# Symbol input
symbol = st.text_input("Enter stock symbol (e.g., NVDA)", value="NVDA").upper()

if symbol:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")

    if data.empty:
        st.error("No data found. Try another symbol.")
    else:
        st.subheader(f"Real-Time Data for {symbol}")
        st.line_chart(data["Close"])

        latest = data.iloc[-1]
        change = (latest["Close"] - data["Close"].iloc[0]) / data["Close"].iloc[0] * 100

        st.metric(label="Latest Price", value=f"${latest['Close']:.2f}", delta=f"{change:.2f}%")

        # Sentiment estimate (simple based on price movement)
        sentiment_score = max(0, min(100, 50 + change))
        st.progress(sentiment_score / 100)
        st.markdown(f"**Market Sentiment Score**: {sentiment_score:.0f}%")

        # Placeholder for more complex features (psychology, entry readiness, dollar flow)
        st.markdown("🔍 *Advanced sentiment indicators coming soon...*")
