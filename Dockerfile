# ✅ Базовый образ уже содержит все системные зависимости и браузеры Playwright
# Выбираем стабильный тег под Ubuntu 22.04 (Jammy)
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

# Рабочая директория
WORKDIR /app

# Ставим зависимости Python
# (если у вас нет requirements.txt — можно пропустить эти 3 строки)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Открываем порт для веб-сервиса
EXPOSE 10000

# Запускаем FastAPI через uvicorn на нужном порту
# Если у вас модуль/объект приложения называется иначе — поправьте main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
