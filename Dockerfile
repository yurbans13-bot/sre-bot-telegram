# ✅ Синхронизировано: базовый образ и библиотека Playwright 1.55.0
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Опционально: более удобные дефолты Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости
# ⚠️ Важно: в requirements.txt либо удали playwright, либо зафиксируй: playwright==1.55.0
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY . .

# Подстраховка: убедиться, что браузеры и deps установлены (обычно уже есть в образе)
RUN playwright install --with-deps chromium

# Порт сервиса
EXPOSE 10000

# Старт приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
