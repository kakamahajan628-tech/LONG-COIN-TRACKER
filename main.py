"""
=========================================================
 MAIN - Bot ka entry point
=========================================================
Yeh file infinite loop me chalti hai:
  1) Market scan karo (Binance se data lo)
  2) Har coin ko score do
  3) Top 10 "pump phase" coins chuno
  4) Telegram pe report bhejo
  5) SCAN_INTERVAL_MINUTES tak so jao, phir repeat

Run karne ke liye:
    python main.py
"""

import asyncio
import os
from aiohttp import web
from data_fetcher import scan_market
from scorer import rank_top_coins
from report_formatter import format_report
from telegram_bot import send_telegram_message
from config import TOP_N_REPORT, MIN_SCORE_TO_REPORT, SCAN_INTERVAL_MINUTES


async def health(request):
    return web.Response(text="Pump Scanner Bot is running ✅")


async def start_dummy_server():
    """Render free Web Service ko HTTP port chahiye - yeh chhota server bas
    ek '/' endpoint deta hai taaki Render service ko healthy samjhe.
    Asli kaam (scanning) main_loop() me ho rahega."""
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Dummy HTTP server chal raha hai port {port} par (Render health check ke liye)")


async def run_scan_cycle():
    print("🔍 Scan shuru ho gaya... market data fetch ho raha hai")
    market_data = await scan_market()
    print(f"✅ {len(market_data)} coins ka data mil gaya, ab analyze kar rahe hai...")

    top_coins = rank_top_coins(market_data, top_n=TOP_N_REPORT, min_score=MIN_SCORE_TO_REPORT)
    print(f"🏆 {len(top_coins)} coins threshold (score >= {MIN_SCORE_TO_REPORT}) cross kar paaye")

    report = format_report(top_coins)
    await send_telegram_message(report)
    print("📨 Report Telegram pe bhej diya gaya.\n")


async def main_loop():
    while True:
        try:
            await run_scan_cycle()
        except Exception as e:
            print(f"❌ Scan cycle me error: {e}")

        print(f"😴 {SCAN_INTERVAL_MINUTES} minute sone ja raha hoon, phir dobara scan karunga...\n")
        await asyncio.sleep(SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    async def runner():
        await start_dummy_server()
        await main_loop()

    asyncio.run(runner())
