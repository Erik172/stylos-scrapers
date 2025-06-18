from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

# Lee la URL de Scrapyd desde las variables de entorno para mayor flexibilidad
SCRAPYD_URL = os.getenv('SCRAPYD_URL', 'http://scrapyd:6800')
PROJECT_NAME = 'stylos'

app = FastAPI(
    title="API de Control de Scrapers",
    description="Una API para gestionar y ejecutar spiders de Scrapy a través de Scrapyd."
)

class ScheduleRequest(BaseModel):
    spider_name: str

@app.get("/", summary="Verificar estado de la API")
def read_root():
    """Endpoint de bienvenida y verificación de estado."""
    return {"message": "Servidor de API para Scrapers está activo."}

@app.post("/schedule", summary="Lanzar un nuevo trabajo de scraping")
def schedule_spider(request: ScheduleRequest):
    """
    Agenda la ejecución de una araña específica.

    Recibe el nombre de la araña y le pide a Scrapyd que la ejecute.
    Retorna el ID del trabajo para poder consultar su estado.
    """
    try:
        response = requests.post(
            f"{SCRAPYD_URL}/schedule.json",
            data={'project': PROJECT_NAME, 'spider': request.spider_name}
        )
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'ok':
            return {"job_id": data['jobid'], "spider": request.spider_name, "status": "scheduled"}
        else:
            raise HTTPException(status_code=500, detail=data.get('message', 'Error desconocido de Scrapyd'))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"No se pudo conectar a Scrapyd: {e}")

@app.get("/status/{job_id}", summary="Consultar el estado de un trabajo")
def get_job_status(job_id: str):
    """
    Consulta el estado de un trabajo de scraping específico usando su ID.

    Posibles estados: pending, running, finished.
    """
    try:
        # Scrapyd tiene diferentes endpoints para trabajos en diferente estado
        # Este es un enfoque simplificado para consultar
        response = requests.get(f"{SCRAPYD_URL}/listjobs.json?project={PROJECT_NAME}")
        response.raise_for_status()
        jobs = response.json()

        for state in ['pending', 'running', 'finished']:
            for job in jobs.get(state, []):
                if job['id'] == job_id:
                    return {"job_id": job_id, "state": state, "spider": job['spider']}
        
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"No se pudo conectar a Scrapyd: {e}")