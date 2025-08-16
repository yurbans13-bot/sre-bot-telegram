# ✅ Обновлённый образ Playwright
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

# Рабочая директория
WORKDIR /app

# Ставим зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Открываем порт
EXPOSE 10000

# Запуск uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
