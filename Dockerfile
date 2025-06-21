FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y netcat-openbsd dos2unix --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrapy.cfg /app/

COPY ./stylos /app/stylos/
COPY ./app /app/app/
RUN dos2unix /app/app/startup.sh && \
    chmod +x /app/app/startup.sh