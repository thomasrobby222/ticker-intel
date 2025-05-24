
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Ticker Intel - Decalp X", layout="wide")

st.markdown(
    """
    <style>
        body {
            background-color: #0e1117;
            color: #c9d1d9;
        }
        .stApp {
            background-color: #0e1117;
        }
        .css-1d391kg {
            background-color: #161b22;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Ticker Intel - Decalp X Dashboard")

ticker = st.text_input("Enter stock symbol", "AAPL")
intervals = ["1m", "5m", "15m", "1h"]
period_mapping = {
    "1m": "1d",
    "5m": "5d",
    "15m": "5d",
    "1h": "7d"
}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calculate_mfi(high, low, close, volume, period=14):
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    direction = typical_price.diff()
    positive_flow = money_flow.where(direction > 0, 0)
    negative_flow = money_flow.where(direction < 0, 0)
    pos_mf = positive_flow.rolling(window=period).sum()
    neg_mf = negative_flow.rolling(window=period).sum()
    mfi = 100 - (100 / (1 + pos_mf / neg_mf))
    return mfi

def get_indicator_summary(df):
    latest = df.iloc[-1]
    return {
        "RSI": round(latest["RSI"], 2),
        "MFI": round(latest["MFI"], 2),
        "MACD": round(latest["MACD"], 2),
        "Signal": round(latest["Signal"], 2),
        "Buy/Sell Pressure": int(latest["Pressure"])
    }

if ticker:
    col1, col2 = st.columns([1, 2])
    all_data = {}
    for interval in intervals:
        with st.spinner(f"Fetching {interval} data..."):
            data = yf.download(ticker, period=period_mapping[interval], interval=interval)
            if not data.empty:
                data['RSI'] = calculate_rsi(data['Close'])
                data['MFI'] = calculate_mfi(data['High'], data['Low'], data['Close'], data['Volume'])
                data['MACD'], data['Signal'] = calculate_macd(data['Close'])
                data['Pressure'] = np.where(data['Close'] > data['Open'], 1, -1)
                all_data[interval] = data

    if all_data:
        st.subheader("📈 Indicator Summary by Timeframe")
        for tf, df in all_data.items():
            indicators = get_indicator_summary(df)
            st.markdown(f"**⏱ {tf} timeframe**")
            st.write(indicators)

        with col1:
            st.subheader("🧭 Gauges (1h timeframe)")
            latest = all_data["1h"].iloc[-1]
            st.metric("RSI", round(latest["RSI"], 2))
            st.metric("MFI", round(latest["MFI"], 2))
            st.metric("MACD", round(latest["MACD"], 2))
            st.metric("Buy/Sell Pressure", int(latest["Pressure"]))

        with col2:
            st.subheader("📊 Price Chart")
            df = all_data["1h"]
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Candlestick'
            ))
            fig.update_layout(
                template="plotly_dark",
                title=f"{ticker} 1h Chart",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No data available. Please try a different ticker.")
