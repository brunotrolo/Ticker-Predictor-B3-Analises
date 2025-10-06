
import pandas as pd

B3_CSV_PATH = "data/b3_tickers.csv"

def load_b3_tickers() -> pd.DataFrame:
    df = pd.read_csv(B3_CSV_PATH)
    df["ticker"] = df["ticker"].str.upper().str.strip()
    df["name"] = df["name"].astype(str)
    return df

def ensure_sa_suffix(ticker: str) -> str:
    if not isinstance(ticker, str) or not ticker.strip():
        return ""
    t = ticker.strip().upper()
    if not t.endswith(".SA"):
        t = f"{t}.SA"
    return t

def is_known_b3_ticker(ticker: str) -> bool:
    df = load_b3_tickers()
    t = ensure_sa_suffix(ticker)
    return t in set(df["ticker"].tolist())

def search_b3(query: str, limit: int = 20) -> pd.DataFrame:
    df = load_b3_tickers()
    if not query:
        return df.head(limit)
    q = query.strip().lower()
    mask = df["ticker"].str.lower().str.contains(q) | df["name"].str.lower().str.contains(q)
    return df[mask].head(limit)
