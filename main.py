import asyncio
import os
import sys
import traceback
from datetime import datetime

import requests
import uvicorn
from fastapi import FastAPI, Request
from playwright.async_api import async_playwright

# 💬 Логи сразу в stdout построчно (чтоб Render всё видел)
sys.stdout.reconfigure(line_buffering=True)

# ─── Настройки ─────────────────────────────────────────────────────────────────
URL = os.environ.get("TARGET_URL") or (
    "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImZjeWpVNEdHNUdTZThUUysyV1VWV0E9PSIsInZhbHVlIjoiQ2t6N3hoZGdIK1Vra1U1cWg5MEt0dz09IiwibWFjIjoiODg1NDllODcyNDc4Y2RmMjZjZmYwYjRiZjQ3NGViMGRjMzViOGZlODEyYThjMDEwMTljZTIzMmRlMjVjNGQyZiIsInRhZyI6IiJ9"
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "600"))  # сек, по умолчанию 10 мин
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "my_webhook_token").strip()  # /webhook/<token>

if not BOT_TOKEN:
    print("⚠️  ВНИМАНИЕ: TELEGRAM_BOT_TOKEN не задан в переменных окружения!")
if not CHAT_ID:
    print("⚠️  ВНИМАНИЕ: TELEGRAM_CHAT_ID не задан в переменных окружения!")

app = FastAPI()


# ─── Утилиты ───────────────────────────────────────────────────────────────────
def send_telegram(text: str, chat_id: str | None = None):
    """Отправка сообщения в Telegram. По умолчанию — в CHAT_ID,
    но можно указать любой chat_id (например, из входящей команды)."""
    try:
        target_chat = chat_id or CHAT_ID
        if not target_chat:
            print("⚠️  CHAT_ID пуст — сообщение некуда отправлять.")
            return

        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": target_chat, "text": text},
            timeout=20,
        )
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"📬 Telegram статус: {resp.status_code}"
        )
    except Exception as e:
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"❗ Ошибка Telegram: {e}"
        )


# ─── Основная проверка слотов ──────────────────────────────────────────────────
async def check_dates():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Проверка доступности...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        try:
            await page.goto(URL, timeout=60000)
            await page.wait_for_timeout(7000)

            # Ищем ячейки с текстом 'Disponible'
            available = await page.query_selector_all("td:has-text('Disponible')")

            if available:
                days = [await el.inner_text() for el in available]
                send_telegram(f"📅 Доступны даты: {', '.join(days)}\n👉 {URL}")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ Нет доступных дат.")
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"⚠️ Ошибка Playwright: {e}"
            )
            traceback.print_exc()
        finally:
            await browser.close()


# ─── Фоновый цикл ──────────────────────────────────────────────────────────────
async def loop():
    check_count = 0
    while True:
        try:
            await check_dates()
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"❗ Ошибка во внешнем цикле: {e}"
            )
            traceback.print_exc()

        check_count += 1
        # Пример: раз в 6 часов (36 * 10 мин) отправим healthcheck
        if check_count % max(1, 6 * 60 // (CHECK_INTERVAL // 60 or 1)) == 0:
            send_telegram("✅ Бот работает. Healthcheck.")

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"⏳ Ожидание {CHECK_INTERVAL} секунд...\n"
        )
        await asyncio.sleep(CHECK_INTERVAL)


# ─── Вебхуки Telegram ──────────────────────────────────────────────────────────
@app.post(f"/webhook/{WEBHOOK_TOKEN}")
async def webhook_handler(request: Request):
    data = await request.json()

    # Иногда message может быть в edited_message или channel_post
    msg = data.get("message") or data.get("edited_message") or data.get("channel_post")
    if not msg:
        return {"ok": True, "ignored": "no_message"}

    text = (msg.get("text") or "").strip()
    entities = msg.get("entities", [])
    chat_id = str(msg.get("chat", {}).get("id") or CHAT_ID)

    # Самый надёжный способ — достать команду из entities
    cmd = ""
    for e in entities:
        if e.get("type") == "bot_command":
            offset = e.get("offset", 0)
            length = e.get("length", 0)
            cmd = text[offset:offset + length]
            break

    # На всякий случай — fallback по первой "словной" команде
    if not cmd and text.startswith("/"):
        cmd = text.split()[0]

    cmd = (cmd or "").lower()
    base_cmd = cmd.split("@", 1)[0]  # /check@BotName -> /check

    if base_cmd == "/check":
        send_telegram("✅ Бот работает. Healthcheck.", chat_id=chat_id)
        return {"ok": True, "handled": "check"}

    # Здесь можно добавить другие команды: /help, /status и т.п.
    return {"ok": True, "ignored": cmd}


# ─── Служебное ─────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """Простой пинг, чтобы на / не было 404 в логах."""
    return {"ok": True, "service": "sre-bot-telegram", "time": datetime.utcnow().isoformat()}


@app.on_event("startup")
async def start_background_tasks():
    # Запускаем фоновую проверку
    asyncio.create_task(loop())


if __name__ == "__main__":
    # Render слушает этот порт (у тебя он уже проброшен в настройках)
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
