FROM python:3.13-slim

# Nieinteraktywna instalacja
ENV DEBIAN_FRONTEND=noninteractive

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libreoffice \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Katalog roboczy
WORKDIR /app

# Kopiowanie plików
COPY . /app

# Instalacja zależności Pythona
RUN pip install --no-cache-dir -r req.txt

# Zmienna środowiskowa dla Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Domyślna komenda (zmień jeśli potrzebujesz)
CMD ["python", "main.py"]
