import yfinance as yf
import pandas as pd
from ta.trend import SMAIndicator
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

def get_features(df):
    df = df.copy()
    close_series = df['Close']
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.squeeze()
    df['SMA_10'] = SMAIndicator(close_series, window=10).sma_indicator()
    df['SMA_50'] = SMAIndicator(close_series, window=50).sma_indicator()
    df['Return'] = close_series.pct_change()
    df['Target'] = (df['Return'].shift(-1) > 0).astype(int)
    df.dropna(inplace=True)
    return df

def train_model(ticker="AAPL"):
    print(f"Downloading data for {ticker}...")
    df = yf.download(ticker, period="2y", interval="1d", progress=False)

    if df.empty:
        print(f"No data found for {ticker}, skipping.")
        return

    df = get_features(df)
    X = df[['SMA_10', 'SMA_50', 'Return']]
    y = df['Target']

    print(f"Features shape: {X.shape}, Target shape: {y.shape}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Training model for {ticker}...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {acc * 100:.2f}%")

    os.makedirs("models", exist_ok=True)
    model_filename = "model.pkl"
    joblib.dump(model, model_filename)
    print(f"Model saved to {model_filename}")

if __name__ == "__main__":
    train_model()
