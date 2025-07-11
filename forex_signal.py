import pandas as pd
import yfinance as yf
import ta
import requests
import time
from datetime import datetime
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8153857317:AAFi1ZkEf-5wW8A6mZmbjNMtnnQjV8bAjMc"
TELEGRAM_USER_ID = "1833631907"
SYMBOL = "GC=F"  # Gold Futures symbol (used by Yahoo Finance)
INTERVAL = "5m"
ATR_MULTIPLIERS = [1, 1.5, 2]  # TP1, TP2, TP3 levels

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        return response
    except Exception as e:
        print("Telegram Error:", e)

def get_signal():
    df = yf.download(SYMBOL, period="5d", interval=INTERVAL)
    if df.empty:
        raise ValueError("No data returned from Yahoo Finance.")

    # === Indicators ===
    ema5 = ta.trend.EMAIndicator(close=df['Close'], window=5).ema_indicator()
    ema10 = ta.trend.EMAIndicator(close=df['Close'], window=10).ema_indicator()
    rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

    atr_obj = ta.volatility.AverageTrueRange(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        window=14
    )
    atr = atr_obj.average_true_range()

    # 🔧 REAL FIX: force ATR to 1D Series
    try:
        atr = pd.Series(atr.squeeze(), index=df.index)
    except:
        atr = pd.Series(atr.values.flatten(), index=df.index)

    # Optional debug
    print("ATR SHAPE:", atr.shape)
    print("ATR TYPE:", type(atr))

    # Assign indicators to dataframe
    df['ema5'] = ema5
    df['ema10'] = ema10
    df['rsi'] = rsi
    df['atr'] = atr

    df.dropna(inplace=True)
    if len(df) < 2:
        raise ValueError("Not enough data after indicators.")

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    signal = None
    direction = None

    if previous['ema5'] < previous['ema10'] and latest['ema5'] > latest['ema10'] and latest['rsi'] > 55:
        signal = "📈 BUY SIGNAL"
        direction = "buy"
    elif previous['ema5'] > previous['ema10'] and latest['ema5'] < latest['ema10'] and latest['rsi'] < 45:
        signal = "📉 SELL SIGNAL"
        direction = "sell"

    return signal, {
        'price': float(latest['Close']),
        'rsi': float(latest['rsi']),
        'atr': float(latest['atr'])
    }, direction

def main():
    sent_signals = set()

    while True:
        try:
            signal, data, direction = get_signal()

            if signal and signal not in sent_signals:
                price = data['price']
                atr = data['atr']
                rsi = data['rsi']
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if direction == "buy":
                    tp1 = price + ATR_MULTIPLIERS[0] * atr
                    tp2 = price + ATR_MULTIPLIERS[1] * atr
                    tp3 = price + ATR_MULTIPLIERS[2] * atr
                    sl = price - atr
                else:
                    tp1 = price - ATR_MULTIPLIERS[0] * atr
                    tp2 = price - ATR_MULTIPLIERS[1] * atr
                    tp3 = price - ATR_MULTIPLIERS[2] * atr
                    sl = price + atr

                message = f"""
⏰ {timestamp}
🔔 {signal}
Pair: GOLD (GC=F)
Price: {price:.2f}
RSI: {rsi:.2f}
ATR: {atr:.2f}

🎯 Take Profits:
TP1: {tp1:.2f}
TP2: {tp2:.2f}
TP3: {tp3:.2f}
🛑 Stop Loss: {sl:.2f}
                """.strip()

                send_telegram_message(message)
                print("Sent:", message)
                sent_signals.add(signal)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No new signal.")

        except Exception as e:
            print("Error:", e)

        time.sleep(300)  # Every 5 minutes

if __name__ == "__main__":
    main()
