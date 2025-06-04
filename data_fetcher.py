import os
import requests

# Load API keys from environment variables
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TRADINGECONOMICS_KEY = os.getenv("TRADINGECONOMICS_KEY")

def fetch_finnhub_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    # Returns current price
    return data.get("c")

def fetch_polygon_price(symbol):
    url = f"https://api.polygon.io/v1/last/stocks/{symbol}?apiKey={POLYGON_API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("last", {}).get("price")

def fetch_twelvedata_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVEDATA_API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return float(data.get("price")) if "price" in data else None

def fetch_news(query, language="en", page_size=5):
    url = f"https://newsapi.org/v2/everything?q={query}&language={language}&pageSize={page_size}&apiKey={NEWSAPI_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    articles = data.get("articles", [])
    return [(a["title"], a["url"]) for a in articles]

def fetch_macro_indicator(country="united states", indicator="gdp"):
    url = f"https://api.tradingeconomics.com/forecast/country/{country}/indicator/{indicator}?c={TRADINGECONOMICS_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data  # returns raw json with indicator info

# Example combined usage function
def get_stock_price(symbol):
    # Try Finnhub first
    try:
        price = fetch_finnhub_price(symbol)
        if price:
            return price
    except Exception:
        pass
    # Fallback Polygon
    try:
        price = fetch_polygon_price(symbol)
        if price:
            return price
    except Exception:
        pass
    # Fallback Twelve Data
    try:
        price = fetch_twelvedata_price(symbol)
        if price:
            return price
    except Exception:
        pass
    return None

if __name__ == "__main__":
    symbol = "AAPL"
    price = get_stock_price(symbol)
    print(f"Price of {symbol}: {price}")

    news = fetch_news("Apple")
    print("News Headlines:")
    for title, url in news:
        print(f"- {title} ({url})")

    macro = fetch_macro_indicator()
    print(f"Macro indicator data: {macro}")
