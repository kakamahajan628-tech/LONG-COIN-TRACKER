"""
=========================================================
 DATA FETCHER - Binance se coin list + candle data laata hai
=========================================================
Binance public API ka use kiya hai kyunki:
 - Bilkul FREE hai, koi API key nahi chahiye
 - 500+ USDT pairs available hai
 - Fast aur reliable

Steps:
 1) Saare USDT pairs ki list lo
 2) 24hr volume ke hisaab se top N sabse "active" coins chuno
 3) Har coin ke 15m / 1h / 4h candles fetch karo (parallel, rate-limit safe)
"""

import asyncio
import aiohttp
import pandas as pd

from config import (
    BINANCE_BASE_URL,
    QUOTE_ASSET,
    TOP_N_BY_VOLUME,
    TIMEFRAMES,
    KLINE_LIMIT,
    CONCURRENT_REQUESTS,
)


async def get_usdt_symbols(session: aiohttp.ClientSession):
    """Binance par saare active USDT spot pairs ki list."""
    url = f"{BINANCE_BASE_URL}/api/v3/exchangeInfo"
    async with session.get(url) as resp:
        data = await resp.json()

    symbols = []
    for s in data.get("symbols", []):
        if (
            s.get("quoteAsset") == QUOTE_ASSET
            and s.get("status") == "TRADING"
            and s.get("isSpotTradingAllowed", False)
        ):
            symbols.append(s["symbol"])
    return symbols


async def get_top_symbols_by_volume(session: aiohttp.ClientSession, symbols):
    """24hr quote-volume ke hisaab se top N coins (sabse active wale)."""
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/24hr"
    async with session.get(url) as resp:
        data = await resp.json()

    df = pd.DataFrame(data)
    df = df[df["symbol"].isin(symbols)].copy()
    df["quoteVolume"] = df["quoteVolume"].astype(float)
    df = df.sort_values("quoteVolume", ascending=False)
    return df.head(TOP_N_BY_VOLUME)["symbol"].tolist()


async def fetch_klines(session, symbol, interval, limit, semaphore):
    """Ek symbol ke liye OHLCV candles fetch karo."""
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    async with semaphore:
        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except Exception:
            return None

    if not isinstance(data, list) or len(data) == 0:
        return None

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


async def fetch_all_timeframes(session, symbol, semaphore):
    """Ek coin ke teeno timeframes (15m, 1h, 4h) fetch karo."""
    result = {}
    for tf_name, tf_interval in TIMEFRAMES.items():
        result[tf_name] = await fetch_klines(session, symbol, tf_interval, KLINE_LIMIT, semaphore)
        await asyncio.sleep(0.03)  # thoda gap - Binance rate limit ke liye
    return result


async def scan_market():
    """
    Main function: poora market scan karke
    {symbol: {"fast": df, "medium": df, "trend": df}, ...} return karta hai
    """
    async with aiohttp.ClientSession() as session:
        all_symbols = await get_usdt_symbols(session)
        top_symbols = await get_top_symbols_by_volume(session, all_symbols)

        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        market_data = {}

        for symbol in top_symbols:
            data = await fetch_all_timeframes(session, symbol, semaphore)
            # sab timeframes ka data sahi mila aur enough candles hai to hi rakho
            if all(v is not None and len(v) >= 30 for v in data.values()):
                market_data[symbol] = data

        return market_data
