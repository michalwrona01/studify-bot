FROM python:3.13-alpine

RUN apk add --no-cache \
    bash \
    chromium \
    chromium-chromedriver \
    libreoffice

RUN pip install --upgrade pip

WORKDIR /app
COPY . /app

# install selenium
RUN pip install -r req.txt

