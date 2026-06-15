"""
=========================================================
 DATA FETCHER - Bybit se coin list + candle data laata hai
=========================================================
Bybit public API ka use kiya hai kyunki:
 - Bina API key ke public endpoints chalte hain
 - SPOT aur FUTURES dono markets available hain
 - India me smooth chalta hai bina kisi block ke

Steps:
 1) Saare active USDT pairs ki list lo (Spot/Linear Futures)
 2) 24hr volume ke hisaab se top N sabse "active" coins chuno
 3) Har coin ke fast / medium / trend candles fetch karo (parallel)
"""

import asyncio
import aiohttp
import pandas as pd

from config import (
    BYBIT_BASE_URL,
    QUOTE_ASSET,
    TOP_N_BY_VOLUME,
    TIMEFRAMES,
    KLINE_LIMIT,
    CONCURRENT_REQUESTS,
    MARKET_TYPES,  # ["spot", "futures"] ko handle karne ke liye
)


async def get_bybit_symbols(session: aiohttp.ClientSession):
    """Bybit par active USDT pairs ki list (Spot aur Futures dono)."""
    symbols = []
    
    # Bybit me category 'spot' aur 'linear' (futures) hoti hai
    categories = []
    if "spot" in MARKET_TYPES:
        categories.append("spot")
    if "futures" in MARKET_TYPES or "linear" in MARKET_TYPES:
        categories.append("linear")

    for category in categories:
        url = f"{BYBIT_BASE_URL}/v5/market/instruments-info"
        params = {"category": category}
        
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                
                for item in data.get("result", {}).get("list", []):
                    # Sirf trading status wale aur USDT pairs select karne hain
                    if (
                        item.get("status") == "Trading" 
                        and item.get("quoteCoin") == QUOTE_ASSET
                    ):
                        symbols.append({
                            "symbol": item["symbol"],
                            "category": category
                        })
        except Exception:
            pass
            
    return symbols


async def get_top_symbols_by_volume(session: aiohttp.ClientSession, symbols_list):
    """24hr turnover/volume ke hisaab se top N coins filter karein."""
    # Bybit me spot aur linear ke tickers alag alag lane padte hain
    categories = list(set([s["category"] for s in symbols_list]))
    all_tickers = []

    for category in categories:
        url = f"{BYBIT_BASE_URL}/v5/market/tickers"
        params = {"category": category}
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    all_tickers.extend(data.get("result", {}).get("list", []))
        except Exception:
            pass

    if not all_tickers:
        return symbols_list[:TOP_N_BY_VOLUME]

    # DataFrame banakar volume parse aur sort karenge
    df = pd.DataFrame(all_tickers)
    valid_symbols = [s["symbol"] for s in symbols_list]
    df = df[df["symbol"].isin(valid_symbols)].copy()
    
    # Bybit me 'turnover' 24h quote volume (USDT amount) ko represent karta hai
    df["turnover"] = df["turnover"].astype(float)
    df = df.sort_values("turnover", ascending=False)
    
    top_symbols_names = df.head(TOP_N_BY_VOLUME)["symbol"].tolist()
    
    # Category metadata retain karne ke liye map karenge
    top_symbols = [s for s in symbols_list if s["symbol"] in top_symbols_names]
    return top_symbols


async def fetch_klines(session, symbol, category, interval, limit, semaphore):
    """Ek Bybit symbol ke liye OHLCV candles fetch karo."""
    url = f"{BYBIT_BASE_URL}/v5/market/kline"
    
    # Bybit me timeframes format standard se thoda alag ho sakta hai
    # (Bybit standard minutes accept karta hai: 15m -> 15, 1h -> 60, 4h -> 240)
    bybit_interval = interval
    if interval == "15m": bybit_interval = "15"
    elif interval == "1h": bybit_interval = "60"
    elif interval == "4h": bybit_interval = "240"

    params = {
        "category": category,
        "symbol": symbol,
        "interval": bybit_interval,
        "limit": limit
    }

    async with semaphore:
        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except Exception:
            return None

    kline_list = data.get("result", {}).get("list", [])
    if not kline_list:
        return None

    # Bybit data format: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
    # Bybit descending order (latest first) me deta hai, humein ascending chahiye analysis ke liye
    df = pd.DataFrame(kline_list, columns=[
        "open_time", "open", "high", "low", "close", "volume", "turnover"
    ])
    
    df = df.iloc[::-1].reset_index(drop=True)  # Reverse to chronological order

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    
    return df


async def fetch_all_timeframes(session, symbol_info, semaphore):
    """Ek coin ke teeno timeframes (fast, medium, trend) fetch karo."""
    result = {}
    symbol = symbol_info["symbol"]
    category = symbol_info["category"]
    
    for tf_name, tf_interval in TIMEFRAMES.items():
        result[tf_name] = await fetch_klines(
            session, symbol, category, tf_interval, KLINE_LIMIT, semaphore
        )
        await asyncio.sleep(0.02)  # Bybit rate limits safe rakhne ke liye chota pause
    return result


async def scan_market():
    """
    Main function: Bybit market scan karke
    {symbol: {"fast": df, "medium": df, "trend": df}, ...} return karta hai.
    """
    async with aiohttp.ClientSession() as session:
        all_symbols = await get_bybit_symbols(session)
        if not all_symbols:
            return {}

        top_symbols = await get_top_symbols_by_volume(session, all_symbols)

        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        market_data = {}

        for symbol_info in top_symbols:
            symbol = symbol_info["symbol"]
            data = await fetch_all_timeframes(session, symbol_info, semaphore)
            
            # Agar sab timeframes ka data properly mila tabhi list me add karenge
            if all(v is not None and len(v) >= 30 for v in data.values()):
                market_data[symbol] = data

        return market_data
