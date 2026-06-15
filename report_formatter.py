"""
=========================================================
 REPORT FORMATTER - Telegram message ready karta hai
=========================================================
"""

from datetime import datetime, timezone


def format_report(results):
    if not results:
        return (
            "🔍 <b>Pump Scanner Report</b>\n\n"
            "Is scan me koi coin threshold cross nahi kar paaya.\n"
            "Next scan ka wait karo 👀"
        )

    now = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")
    lines = [f"🚀 <b>TOP {len(results)} PUMP CANDIDATES</b>", f"🕒 {now}", ""]

    for i, r in enumerate(results, 1):
        pair = r["symbol"].replace("USDT", "/USDT")
        lines.append(f"<b>{i}. {pair}</b> — Score: <b>{r['score']}/100</b> 🔥")
        price_str = f"{r['price']:.8f}".rstrip("0").rstrip(".") if r['price'] < 1 else f"{r['price']:,.4f}"
        lines.append(f"   💰 Price: {price_str}")
        lines.append(f"   📊 RSI(15m/1h): {r['rsi_15m']} / {r['rsi_1h']}  |  MFI: {r['mfi_15m']}")
        lines.append(f"   📈 Vol Spike: {r['vol_ratio']}x  |  1hr ROC: {r['roc_1h']}%")

        if r["reasons"]:
            lines.append(f"   ✅ Signals: {', '.join(r['reasons'])}")

        lines.append("   🎯 Trade Setup (technical, ATR based):")
        lines.append(f"      • Entry: {r['entry']}")
        lines.append(f"      • Stop Loss: {r['stop_loss']}")
        lines.append(f"      • Target 1: {r['target1']}  |  Target 2: {r['target2']}")
        lines.append(f"      • Risk:Reward → T1 = 1:{r['risk_reward_t1']}  |  T2 = 1:{r['risk_reward_t2']}")
        lines.append("")

    lines.append("⚠️ <i>Yeh purely technical analysis hai, financial advice nahi. Apna risk apna decision (DYOR).</i>")
    return "\n".join(lines)
