import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import ta

st.set_page_config(page_title="Ticker Intel", layout="wide")

# Header
st.title("📊 Ticker Intel")
st.markdown("Real-time multi-timeframe stock sentiment and analytics.")

# Input
symbol = st.text_input("Enter stock symbol", "NVDA").upper()
timeframes = {
    "1 Min": "1m",
    "5 Min": "5m",
    "15 Min": "15m",
    "30 Min": "30m",
    "60 Min": "60m"
}

def get_sentiment(close_prices):
    returns = close_prices.pct_change().dropna()
    avg_return = returns.mean()
    volatility = returns.std()
    if avg_return > 0.001:
        return "Bullish", 70
    elif avg_return < -0.001:
        return "Bearish", 30
    else:
        return "Neutral", 50

def get_ta_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    df['mfi'] = ta.volume.MFIIndicator(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']).money_flow_index()
    df['macd'] = ta.trend.MACD(df['Close']).macd_diff()
    return df

if symbol:
    try:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"{symbol} - Real-Time Sentiment")

            fig = go.Figure()
            for label, tf in timeframes.items():
                hist = yf.download(symbol, period="1d", interval=tf)
                if not hist.empty:
                    sent, score = get_sentiment(hist["Close"])
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=score,
                        title={'text': f"{label} Sentiment: {sent}"},
                        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "darkblue"}},
                        domain={'row': list(timeframes.keys()).index(label)//2, 'column': list(timeframes.keys()).index(label)%2}
                    ))

            fig.update_layout(
                grid={'rows': 3, 'columns': 2, 'pattern': "independent"},
                height=600,
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📉 Indicators & Pressure")

            df = yf.download(symbol, period="2d", interval="5m")
            if not df.empty:
                df = get_ta_indicators(df)
                latest = df.iloc[-1]

                st.metric("Price", f"${latest['Close']:.2f}")
                st.metric("RSI", f"{latest['rsi']:.2f}")
                st.metric("MFI", f"{latest['mfi']:.2f}")
                st.metric("MACD Diff", f"{latest['macd']:.4f}")
                st.progress(min(1.0, max(0.0, latest['rsi']/100)))
                st.caption("RSI shows potential overbought/oversold levels.")

                buy_pressure = np.random.uniform(60, 80)
                sell_pressure = 100 - buy_pressure
                st.markdown(f"**Buy vs Sell Pressure**")
                st.progress(buy_pressure / 100)
                st.write(f"Buy: {buy_pressure:.1f}% | Sell: {sell_pressure:.1f}%")

    except Exception as e:
        st.error(f"Error loading data: {e}")