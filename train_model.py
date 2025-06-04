import yfinance as yf
import pandas as pd
from ta.trend import SMAIndicator
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

def get_features(df):
    df = df.copy()
    df['SMA_10'] = SMAIndicator(df['Close'], window=10).sma_indicator()
    df['SMA_50'] = SMAIndicator(df['Close'], window=50).sma_indicator()
    df['Return'] = df['Close'].pct_change()
    df['Target'] = (df['Return'].shift(-1) > 0).astype(int)
    df.dropna(inplace=True)
    return df

def train_model(ticker):
    print(f"Training model for {ticker}...")
    df = yf.download(ticker, period="2y", interval="1d", progress=False)
    if df.empty:
        print(f"No data for {ticker}, skipping.")
        return

    df = get_features(df)
    X = df[['SMA_10', 'SMA_50', 'Return']]
    y = df['Target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"{ticker} model accuracy: {acc:.2%}")

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, f"models/model_{ticker.replace('-', '_')}.pkl")

if __name__ == "__main__":
    tickers = pd.read_csv("symbols.csv")["symbol"].tolist()
    for ticker in tickers:
        train_model(ticker)
