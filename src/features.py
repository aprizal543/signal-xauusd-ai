"""
src/features.py
Hitung indikator teknikal untuk inference real-time.
Harus identik dengan yang dipakai saat training.
"""

import pandas as pd
import numpy as np
import pandas_ta as ta


FEATURE_COLS = [
    'ema_9', 'ema_21', 'ema_50', 'ema_200', 'rsi',
    'macd', 'macd_signal', 'macd_hist',
    'bb_upper', 'bb_middle', 'bb_lower', 'bb_pct',
    'atr', 'return_1', 'return_5', 'return_10',
    'day_of_week', 'is_bullish', 'hl_range',
    'body_size', 'volume_ratio', 'rolling_std_20'
]

SEQUENCE_LENGTH = 60  # harus sama dengan saat training


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung semua indikator teknikal.
    Input: DataFrame OHLCV
    Output: DataFrame dengan semua fitur
    """
    df = df.copy()

    # Trend
    df['ema_9']   = ta.ema(df['Close'], length=9)
    df['ema_21']  = ta.ema(df['Close'], length=21)
    df['ema_50']  = ta.ema(df['Close'], length=50)
    df['ema_200'] = ta.ema(df['Close'], length=200)

    # Momentum
    df['rsi'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    df['macd']        = macd['MACD_12_26_9']
    df['macd_signal'] = macd['MACDs_12_26_9']
    df['macd_hist']   = macd['MACDh_12_26_9']

    # Volatility
    bb = ta.bbands(df['Close'], length=20)
    df['bb_upper']  = bb['BBU_20_2.0_2.0']
    df['bb_middle'] = bb['BBM_20_2.0_2.0']
    df['bb_lower']  = bb['BBL_20_2.0_2.0']
    df['bb_pct']    = bb['BBP_20_2.0_2.0']
    df['atr']       = ta.atr(df['High'], df['Low'], df['Close'], length=14)

    # Price features
    df['return_1']  = df['Close'].pct_change(1)  * 100
    df['return_5']  = df['Close'].pct_change(5)  * 100
    df['return_10'] = df['Close'].pct_change(10) * 100

    # Time features
    df['day_of_week'] = df.index.dayofweek
    df['is_bullish']  = (df['Close'] > df['Open']).astype(int)

    # Candle features
    df['hl_range']   = df['High'] - df['Low']
    df['body_size']  = abs(df['Close'] - df['Open'])

    # Volume
    df['volume_ma20']  = df['Volume'].rolling(20).mean()
    df['volume_ratio'] = df['Volume'] / (df['volume_ma20'] + 1e-9)

    # Rolling stats
    df['rolling_std_20'] = df['Close'].rolling(20).std()

    df.dropna(inplace=True)
    return df


def get_latest_features(df: pd.DataFrame) -> tuple:
    """
    Ambil fitur terbaru untuk prediksi.
    Returns:
        x_flat  : array 1D untuk XGBoost (1 candle terakhir)
        x_seq   : array 3D untuk LSTM (sequence 60 candle)
        latest  : dict info candle terbaru
    """
    df = compute_features(df)

    if len(df) < SEQUENCE_LENGTH:
        raise ValueError(f"Data kurang: butuh minimal {SEQUENCE_LENGTH} candle")

    # Ambil fitur
    X = df[FEATURE_COLS].values

    # XGBoost: 1 baris terakhir
    x_flat = X[-1:].reshape(1, -1)

    # LSTM: sequence 60 candle terakhir
    x_seq = X[-SEQUENCE_LENGTH:].reshape(1, SEQUENCE_LENGTH, len(FEATURE_COLS))

    # Info candle terakhir
    last = df.iloc[-1]
    latest = {
        'datetime': df.index[-1],
        'close'   : float(last['Close']),
        'rsi'     : float(last['rsi']),
        'macd'    : float(last['macd']),
        'macd_hist': float(last['macd_hist']),
        'bb_pct'  : float(last['bb_pct']),
        'atr'     : float(last['atr']),
        'ema_9'   : float(last['ema_9']),
        'ema_21'  : float(last['ema_21']),
    }

    return x_flat, x_seq, latest
