"""
=========================================================
 INDICATORS - saare technical indicators yahi calculate hote hai
=========================================================
Sabse simple zubaan me:
 - RSI    -> coin "thaka" hua hai ya "fresh" hai (overbought/oversold)
 - MFI    -> RSI jaisa hi but volume ko bhi count karta hai (real money flow)
 - EMA    -> average price line, trend dikhata hai
 - MACD   -> momentum building ho rahi hai ya khatam ho rahi hai
 - BBands -> price kitna "squeeze" me hai (storm se pehle ki shanti)
 - ATR    -> coin normally kitna hilta hai (stop-loss set karne ke liye)
 - ROC    -> price kitni % badla X candles me (speed of move)
"""

import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.fillna(50)


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    direction = typical_price.diff()

    pos_flow = money_flow.where(direction > 0, 0.0)
    neg_flow = money_flow.where(direction < 0, 0.0)

    pos_sum = pos_flow.rolling(period).sum()
    neg_sum = neg_flow.rolling(period).sum()

    mfr = pos_sum / neg_sum.replace(0, np.nan)
    mfi_val = 100 - (100 / (1 + mfr))
    return mfi_val.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    bandwidth = (upper - lower) / mid
    return upper, mid, lower, bandwidth


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def roc(series: pd.Series, period: int = 4) -> pd.Series:
    return (series / series.shift(period) - 1) * 100
