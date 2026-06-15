"""
=========================================================
 CONFIG FILE - sab settings yahi se control hoti hai
=========================================================
Telegram token / chat id ko ENVIRONMENT VARIABLES se lena
hai (Render -> Environment tab me daalna), code me mat likhna.
"""

import os

# ---------- Exchange Settings (Binance public API - no key needed) ----------
BINANCE_BASE_URL = "https://api.binance.com"
QUOTE_ASSET = "USDT"          # sirf USDT pairs scan honge

# ---------- Telegram Settings ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------- Optional: CoinGlass (sirf bonus signal, free key bhi lagana hoga) ----------
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY", "")  # blank rakho to skip ho jayega

# ---------- Scan Universe ----------
# Binance par ~400-500 USDT pairs hote hai. Hum sabse liquid (high volume)
# top N ko scan karte hai - taaki dead/fake coins skip ho jaye.
TOP_N_BY_VOLUME = 300

# ---------- Report Settings ----------
TOP_N_REPORT = 10            # final report me kitne coins dikhane hai
MIN_SCORE_TO_REPORT = 55      # 0-100 me se minimum score - isse kam wale skip
SCAN_INTERVAL_MINUTES = 15    # bot kitni der me dobara scan karega

# ---------- Timeframes (multi-timeframe analysis) ----------
# fast   -> pump phase pakadne ke liye (short term momentum)
# medium -> trend confirmation
# trend  -> bada picture (fake pump filter)
TIMEFRAMES = {
    "fast": "15m",
    "medium": "1h",
    "trend": "4h",
}
KLINE_LIMIT = 100   # har timeframe me kitni candles fetch karni hai

# ---------- Scoring Weights (total = 100) ----------
# Yeh weights badal kar tum apna "style" customize kar sakte ho
WEIGHTS = {
    "volume_spike":   20,   # sudden volume jump = pump ka pehla sign
    "rsi_sweet_spot": 15,   # RSI healthy zone me ho (overbought na ho)
    "mfi_confirm":    10,   # money actually aa rahi hai coin me
    "macd_bullish":   15,   # momentum build ho raha hai
    "ema_alignment":  15,   # overall trend bullish hai
    "momentum_roc":   15,   # price kitni tezi se badh raha hai
    "bb_breakout":    10,   # squeeze ke baad breakout (calm before storm)
}

# ---------- Networking ----------
CONCURRENT_REQUESTS = 8   # ek time par max parallel API calls (rate-limit safe)
