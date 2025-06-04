import os
import requests
import json
from datetime import datetime, timedelta
import numpy as np

# --- CONFIG ---

STARTING_BALANCE = 10000.0
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX",
    "AMD", "INTC", "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO",
    "ARKK", "XLK", "XLF", "XLY", "XLE", "XLI", "XLB", "XLV",
    "XLC", "XLU", "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD",
    "DOGE-USD", "XRP-USD", "LTC-USD", "AVAX-USD", "DOT-USD",
    "BNB-USD", "BRK-B", "JNJ", "V", "MA", "JPM", "UNH", "HD",
    "PG", "DIS", "BAC", "KO", "PFE", "PEP", "T", "CSCO",
    "ORCL", "IBM", "CRM", "BABA", "TM", "NSRGY", "VWAGY",
    "TSM", "NIO"
]

ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TRADINGECONOMICS_KEY = os.getenv("TRADINGECONOMICS_KEY")

# Files to save bot state
BALANCE_FILE = "balance.txt"
PORTFOLIO_FILE = "portfolio.json"

# --- HELPER FUNCTIONS ---

def load_balance():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            return float(f.read())
    return STARTING_BALANCE

def save_balance(balance):
    with open(BALANCE_FILE, "w") as f:
        f.write(str(balance))

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)

# Fetch Alpha Vantage 15 min intraday data
def fetch_alpha_vantage_data(ticker):
    url = (
        "https://www.alphavantage.co/query"
        "?function=TIME_SERIES_INTRADAY"
        f"&symbol={ticker}"
        "&interval=15min"
        "&outputsize=compact"
        f"&apikey={ALPHAVANTAGE_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    ts_key = "Time Series (15min)"
    if ts_key not in data:
        print(f"Alpha Vantage error or rate limit for {ticker}: {data.get('Note', data)}")
        return None
    return data[ts_key]

# Fetch recent news for a ticker (last 3 days)
def fetch_news(ticker):
    today = datetime.utcnow().date()
    from_date = today - timedelta(days=3)
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={ticker}"
        f"&from={from_date}"
        f"&sortBy=publishedAt"
        f"&language=en"
        f"&apiKey={NEWSAPI_KEY}"
        "&pageSize=5"
    )
    response = requests.get(url)
    data = response.json()
    if data.get("status") != "ok":
        print(f"NewsAPI error for {ticker}: {data}")
        return []
    return data.get("articles", [])

# Simple sentiment scoring (just counts positive vs negative words for demo)
POSITIVE_WORDS = ["gain", "rise", "bull", "up", "beat", "growth", "profit"]
NEGATIVE_WORDS = ["loss", "fall", "bear", "down", "miss", "decline", "risk"]

def score_sentiment(articles):
    score = 0
    for article in articles:
        text = (article.get("title","") + " " + article.get("description","")).lower()
        for w in POSITIVE_WORDS:
            score += text.count(w)
        for w in NEGATIVE_WORDS:
            score -= text.count(w)
    return score

# Fetch upcoming economic events
def fetch_economic_events():
    url = f"https://api.tradingeconomics.com/calendar?c={TRADINGECONOMICS_KEY}&f=json"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Trading Economics error: {response.status_code}")
        return []
    data = response.json()
    # Filter events in next 24h with high impact (optional)
    now = datetime.utcnow()
    upcoming = []
    for event in data:
        event_time = datetime.strptime(event["Date"], "%Y-%m-%dT%H:%M:%S")
        if 0 <= (event_time - now).total_seconds() <= 86400:
            if event.get("Impact", "").lower() == "high":
                upcoming.append(event)
    return upcoming

# Decide action based on price & sentiment (very simple logic here)
def decide_action(price_now, price_15min_ago, sentiment_score, holding_quantity):
    price_change_pct = (price_now - price_15min_ago) / price_15min_ago if price_15min_ago else 0

    # If we hold and price dropped significantly or sentiment negative -> Sell
    if holding_quantity > 0 and (price_change_pct < -0.002 or sentiment_score < 0):
        return "SELL"

    # If we do not hold and price increased moderately and sentiment positive -> Buy
    if holding_quantity == 0 and price_change_pct > 0.001 and sentiment_score > 0:
        return "BUY"

    # If we hold and price stable or sentiment neutral -> Hold
    if holding_quantity > 0:
        return "HOLD"

    # Otherwise skip
    return "SKIP"

# --- MAIN BOT LOOP ---

def main():
    balance = load_balance()
    portfolio = load_portfolio()

    print(f"Starting balance: ${balance:.2f}")
    print(f"Starting portfolio: {portfolio}")

    economic_events = fetch_economic_events()
    print(f"Upcoming economic events in next 24h (high impact): {len(economic_events)}")

    for ticker in TICKERS:
        print(f"\nProcessing {ticker}...")

        # Get intraday data
        data = fetch_alpha_vantage_data(ticker)
        if not data:
            print(f"Skipping {ticker} due to missing data.")
            continue

        times = sorted(data.keys())
        if len(times) < 2:
            print(f"Not enough data points for {ticker}, skipping.")
            continue

        latest_time = times[-1]
        prev_time = times[-2]

        price_now = float(data[latest_time]["4. close"])
        price_15min_ago = float(data[prev_time]["4. close"])

        # Get current holdings
        holding = portfolio.get(ticker, {"quantity": 0, "avg_price": 0})
        quantity = holding["quantity"]
        avg_price = holding["avg_price"]

        # Fetch recent news and calculate sentiment
        articles = fetch_news(ticker)
        sentiment = score_sentiment(articles)

        # Decide action
        action = decide_action(price_now, price_15min_ago, sentiment, quantity)
        print(f"Action for {ticker}: {action} | Price now: {price_now} | Prev: {price_15min_ago} | Sentiment score: {sentiment}")

        # Execute action
        if action == "BUY" and balance > 0:
            # Buy up to 10% of balance
            amount_to_spend = balance * 0.1
            shares_to_buy = amount_to_spend / price_now
            new_quantity = quantity + shares_to_buy
            new_avg_price = ((avg_price * quantity) + (price_now * shares_to_buy)) / new_quantity
            portfolio[ticker] = {"quantity": new_quantity, "avg_price": new_avg_price}
            balance -= amount_to_spend
            print(f"Bought {shares_to_buy:.4f} shares of {ticker} at ${price_now:.2f}")

        elif action == "SELL" and quantity > 0:
            proceeds = quantity * price_now
            balance += proceeds
            portfolio[ticker] = {"quantity": 0, "avg_price": 0}
            print(f"Sold {quantity:.4f} shares of {ticker} at ${price_now:.2f}")

        elif action == "HOLD":
            print(f"Holding {quantity:.4f} shares of {ticker}.")

        elif action == "SKIP":
            print("Skipping this ticker.")

    # Save updated state
    save_balance(balance)
    save_portfolio(portfolio)

    print(f"\nEnding balance: ${balance:.2f}")
    print(f"Ending portfolio: {portfolio}")

if __name__ == "__main__":
    main()
