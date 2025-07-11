import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime

# App config
st.set_page_config(page_title="Forex Signal Dashboard", layout="wide")
st.title("📈 Real-Time Forex Signal Dashboard")

SYMBOL = "XAUUSD=X"  # Gold
INTERVAL = "1h"

@st.cache_data(ttl=300)  # Refresh data every 5 minutes
def load_data():
    df = yf.download(SYMBOL, period="7d", interval=INTERVAL)
    df['ema9'] = ta.trend.ema_indicator(df['Close'], window=9).ema_indicator()
    df['ema21'] = ta.trend.ema_indicator(df['Close'], window=21).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    return df

def get_signal(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    signal = "NO SIGNAL ❌"

    if prev['ema9'] < prev['ema21'] and latest['ema9'] > latest['ema21'] and latest['rsi'] > 50:
        signal = "📈 BUY SIGNAL"
    elif prev['ema9'] > prev['ema21'] and latest['ema9'] < latest['ema21'] and latest['rsi'] < 50:
        signal = "📉 SELL SIGNAL"

    return signal, latest

# Load data and calculate
data = load_data()
signal, latest = get_signal(data)

# Display info
st.subheader(f"Symbol: {SYMBOL}")
st.metric(label="Latest Price", value=f"${latest['Close']:.2f}")
st.metric(label="RSI", value=f"{latest['rsi']:.2f}")
st.markdown(f"### Signal: **{signal}**")

# Plot
st.line_chart(data[['Close', 'ema9', 'ema21']].dropna())

# Footer
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
