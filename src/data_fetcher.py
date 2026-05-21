"""
src/data_fetcher.py
Fetch data XAUUSD real-time dari Yahoo Finance.
"""

import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

SYMBOL   = "GC=F"
MIN_CANDLES = 250  # minimal candle untuk hitung indikator


def fetch_latest_data(n_candles: int = 300) -> pd.DataFrame:
    """
    Fetch data XAUUSD terbaru.
    Returns DataFrame OHLCV siap pakai.
    """
    try:
        logger.info(f"Fetching {SYMBOL} data...")
        df = yf.download(
            SYMBOL,
            period="30d",
            interval="1h",
            progress=False
        )

        if df.empty:
            raise ValueError("Data kosong dari Yahoo Finance")

        # Clean columns
        if hasattr(df.columns, 'droplevel'):
            try:
                df.columns = df.columns.droplevel(1)
            except Exception:
                pass

        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.index = pd.to_datetime(df.index)

        # Remove timezone
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df.dropna(inplace=True)
        df.sort_index(inplace=True)

        logger.info(f"Fetched {len(df)} candle | Last: ${df['Close'].iloc[-1]:.2f}")
        return df

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise


def get_current_price() -> float:
    """Ambil harga XAUUSD saat ini."""
    try:
        ticker = yf.Ticker(SYMBOL)
        info   = ticker.fast_info
        return float(info.last_price)
    except Exception:
        df = fetch_latest_data()
        return float(df['Close'].iloc[-1])
