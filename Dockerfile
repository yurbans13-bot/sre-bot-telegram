FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libgtk-3-0 libasound2 libxshmfence1 libxss1 \
    libx11-xcb1 libxext6 libnss3 libnspr4 libdrm2 libxfixes3 libglib2.0-0 \
    libenchant-2-2 libevent-2.1-7 libflite1 libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 libharfbuzz-icu0 libhyphen0 libsecret-1-0 \
    libvpx7 libwoff1 libxslt1.1 libmanette-0.2-0 libopus0 libwebpdemux2 libsoup-3.0-0 \
    && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python -m playwright install --with-deps

CMD ["python", "main.py"]
