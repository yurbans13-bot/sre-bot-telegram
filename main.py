import asyncio
from playwright.async_api import async_playwright
import requests
import datetime

# 🔧 Настройки
URL = "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImR5bXZ2eGtuciswb3pJUzZ4cjVrT3c9PSIsInZhbHVlIjoiS1hPRU1Fc0QvaSs2TXNjVlYvWXhRUT09IiwibWFjIjoiMTAwZGUwMWUzOTBmZmQwMjVlYTg3MmE4Yjk2ODAzNzdmZjU3YWUzMjdjYmJmNmNkMWVkYWJhMmExMTRiMmQ3NSIsInRhZyI6IiJ9"
TELEGRAM_BOT_TOKEN = "8101121299:AAG5M15XQjgLJX7zjQiPqqeiFgTTg_lVgoU"
TELEGRAM_CHAT_ID = "243580570"
CHECK_INTERVAL = 600  # 10 минут

# 📤 Отправка сообщений
def send_telegram(text):
    print("📬 Отправка в Telegram:", text)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
        )
        print("📨 Статус Telegram:", r.status_code)
        if not r.ok:
            print("⚠️ Ответ Telegram:", r.text)
    except Exception as e:
        print("❗ Ошибка при отправке Telegram:", e)

# 🔎 Проверка сайта
async def check_dates():
    print(f"🔍 [{datetime.datetime.now()}] Проверка доступных дат...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(7000)

        available = await page.locator("td:has-text('Disponible')").all()
        if available:
            days = [await d.inner_text() for d in available]
            send_telegram(f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}")
        else:
            print("⏱ Нет доступных дат.")
        await browser.close()

# 🔁 Цикл работы
async def loop():
    print("🔄 Бот запущен (интервал 20 минут)")
    await asyncio.sleep(3)
    while True:
        try:
            await check_dates()
        except Exception as e:
            print("❗ Ошибка проверки:", e)
        await asyncio.sleep(CHECK_INTERVAL)

# 🚀 Запуск
if __name__ == "__main__":
    asyncio.run(loop())
