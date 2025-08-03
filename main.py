import asyncio
from playwright.async_api import async_playwright
import requests

# 🔧 ТВОИ ДАННЫЕ:
URL = "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImR5bXZ2eGtuciswb3pJUzZ4cjVrT3c9PSIsInZhbHVlIjoiS1hPRU1Fc0QvaSs2TXNjVlYvWXhRUT09IiwibWFjIjoiMTAwZGUwMWUzOTBmZmQwMjVlYTg3MmE4Yjk2ODAzNzdmZjU3YWUzMjdjYmJmNmNkMWVkYWJhMmExMTRiMmQ3NSIsInRhZyI6IiJ9"
TELEGRAM_BOT_TOKEN = "8101121299:AAG5M15XQjgLJX7zjQiPqqeiFgTTg_lVgoU"
TELEGRAM_CHAT_ID = "243580570"
CHECK_INTERVAL = 1800  # интервал проверки в секундах

def send_telegram(text: str):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print("Ошибка отправки в Telegram:", e)

async def check_dates():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(7000)

        available = await page.locator("td:has-text('Disponible')").all()
        if available:
            days = [await el.inner_text() for el in available]
            message = f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}"
            print(message)
            send_telegram(message)
        else:
            print("⏱ Нет доступных дат.")
        await browser.close()

async def main_loop():
    while True:
        try:
            await check_dates()
        except Exception as e:
            print("❗ Ошибка:", e)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
