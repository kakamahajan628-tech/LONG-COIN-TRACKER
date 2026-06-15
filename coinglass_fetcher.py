"""
=========================================================
 COINGLASS FETCHER (OPTIONAL EXTENSION)
=========================================================
CoinGlass ka FREE plan bhi ab API key maangta hai
(https://www.coinglass.com/pricing -> "Hobbyist" free tier).

Agar COINGLASS_API_KEY set hai (.env / Render env var), to yeh module
funding rate fetch karega - NEGATIVE funding rate ek extra bullish
signal hota hai (shorts longs ko paisa de rahe hai -> squeeze fuel).

Agar key NAHI hai, to yeh function silently None return karega aur
bot bina kisi error ke chalta rahega. Yani yeh PURA OPTIONAL hai.

----------------------------------------------------------------
KAISE USE KARE (agar key ho):
----------------------------------------------------------------
from coinglass_fetcher import get_funding_rate

funding = await get_funding_rate("BTCUSDT")
if funding is not None and funding < 0:
    score += 5   # tumhare scorer.py me bonus point add kar sakte ho
"""

import aiohttp
from config import COINGLASS_API_KEY

COINGLASS_BASE = "https://open-api-v4.coinglass.com/api"


async def get_funding_rate(symbol: str):
    """
    symbol example: 'BTCUSDT'
    Returns: float funding rate, ya None (agar key nahi/error aaya)
    """
    if not COINGLASS_API_KEY:
        return None

    url = f"{COINGLASS_BASE}/futures/funding-rate"
    headers = {"CG-API-KEY": COINGLASS_API_KEY}
    params = {"symbol": symbol}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                # CoinGlass response structure version se thoda alag ho sakta hai -
                # apni actual response dekh kar yeh parsing adjust kar lena
                return data.get("data", {}).get("fundingRate")
    except Exception:
        return None
