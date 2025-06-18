#!/bin/bash
# app/startup.sh

set -e

echo "Esperando a que Scrapyd esté listo..."
while ! nc -z scrapyd 6800; do
  sleep 1
done
echo "Scrapyd está activo."

# 1. Navegar a la carpeta del proyecto Scrapy para el despliegue
cd stylos
echo "Desplegando proyecto 'stylos' a Scrapyd..."
scrapyd-deploy scrapyd -p stylos
# Volver al directorio de trabajo principal
cd ..

# 2. Iniciar el servidor de la API FastAPI, apuntando al módulo correcto
echo "Iniciando servidor de API FastAPI..."
# Le decimos a Uvicorn que la app está en 'app.api_server'
uvicorn app.api_server:app --host 0.0.0.0 --port 8000