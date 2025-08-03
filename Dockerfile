# Используем стабильную версию Python
FROM python:3.10-slim

# Обновляем пакеты и ставим зависимости для Playwright
RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg build-essential \
    libnss3 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libdrm2 libgbm1 libasound2 \
    && apt-get clean

# Копируем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright браузеры
RUN python -m playwright install

# Копируем всё приложение
COPY . /app
WORKDIR /app

# Запуск
CMD ["python", "main.py"]

