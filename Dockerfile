FROM python:3.13-alpine

RUN apk update && apk add bash

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

# install chromedriver
RUN apk update
RUN apk add chromium chromium-chromedriver

# install libraoffice
RUN apk add libreoffice

# upgrade pip
RUN pip install --upgrade pip

# install selenium
RUN pip install -r req.txt

WORKDIR /app
COPY . /app

