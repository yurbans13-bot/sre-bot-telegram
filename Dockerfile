FROM python:3.10-slim

# Установка системных библиотек, необходимых для playwright
RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg build-essential \
    libnss3 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libdrm2 libgbm1 libasound2 \
    && apt-get clean

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Установка браузеров Playwright
RUN python -m playwright install

# Копируем код бота
COPY . /app
WORKDIR /app

# Запуск
CMD ["python", "main.py"]
