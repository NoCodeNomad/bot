import os
import requests

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TRADINGECONOMICS_KEY = os.getenv("TRADINGECONOMICS_KEY")

def fetch_finnhub_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("c")

def fetch_polygon_price(symbol):
    url = f"https://api.polygon.io/v1/last/stocks/{symbol}?apiKey={POLYGON_API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("last", {}).get("price")

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
    articles = resp.json().get("articles", [])
    return [(a["title"], a["url"]) for a in articles]

def fetch_macro_indicator(country="united states", indicator="gdp"):
    url = f"https://api.tradingeconomics.com/forecast/country/{country}/indicator/{indicator}?c={TRADINGECONOMICS_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def get_stock_price(symbol):
    for fetcher in [fetch_finnhub_price, fetch_polygon_price, fetch_twelvedata_price]:
        try:
            price = fetcher(symbol)
            if price:
                return price
        except:
            continue
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
    print(f"Macro indicator data sample: {macro[:1]}")
