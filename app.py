
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ticker Intel", layout="wide")

st.title("💹 Ticker Intel — Market Dashboard")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calculate_mfi(high, low, close, volume, period=14):
    tp = (high + low + close) / 3
    mf = tp * volume
    pos_mf = mf.where(tp.diff() > 0, 0).rolling(window=period).sum()
    neg_mf = mf.where(tp.diff() < 0, 0).rolling(window=period).sum()
    mfi = 100 - (100 / (1 + pos_mf / neg_mf))
    return mfi

ticker = st.text_input("Enter stock symbol", "AAPL")
intervals = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "7d"}

if ticker:
    tabs = st.tabs([f"⏱ {i}" for i in intervals])
    for idx, (interval, period) in enumerate(intervals.items()):
        with tabs[idx]:
            st.subheader(f"{ticker.upper()} - {interval} Analysis")
            data = yf.download(ticker, period=period, interval=interval)
            if not data.empty:
                data['RSI'] = calculate_rsi(data['Close'])
                data['MFI'] = calculate_mfi(data['High'], data['Low'], data['Close'], data['Volume'])
                data['MACD'], data['Signal'] = calculate_macd(data['Close'])
                data['Pressure'] = np.where(data['Close'] > data['Open'], 1, -1)

                data_clean = data.dropna()
                if data_clean.empty:
                    st.warning("Not enough data to compute indicators yet.")
                    continue

                last = data_clean.iloc[-1]

                def safe_metric(value):
                    try:
                        return f"{float(value):.2f}"
                    except:
                        return "N/A"

                try:
                    pressure_val = int(last["Pressure"])
                except:
                    pressure_val = "N/A"

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📉 RSI", safe_metric(last['RSI']))
                col2.metric("💧 MFI", safe_metric(last['MFI']))
                col3.metric("📊 MACD", safe_metric(last['MACD']))
                col4.metric("🟢 Pressure", pressure_val)

                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'], name='Candles'
                ))
                fig.update_layout(title=f"{ticker.upper()} Candlestick Chart", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("📈 Indicator Tables"):
                    st.dataframe(data[['RSI', 'MFI', 'MACD', 'Signal', 'Pressure']].dropna().tail(10))

                st.download_button(
                    label="📥 Download Data",
                    data=data.to_csv().encode('utf-8'),
                    file_name=f"{ticker}_{interval}.csv",
                    mime='text/csv'
                )
            else:
                st.warning("No data available.")
