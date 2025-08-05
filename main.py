import asyncio
from playwright.async_api import async_playwright
import requests
from datetime import datetime
import sys
import traceback
import os

# 💬 Логируем всё в реальном времени
sys.stdout.reconfigure(line_buffering=True)

# 🔧 Настройки
URL = "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImZjeWpVNEdHNUdTZThUUysyV1VWV0E9PSIsInZhbHVlIjoiQ2t6N3hoZGdIK1Vra1U1cWg5MEt0dz09IiwibWFjIjoiODg1NDllODcyNDc4Y2RmMjZjZmYwYjRiZjQ3NGViMGRjMzViOGZlODEyYThjMDEwMTljZTIzMmRlMjVjNGQyZiIsInRhZyI6IiJ9"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 600  # 10 минут
WEBHOOK_TOKEN = "my_webhook_token"  # опционально

def send_telegram(text):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text}
        )
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📬 Telegram статус: {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❗ Ошибка Telegram: {e}")

async def check_dates():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Проверка доступности...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        try:
            await page.goto(URL, timeout=60000)
            await page.wait_for_timeout(7000)

            available = await page.query_selector_all("td:has-text('Disponible')")
            if available:
                days = [await el.inner_text() for el in available]
                send_telegram(f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ Нет доступных дат.")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Ошибка Playwright: {e}")
            traceback.print_exc()
            send_telegram(f"❗ Ошибка во время проверки: {e}")
        finally:
            await browser.close()

async def loop():
    check_count = 0
    while True:
        try:
            await check_dates()
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❗ Ошибка во внешнем цикле: {e}")
            traceback.print_exc()
            send_telegram(f"❗ Ошибка во внешнем цикле: {e}")

        check_count += 1
        if check_count % 36 == 0:  # каждые 6 часов при CHECK_INTERVAL=600
            send_telegram("✅ Бот работает. Healthcheck.")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ Ожидание {CHECK_INTERVAL} секунд...\n")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(loop())
