
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from ta.momentum import RSIIndicator, MoneyFlowIndex
from ta.trend import MACD

st.set_page_config(page_title="Ticker Intel", layout="wide")

st.title("📊 Ticker Intel - Sentiment Dashboard")

ticker = st.text_input("Enter stock symbol (e.g., AAPL)", "AAPL")

if ticker:
    data = yf.download(ticker, period="5d", interval="5m")

    if not data.empty:
        # Indicators
        data['RSI'] = RSIIndicator(data['Close']).rsi()
        data['MFI'] = MoneyFlowIndex(high=data['High'], low=data['Low'], close=data['Close'], volume=data['Volume']).money_flow_index()
        macd = MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()

        # Buy/Sell Pressure Estimate
        buy_pressure = np.where(data['Close'] > data['Open'], 1, -1)
        data['Pressure'] = buy_pressure

        # Chart
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
