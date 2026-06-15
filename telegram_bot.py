"""
=========================================================
 TELEGRAM SENDER
=========================================================
TELEGRAM_BOT_TOKEN aur TELEGRAM_CHAT_ID environment variables
me set karna hai (Render -> Environment tab).

Chat ID kaise nikale:
 1) Apne bot ko Telegram pe DM/group me add karo
 2) Ek msg bhejo
 3) Browser me yeh URL kholo:
    https://api.telegram.org/bot<TOKEN>/getUpdates
 4) Usme "chat":{"id": ...} wala number hi tumhara CHAT_ID hai
"""

import aiohttp
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID set nahi hai. Console pe print kar raha hoon:\n")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram message length limit ~4096 chars - lamba report split karo
    max_len = 3800
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]

    async with aiohttp.ClientSession() as session:
        for chunk in chunks:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            try:
                async with session.post(url, json=payload, timeout=15) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        print(f"❌ Telegram send error: {err}")
            except Exception as e:
                print(f"❌ Telegram send exception: {e}")
