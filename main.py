import asyncio
from playwright.async_api import async_playwright
import requests
from datetime import datetime

# 🔧 Настройки
URL = "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImR5bXZ2eGtuciswb3pJUzZ4cjVrT3c9PSIsInZhbHVlIjoiS1hPRU1Fc0QvaSs2TXNjVlYvWXhRUT09IiwibWFjIjoiMTAwZGUwMWUzOTBmZmQwMjVlYTg3MmE4Yjk2ODAzNzdmZjU3YWUzMjdjYmJmNmNkMWVkYWJhMmExMTRiMmQ3NSIsInRhZyI6IiJ9"
TELEGRAM_BOT_TOKEN = "8101121299:AAEUKSZjhkMi6k8ccHh3PQ7xKGalW3t2b_s"
TELEGRAM_CHAT_ID = "243580570"
CHECK_INTERVAL = 600  # 10 минут

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
        )
    except Exception as e:
        print("Ошибка при отправке Telegram:", e)

async def check_dates():
    print(f"🔵 {datetime.now():%Y-%m-%d %H:%M:%S} | 🔍 Проверка доступности...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(7000)

        available = await page.locator("td:has-text('Disponible')").all()
        if available:
            days = [await a.inner_text() for a in available]
            message = f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}"
            print(f"✅ {datetime.now():%Y-%m-%d %H:%M:%S} | Даты найдены!")
            send_telegram(message)
        else:
            print(f"⏱ {datetime.now():%Y-%m-%d %H:%M:%S} | Нет доступных дат.")
        await browser.close()

async def loop():
    while True:
        try:
            await check_dates()
        except Exception as e:
            print("❗ Ошибка:", e)
        print(f"⏳ Ожидание {CHECK_INTERVAL} секунд...\n")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(loop())
