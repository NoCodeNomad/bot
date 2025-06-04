import yfinance as yf
import json
import os
import joblib
import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands

# Tickers you want to trade on
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX"]

# Load or initialize balance
if os.path.exists("balance.txt"):
    with open("balance.txt", "r") as f:
        balance = float(f.read())
else:
    balance = 10000.0

# Load or initialize portfolio (store quantity and avg price per ticker)
if os.path.exists("portfolio.json"):
    with open("portfolio.json", "r") as f:
        portfolio = json.load(f)
else:
    portfolio = {}

print(f"Starting balance: ${balance:.2f}")
print(f"Starting portfolio: {portfolio}")

# Load trained ML model
if not os.path.exists("model.pkl"):
    print("Model not found! Run train_model.py first.")
    exit(1)
model = joblib.load("model.pkl")

def get_features(df):
    df['SMA_10'] = SMAIndicator(df['Close'], window=10).sma_indicator()
    df['SMA_30'] = SMAIndicator(df['Close'], window=30).sma_indicator()
    df['RSI_14'] = RSIIndicator(df['Close'], window=14).rsi()
    macd = MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    bollinger = BollingerBands(df['Close'])
    df['bb_high'] = bollinger.bollinger_hband()
    df['bb_low'] = bollinger.bollinger_lband()
    df['Volume'] = df['Volume']
    df = df.dropna()
    return df

def score_sentiment(articles):
    total_score = 0
    for article in articles:
        title = article.get("title") or ""
        description = article.get("description") or ""
        text = (title + " " + description).lower()

        # Example sentiment scoring logic:
        if "good" in text:
            total_score += 1
        elif "bad" in text:
            total_score -= 1

    return total_score

def predict_signal(df):
    features = df[['SMA_10', 'SMA_30', 'RSI_14', 'MACD', 'MACD_signal', 'bb_high', 'bb_low', 'Volume']]
    latest = features.iloc[-1].values.reshape(1, -1)
    pred = model.predict(latest)[0]
    return pred  # 1 = Buy, -1 = Sell, 0 = Hold

def fetch_news(ticker):
    # Dummy placeholder: Replace with actual API call
    # Must return list of dicts with keys "title" and "description"
    return []

for ticker in tickers:
    print(f"\nProcessing {ticker}...")
    try:
        df = yf.download(ticker, period="60d", progress=False)
        if df.empty:
            print(f"No data for {ticker}")
            continue
        df = get_features(df)
        signal = predict_signal(df)
        price = df['Close'].iloc[-1]

        # Sentiment analysis from news (replace with real news fetch)
        articles = fetch_news(ticker)
        sentiment = score_sentiment(articles)

        # Current holding
        holding = portfolio.get(ticker, {"quantity": 0, "avg_price": 0})
        quantity = holding.get("quantity", 0)
        avg_price = holding.get("avg_price", 0)

        print(f"Action for {ticker}: {['SELL','HOLD','BUY'][signal+1]} | Price now: {price:.2f} | Sentiment score: {sentiment}")

        if signal == 1:
            # Buy 10% of balance if enough funds
            amount_to_spend = balance * 0.1
            shares_to_buy = amount_to_spend / price
            if balance >= amount_to_spend:
                new_quantity = quantity + shares_to_buy
                new_avg_price = ((avg_price * quantity) + (price * shares_to_buy)) / new_quantity if new_quantity > 0 else 0
                portfolio[ticker] = {"quantity": new_quantity, "avg_price": new_avg_price}
                balance -= amount_to_spend
                print(f"Bought {shares_to_buy:.4f} shares of {ticker} at ${price:.2f}")
            else:
                print(f"Not enough balance to buy {ticker}")
        elif signal == -1 and quantity > 0:
            # Sell all holdings
            proceeds = quantity * price
            balance += proceeds
            portfolio[ticker] = {"quantity": 0, "avg_price": 0}
            print(f"Sold {quantity:.4f} shares of {ticker} at ${price:.2f}")
        else:
            print(f"Holding {quantity:.4f} shares of {ticker}, no action.")

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

print("\n--- Summary ---")
print(f"Remaining balance: ${balance:.2f}")
print("Portfolio holdings:")
for t, info in portfolio.items():
    print(f"{t}: {info['quantity']:.4f} shares at avg price ${info['avg_price']:.2f}")

# Save balance and portfolio
with open("balance.txt", "w") as f:
    f.write(str(balance))

with open("portfolio.json", "w") as f:
    json.dump(portfolio, f, indent=2)
