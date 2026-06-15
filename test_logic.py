"""Quick sanity test - synthetic data ke saath indicators/scorer test karo."""

import numpy as np
import pandas as pd

from scorer import analyze_symbol, rank_top_coins
from report_formatter import format_report


def make_fake_df(n=100, trend="up", vol_spike=False, seed=1):
    rng = np.random.default_rng(seed)
    base_price = 100.0

    if trend == "up":
        drift = np.linspace(0, 15, n)
    elif trend == "down":
        drift = np.linspace(0, -15, n)
    else:
        drift = np.zeros(n)

    noise = rng.normal(0, 0.5, n)
    close = base_price + drift + np.cumsum(noise) * 0.2
    close = np.clip(close, 1, None)

    high = close + rng.uniform(0.1, 1.0, n)
    low = close - rng.uniform(0.1, 1.0, n)
    open_ = close + rng.normal(0, 0.3, n)

    volume = rng.uniform(1000, 2000, n)
    if vol_spike:
        volume[-1] = volume[:-1].mean() * 5  # last candle me bada volume spike

    df = pd.DataFrame({
        "open_time": range(n),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "close_time": range(n),
        "quote_volume": volume * close,
        "trades": 100,
        "taker_buy_base": volume / 2,
        "taker_buy_quote": volume * close / 2,
        "ignore": 0,
    })
    return df


# Case 1: Strong bullish setup with volume spike (should score high)
bullish_data = {
    "fast": make_fake_df(100, trend="up", vol_spike=True, seed=1),
    "medium": make_fake_df(100, trend="up", vol_spike=False, seed=2),
    "trend": make_fake_df(100, trend="up", vol_spike=False, seed=3),
}

# Case 2: Flat/random market (should score low)
flat_data = {
    "fast": make_fake_df(100, trend="flat", vol_spike=False, seed=10),
    "medium": make_fake_df(100, trend="flat", vol_spike=False, seed=11),
    "trend": make_fake_df(100, trend="flat", vol_spike=False, seed=12),
}

# Case 3: Downtrend (should score low)
bear_data = {
    "fast": make_fake_df(100, trend="down", vol_spike=False, seed=20),
    "medium": make_fake_df(100, trend="down", vol_spike=False, seed=21),
    "trend": make_fake_df(100, trend="down", vol_spike=False, seed=22),
}

result1 = analyze_symbol("BULLUSDT", bullish_data)
result2 = analyze_symbol("FLATUSDT", flat_data)
result3 = analyze_symbol("BEARUSDT", bear_data)

print("=== Bullish coin ===")
print(result1)
print("\n=== Flat coin ===")
print(result2)
print("\n=== Bearish coin ===")
print(result3)

# Test ranking
market_data = {
    "BULLUSDT": bullish_data,
    "FLATUSDT": flat_data,
    "BEARUSDT": bear_data,
}
top = rank_top_coins(market_data, top_n=10, min_score=0)
print("\n=== Ranked (min_score=0) ===")
for r in top:
    print(r["symbol"], r["score"])

# Test report formatting
print("\n=== Sample Telegram Report ===")
report_top = rank_top_coins(market_data, top_n=10, min_score=20)
print(format_report(report_top))
