import asyncio
from playwright.async_api import async_playwright
import requests
import logging

URL = "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImR5bXZ2eGtuciswb3pJUzZ4cjVrT3c9PSIsInZhbHVlIjoiS1hPRU1Fc0QvaSs2TXNjVlYvWXhRUT09IiwibWFjIjoiMTAwZGUwMWUzOTBmZmQwMjVlYTg3MmE4Yjk2ODAzNzdmZjU3YWUzMjdjYmJmNmNkMWVkYWJhMmExMTRiMmQ3NSIsInRhZyI6IiJ9"
TELEGRAM_BOT_TOKEN = "8101121299:AAEUKSZjhkMi6k8ccHh3PQ7xKGalW3t2b_s"
TELEGRAM_CHAT_ID = "243580570"
CHECK_INTERVAL = 600  # 10 минут

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

def send_telegram(text):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
        )
        logging.info("📬 Отправлено в Telegram: %s", response.status_code)
    except Exception as e:
        logging.error("Ошибка отправки в Telegram: %s", e)

async def check_dates():
    logging.info("🔍 Проверка доступности...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(URL, timeout=60000)
            await page.wait_for_timeout(7000)
            available = await page.locator("td:has-text('Disponible')").all()
            if available:
                days = [await a.inner_text() for a in available]
                send_telegram(f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}")
            else:
                logging.info("⏱ Нет доступных дат.")
        except Exception as e:
            logging.error("⚠️ Ошибка Playwright: %s", e)
        finally:
            await browser.close()

async def loop():
    while True:
        await check_dates()
        logging.info("⏳ Ожидание %s секунд...", CHECK_INTERVAL)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(loop())
