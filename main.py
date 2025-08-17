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
    "https://reipv6.sre.gob.mx/sinna/registro/citas/eyJpdiI6ImZOWld4T0VuVWEyYTQ5a1JxV3VQeUE9PSIsInZhbHVlIjoiWmRiTlgyTGFweXRIVTZsaHVQS2lmUT09IiwibWFjIjoiNzk1NTc0NDFmZjVjMDc0YjYxODhlNTdhYTUzNzdlMDViYTQyMDI1Nzg0MTBhNjIwYjY0OWEyNTUzY2UyN2I3NyIsInRhZyI6IiJ9"
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Как часто проверяем сайт (секунды)
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "1800"))  # по умолчанию 30 мин

# Вебхук Telegram: /webhook/<token>
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "my_webhook_token").strip()

# Авто-healthcheck (по умолчанию выключен)
AUTO_HEALTHCHECK = os.environ.get("AUTO_HEALTHCHECK", "0") == "1"
HEALTHCHECK_INTERVAL = int(os.environ.get("HEALTHCHECK_INTERVAL", str(6 * 3600)))  # 6 часов

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


# ─── Фоновые циклы ─────────────────────────────────────────────────────────────
async def check_loop():
    """Периодическая проверка сайта (рассылает ДАТЫ при появлении)."""
    while True:
        try:
            await check_dates()
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"❗ Ошибка во внешнем цикле check_loop: {e}"
            )
            traceback.print_exc()

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"⏳ Ожидание {CHECK_INTERVAL} секунд...\n"
        )
        await asyncio.sleep(CHECK_INTERVAL)


async def healthcheck_loop():
    """(Опционально) авто-сообщение «бот жив» — запускается только если включено через ENV."""
    while True:
        try:
            send_telegram("✅ Бот работает. Healthcheck.")
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"❗ Ошибка healthcheck_loop: {e}"
            )
        await asyncio.sleep(HEALTHCHECK_INTERVAL)


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
    # Запускаем задачи и держим ссылки, чтобы можно было корректно остановить
    app.state.tasks = []
    app.state.tasks.append(asyncio.create_task(check_loop()))
    if AUTO_HEALTHCHECK:
        app.state.tasks.append(asyncio.create_task(healthcheck_loop()))


@app.on_event("shutdown")
async def stop_background_tasks():
    # Корректно отменяем фоновые задачи
    for t in getattr(app.state, "tasks", []):
        try:
            t.cancel()
        except Exception:
            pass


if __name__ == "__main__":
    # Render слушает этот порт (у тебя он уже проброшен в настройках)
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
