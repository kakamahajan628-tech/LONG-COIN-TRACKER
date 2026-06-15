# 🚀 Crypto Pump Scanner Bot (Telegram)

Yeh bot Binance ke saare USDT pairs (top 300 most-active by volume) scan karta hai,
har coin ko **multi-indicator + multi-timeframe** score deta hai (0-100), aur
**top 10 "pump phase" coins** ka detailed report Telegram pe bhejta hai —
saath me trade setup (entry / stop-loss / targets) bhi.

---

## 🧠 Concept (5 saal ke bache jaisi simple zubaan me)

Har coin ke liye bot 3 "lens" se dekhta hai:

| Timeframe | Kaam |
|---|---|
| **15m** | "Abhi kya ho raha hai?" — pump start ho raha hai kya? (volume, RSI, MFI, momentum, squeeze breakout) |
| **1h**  | "Momentum sahi direction me hai?" — MACD, RSI, EMA |
| **4h**  | "Bada trend bullish hai ya yeh sirf chhota jhatka hai?" — EMA50 |

Fir saat alag-alag indicators ko ek **report card score (0-100)** me jod diya jaata hai:

| Signal | Points |
|---|---|
| Volume Spike (sudden volume jump) | 20 |
| RSI healthy zone (overbought nahi) | 15 |
| MFI (real money flow) | 10 |
| MACD bullish momentum | 15 |
| EMA trend alignment | 15 |
| Price momentum (ROC) | 15 |
| Bollinger squeeze breakout | 10 |

Jo coins **score >= 55** cross karte hai, unme se **top 10** Telegram report me jaate hai —
har coin ke saath Entry / Stop-Loss / Target1 / Target2 / Risk:Reward bhi.

⚠️ Yeh sirf **technical signal generator** hai — financial advice nahi hai. Apna research khud karo (DYOR).

---

## 📁 Files

```
pump_scanner_bot/
├── config.py             # saari settings (timeframes, weights, thresholds)
├── indicators.py         # RSI, MFI, EMA, MACD, Bollinger Bands, ATR, ROC
├── data_fetcher.py        # Binance se coin list + candle data (async)
├── scorer.py              # scoring engine + trade setup calculator
├── report_formatter.py    # Telegram message banata hai
├── telegram_bot.py        # Telegram pe message bhejta hai
├── coinglass_fetcher.py   # OPTIONAL: CoinGlass funding-rate bonus signal
├── main.py                 # entry point - infinite scan loop
├── test_logic.py           # local test (fake data se logic verify karo)
└── requirements.txt
```

---

## ⚙️ Setup (Local)

```bash
pip install -r requirements.txt
```

Environment variables set karo (terminal me ya `.env` file me):

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-your-bot-token"
export TELEGRAM_CHAT_ID="123456789"
```

### Telegram Bot Token + Chat ID kaise milega?

1. Telegram me **@BotFather** ko open karo → `/newbot` → naam do → token milega
2. Apne naye bot ko ek group me add karo (ya direct DM karo) aur ek message bhejo
3. Browser me yeh URL kholo (apna token daal kar):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. JSON response me `"chat":{"id": ...}` wala number = `TELEGRAM_CHAT_ID`

### Run karo

```bash
python main.py
```

Pehle hi run me console pe scan progress dikhega, fir Telegram pe report aa jayega.
Har `SCAN_INTERVAL_MINUTES` (default 15 min) baad dobara scan hota hai.

### Logic test karna ho bina Telegram/Internet ke

```bash
python test_logic.py
```

Yeh fake (synthetic) data se indicators + scoring + report format check karta hai.

---

## ☁️ Deploy karna (Render.com)

1. Yeh sara folder GitHub repo me push karo
2. Render → **New → Background Worker** (Web Service nahi — yeh continuously
   chalne wala script hai, koi HTTP port nahi)
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python main.py`
5. **Environment** tab me daalo:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - (optional) `COINGLASS_API_KEY`
6. Python version pin karna chaho to `runtime.txt` me likho: `python-3.11.4`
   (pichli baar yeh version stable raha tha)

---

## 🎛️ Customize karna (config.py)

- **`TOP_N_BY_VOLUME`** → kitne coins scan honge (default 300, Binance ke ~500
  USDT pairs me se sabse "active" wale)
- **`MIN_SCORE_TO_REPORT`** → kitna strict hona hai (55 = balanced, 70 = bahut
  strict-only-super-strong-signals, 40 = loose-more-coins-aayenge)
- **`SCAN_INTERVAL_MINUTES`** → har kitni der me dobara scan kare
- **`WEIGHTS`** → kaunsa indicator kitna important hai — apna trading style
  ke hisaab se badal sakte ho (total 100 rakhna recommended)
- **`TIMEFRAMES`** → agar tumhe slow/swing pumps chahiye to `"fast": "1h"`,
  `"medium": "4h"`, `"trend": "1d"` kar sakte ho

---

## 🔌 Extensions (agar future me chahiye)

- **CoinGlass API** (`coinglass_fetcher.py`) — funding rate / open interest ko
  bonus score me jodne ke liye. Free key chahiye hoga (CoinGlass "Hobbyist"
  plan se). Set `COINGLASS_API_KEY` env var, fir `scorer.py` me bonus logic
  add kar sakte ho.
- **OKX / Bybit / Gate.io** — `data_fetcher.py` me similar async functions add
  kar ke unke USDT pairs bhi merge kiye ja sakte hai (jaise tumhare pichle
  RSI/MFI bot me tha) — total scan universe 1000+ coins tak badh jayega.
- **CoinMarketCap / TradingView** — TradingView ka koi free public OHLCV API
  nahi hai (scraping ToS violate karta hai, isliye avoid kiya). CoinMarketCap
  free tier API key se sirf market-cap ranking ke liye coin-universe filter
  add kiya ja sakta hai — agar chahiye to bata dena, alag function bana dunga.

---

## ⚠️ Disclaimer

Yeh bot purely **technical indicators** par based hai. Crypto market bahut
volatile hai — kisi bhi signal par trade lene se pehle apna risk management
(position sizing, stop-loss) khud decide karo. Yeh financial advice nahi hai.
