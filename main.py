import asyncio
from playwright.async_api import async_playwright
import requests

# 🔧 ДАННЫЕ
URL = "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImR5bXZ2eGtuciswb3pJUzZ4cjVrT3c9PSIsInZhbHVlIjoiS1hPRU1Fc0QvaSs2TXNjVlYvWXhRUT09IiwibWFjIjoiMTAwZGUwMWUzOTBmZmQwMjVlYTg3MmE4Yjk2ODAzNzdmZjU3YWUzMjdjYmJmNmNkMWVkYWJhMmExMTRiMmQ3NSIsInRhZyI6IiJ9"
TELEGRAM_BOT_TOKEN = "8101121299:AAG5M15XQjgLJX7zjQiPqqeiFgTTg_lVgoU"
TELEGRAM_CHAT_ID = "243580570"
CHECK_INTERVAL = 10  # интервал в секундах

# 📤 Отправка сообщений в Telegram
def send_telegram(text):
    print("📬 Отправка в Telegram:", text)
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
        )
        print("📨 Статус ответа Telegram:", response.status_code)
        if not response.ok:
            print("⚠️ Ошибка Telegram:", response.text)
    except Exception as e:
        print("❗ Ошибка при отправке Telegram:", e)

# 🔍 Проверка доступных дат
async def check_dates():
    print("🔎 Проверка доступности...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(7000)

        available = await page.locator("td:has-text('Disponible')").all()
        if available:
            days = [await a.inner_text() for a in available]
            send_telegram(f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}")
        else:
            print("⏱ Нет доступных дат.")
        await browser.close()

# 🔁 Запуск в цикле
async def loop():
    print("🔄 Бот запущен")
    await asyncio.sleep(3)  # небольшая пауза для логов
    while True:
        try:
            await check_dates()
        except Exception as e:
            print("❗ Ошибка при проверке:", e)
        await asyncio.sleep(CHECK_INTERVAL)

# 🚀 Старт
if __name__ == "__main__":
    asyncio.run(loop())
