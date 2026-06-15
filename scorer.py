"""
=========================================================
 SCORER - har coin ko 0-100 "PUMP SCORE" deta hai
=========================================================
Soch yeh ek REPORT CARD hai:

  1) Volume Spike      (20 pts) -> achanak volume kyu badha?
  2) RSI Sweet Spot    (15 pts) -> coin "fresh" hai, thaka nahi
  3) MFI Confirm       (10 pts) -> real paisa aa raha hai
  4) MACD Bullish      (15 pts) -> momentum build ho raha hai
  5) EMA Alignment     (15 pts) -> bada trend bhi support kar raha hai
  6) Momentum / ROC    (15 pts) -> price kitni tezi se bhaag raha hai
  7) BB Breakout       (10 pts) -> "calm before storm" ke baad breakout

Total = 100. Jitna zyada score, utna strong "pump phase" signal.

Trade setup ATR (average movement) ke base par calculate hota hai -
yeh sirf TECHNICAL reference hai, financial advice nahi.
"""

from indicators import rsi, mfi, ema, macd, bollinger_bands, atr, roc
from config import WEIGHTS


def analyze_symbol(symbol, data):
    df15 = data["fast"].copy()
    df1h = data["medium"].copy()
    df4h = data["trend"].copy()

    # ---------------- 15m (fast / pump-phase) indicators ----------------
    df15["rsi"] = rsi(df15["close"], 14)
    df15["mfi"] = mfi(df15["high"], df15["low"], df15["close"], df15["volume"], 14)
    df15["vol_avg20"] = df15["volume"].rolling(20).mean()
    df15["roc"] = roc(df15["close"], 4)  # ~1hr momentum (4 x 15m)
    _, _, _, df15["bb_width"] = bollinger_bands(df15["close"], 20, 2)
    df15["bb_width_avg"] = df15["bb_width"].rolling(50).mean()
    df15["atr"] = atr(df15["high"], df15["low"], df15["close"], 14)

    last15 = df15.iloc[-1]
    prev15 = df15.iloc[-2]

    # ---------------- 1h (trend confirmation) indicators ----------------
    df1h["rsi"] = rsi(df1h["close"], 14)
    df1h["ema20"] = ema(df1h["close"], 20)
    df1h["ema50"] = ema(df1h["close"], 50)
    _, _, df1h["macd_hist"] = macd(df1h["close"])

    last1h = df1h.iloc[-1]
    prev1h = df1h.iloc[-2]

    # ---------------- 4h (macro trend filter) indicators ----------------
    df4h["ema50"] = ema(df4h["close"], 50)
    last4h = df4h.iloc[-1]

    score = 0.0
    reasons = []

    # 1) Volume Spike (15m)
    vol_avg = last15["vol_avg20"]
    vol_ratio = (last15["volume"] / vol_avg) if vol_avg and vol_avg > 0 else 0
    vol_points = min(vol_ratio / 3, 1) * WEIGHTS["volume_spike"]
    score += vol_points
    if vol_ratio >= 1.5:
        reasons.append(f"Volume {vol_ratio:.1f}x avg se zyada")

    # 2) RSI sweet spot (healthy momentum, overbought nahi)
    rsi_pts = 0.0
    if 50 <= last15["rsi"] <= 75 and last15["rsi"] > prev15["rsi"]:
        rsi_pts += WEIGHTS["rsi_sweet_spot"] * 0.6
    if 45 <= last1h["rsi"] <= 75:
        rsi_pts += WEIGHTS["rsi_sweet_spot"] * 0.4
    score += rsi_pts
    if rsi_pts > 0:
        reasons.append(f"RSI healthy zone (15m: {last15['rsi']:.0f}, 1h: {last1h['rsi']:.0f})")

    # 3) MFI confirmation (real money inflow)
    mfi_pts = 0.0
    if last15["mfi"] > 55:
        mfi_pts = WEIGHTS["mfi_confirm"] * min((last15["mfi"] - 50) / 30, 1)
    score += mfi_pts
    if mfi_pts > 0:
        reasons.append(f"Money flow positive (MFI {last15['mfi']:.0f})")

    # 4) MACD bullish momentum (1h)
    macd_pts = 0.0
    if last1h["macd_hist"] > 0 and last1h["macd_hist"] > prev1h["macd_hist"]:
        macd_pts = WEIGHTS["macd_bullish"]
    elif last1h["macd_hist"] > prev1h["macd_hist"]:
        macd_pts = WEIGHTS["macd_bullish"] * 0.4
    score += macd_pts
    if macd_pts > 0:
        reasons.append("MACD momentum building (1h)")

    # 5) EMA trend alignment (1h + 4h)
    ema_pts = 0.0
    if last1h["close"] > last1h["ema20"] > last1h["ema50"]:
        ema_pts += WEIGHTS["ema_alignment"] * 0.6
    if last4h["close"] > last4h["ema50"]:
        ema_pts += WEIGHTS["ema_alignment"] * 0.4
    score += ema_pts
    if ema_pts > 0:
        reasons.append("Uptrend structure (price > EMA20 > EMA50)")

    # 6) Momentum / Rate of Change (15m, ~1hr lookback)
    roc_val = last15["roc"] if last15["roc"] == last15["roc"] else 0  # NaN check
    roc_pts = max(min(roc_val / 5, 1), 0) * WEIGHTS["momentum_roc"]
    score += roc_pts
    if roc_val > 1:
        reasons.append(f"Price momentum +{roc_val:.1f}% (last ~1hr)")

    # 7) Bollinger squeeze -> breakout (storm se pehle ki shanti -> storm)
    bb_pts = 0.0
    bb_avg = last15["bb_width_avg"]
    if bb_avg == bb_avg and bb_avg > 0:  # not NaN
        if last15["bb_width"] > bb_avg * 1.2 and last15["close"] > prev15["close"]:
            bb_pts = WEIGHTS["bb_breakout"]
    score += bb_pts
    if bb_pts > 0:
        reasons.append("Volatility breakout after squeeze")

    score = round(min(max(score, 0), 100), 1)

    # ---------------- Trade Setup (ATR based) ----------------
    entry = float(last15["close"])
    atr_val = float(last15["atr"]) if last15["atr"] == last15["atr"] else entry * 0.01

    stop_loss = entry - 1.0 * atr_val
    target1 = entry + 1.5 * atr_val
    target2 = entry + 3.0 * atr_val
    risk = entry - stop_loss
    rr1 = (target1 - entry) / risk if risk > 0 else 0
    rr2 = (target2 - entry) / risk if risk > 0 else 0

    return {
        "symbol": symbol,
        "score": score,
        "price": entry,
        "rsi_15m": round(float(last15["rsi"]), 1),
        "rsi_1h": round(float(last1h["rsi"]), 1),
        "mfi_15m": round(float(last15["mfi"]), 1),
        "vol_ratio": round(vol_ratio, 2),
        "roc_1h": round(roc_val, 2),
        "reasons": reasons,
        "entry": round(entry, 6),
        "stop_loss": round(stop_loss, 6),
        "target1": round(target1, 6),
        "target2": round(target2, 6),
        "risk_reward_t1": round(rr1, 2),
        "risk_reward_t2": round(rr2, 2),
    }


def rank_top_coins(market_data, top_n=10, min_score=55):
    """Saare coins analyze karke, top N best score wale return karta hai."""
    results = []
    for symbol, data in market_data.items():
        try:
            result = analyze_symbol(symbol, data)
            if result["score"] >= min_score:
                results.append(result)
        except Exception:
            # kabhi kabhi koi coin ka data thoda incomplete hota hai - skip karo
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]
