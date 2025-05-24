
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Ticker Intel V2", layout="wide")
st.title("📊 Ticker Intel V2 — Smart Signal Dashboard")

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

def calculate_sma(series, period=20):
    return series.rolling(window=period).mean()

def render_gauge(label, value, min_val=0, max_val=100, color="blue"):
    try:
        val = float(value)
        if not np.isfinite(val):
            val = 0
    except:
        val = 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={'text': label},
        gauge={'axis': {'range': [min_val, max_val]}, 'bar': {'color': color}},
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=20, l=10, r=10))
    return fig

tickers = st.multiselect("Select Tickers", ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL"], default=["AAPL"])
interval = st.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"])
period_map = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "7d", "1d": "1mo"}

for ticker in tickers:
    st.markdown(f"## 🔍 {ticker.upper()} — {interval}")
    data = yf.download(ticker, period=period_map[interval], interval=interval)
    if data.empty:
        st.warning(f"No data for {ticker}")
        continue

    data['RSI'] = calculate_rsi(data['Close'])
    data['MACD'], data['Signal'] = calculate_macd(data['Close'])
    data['SMA20'] = calculate_sma(data['Close'])
    data['Pressure'] = np.where(data['Close'] > data['Open'], 1, -1)

    data_clean = data.dropna()
    if data_clean.empty:
        st.warning("Not enough data to compute indicators.")
        continue

    last = data_clean.iloc[-1]

    def safe_metric(val):
        try:
            return f"{float(val):.2f}"
        except:
            return "N/A"

    try:
        pressure_val = int(last["Pressure"])
    except:
        pressure_val = "N/A"

    # Interpret signal
    rsi_val = last["RSI"]
    macd_val = last["MACD"]
    signal_val = last["Signal"]

    rsi_flag = "🔴 Overbought" if rsi_val > 70 else ("🟢 Oversold" if rsi_val < 30 else "⚪ Neutral")
    macd_flag = "🟢 Bullish" if macd_val > signal_val else "🔴 Bearish"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📉 RSI", safe_metric(rsi_val), rsi_flag)
    col2.metric("📊 MACD", safe_metric(macd_val), macd_flag)
    col3.metric("🟢 Pressure", pressure_val)
    col4.metric("🔻 Signal", safe_metric(signal_val))

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02,
                        row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=("Price w/ SMA", "RSI", "MACD"))

    fig.add_trace(go.Candlestick(x=data_clean.index,
                                 open=data_clean['Open'],
                                 high=data_clean['High'],
                                 low=data_clean['Low'],
                                 close=data_clean['Close'],
                                 name='Candlestick'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data_clean.index, y=data_clean['SMA20'],
                             mode='lines', name='20 SMA', line=dict(color='royalblue')), row=1, col=1)

    fig.add_trace(go.Scatter(x=data_clean.index, y=data_clean['RSI'],
                             mode='lines', name='RSI', line=dict(color='green')), row=2, col=1)

    fig.add_trace(go.Scatter(x=data_clean.index, y=data_clean['MACD'],
                             mode='lines', name='MACD', line=dict(color='orange')), row=3, col=1)

    fig.update_layout(height=700, showlegend=False,
                      xaxis_rangeslider_visible=False,
                      title_text=f"{ticker.upper()} Price + RSI + MACD")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📟 Gauges")
    g1, g2, g3 = st.columns(3)
    with g1: st.plotly_chart(render_gauge("RSI", rsi_val, color="green"))
    with g2: st.plotly_chart(render_gauge("MACD", macd_val, min_val=-5, max_val=5, color="orange"))
    with g3: st.plotly_chart(render_gauge("Buy/Sell Pressure", last['Pressure'], min_val=-1, max_val=1, color="blue"))

    with st.expander("📄 Indicator Table"):
        st.dataframe(data[['RSI', 'MACD', 'Signal', 'SMA20', 'Pressure']].dropna().tail(10))

    st.download_button("📥 Download CSV", data.to_csv().encode('utf-8'), file_name=f"{ticker}_{interval}.csv", mime="text/csv")
