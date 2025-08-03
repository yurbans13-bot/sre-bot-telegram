FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y curl unzip wget gnupg build-essential libnss3 libxss1 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libdrm2 libgbm1 libasound2

# Установка зависимостей проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install

# Копируем исходники
COPY . /app
WORKDIR /app

# Команда запуска
CMD ["python", "main.py"]
