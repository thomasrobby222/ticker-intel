
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Ticker Intel V2", layout="wide")
st.title("📊 Ticker Intel V2 — Market Signal Dashboard")

# Helper functions
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

def render_gauge(label, value, min_val=0, max_val=100, color="blue"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value if np.isfinite(value) else 0,
        title={'text': label},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': color},
        }
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=20, l=10, r=10))
    return fig

# UI - Multi-ticker selection
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
    data['Pressure'] = np.where(data['Close'] > data['Open'], 1, -1)

    last = data.dropna().iloc[-1]

    # Metrics grid
    col1, col2, col3, col4 = st.columns(4)
    def safe_metric(val):
        try:
            return f"{float(val):.2f}"
        except:
            return "N/A"
    def safe_int(val):
        try:
            return int(val)
        except:
            return "N/A"
    col1.metric("📉 RSI", safe_metric(last['RSI']))
    col2.metric("📊 MACD", safe_metric(last['MACD']))
    col3.metric("🟢 Pressure", safe_int(last['Pressure']))
    col4.metric("🔻 Signal", safe_metric(last['Signal']))

    # Chart with overlays
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'],
        low=data['Low'], close=data['Close'], name='Candles'
    ))
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI", yaxis="y2", line=dict(color="green", dash="dot")))
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD", yaxis="y3", line=dict(color="orange")))

    fig.update_layout(
        title=f"{ticker} Price, RSI & MACD",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        yaxis2=dict(overlaying="y", side="right", position=0.95, title="RSI", range=[0, 100]),
        yaxis3=dict(overlaying="y", side="right", position=1.05, title="MACD"),
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gauges
    st.markdown("### 📟 Gauges")
    g1, g2, g3 = st.columns(3)
    with g1: st.plotly_chart(render_gauge("RSI", last['RSI'], color="green"))
    with g2: st.plotly_chart(render_gauge("MACD", last['MACD'], min_val=-5, max_val=5, color="orange"))
    with g3: st.plotly_chart(render_gauge("Buy/Sell Pressure", last['Pressure'], min_val=-1, max_val=1, color="blue"))

    with st.expander("📄 Indicator Table"):
        st.dataframe(data[['RSI', 'MACD', 'Signal', 'Pressure']].dropna().tail(10))

    st.download_button("📥 Download CSV", data.to_csv().encode('utf-8'), file_name=f"{ticker}_{interval}.csv", mime="text/csv")
