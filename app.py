
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go

st.set_page_config(page_title="Ticker Intel", layout="wide")
st.title("📊 Ticker Intel - Sentiment Dashboard")

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

ticker = st.text_input("Enter stock symbol (e.g., AAPL)", "AAPL")

if ticker:
    data = yf.download(ticker, period="5d", interval="5m")

    if not data.empty:
        data['RSI'] = calculate_rsi(data['Close'])
        data['MFI'] = calculate_mfi(data['High'], data['Low'], data['Close'], data['Volume'])
        data['MACD'], data['Signal'] = calculate_macd(data['Close'])

        buy_pressure = np.where(data['Close'] > data['Open'], 1, -1)
        data['Pressure'] = buy_pressure

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Candlestick'
        ))
        fig.update_layout(title=f"{ticker} Price & Indicators", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Indicators Summary")
        st.write(data[['RSI', 'MFI', 'MACD', 'Signal', 'Pressure']].tail())

    else:
        st.error("No data found. Please check the symbol and try again.")
else:
    st.info("Please enter a stock symbol.")
