# Dockerfile para la aplicación Scrapy

# Usamos una imagen de Python ligera
FROM python:3.11-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copiamos e instalamos las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto
COPY ./stylos /app/stylos