# control_scraper.py

import argparse
import sys
import time
from typing import Dict, Any, Optional

import requests

# --- Configuración ---
# La URL base de tu API. Si la ejecutas en otro lugar, solo cambias esta línea.
API_BASE_URL = "http://localhost:8000"
PROJECT_NAME = "stylos"  # El nombre de tu proyecto en Scrapyd

def schedule_job(spider_name: str, url: Optional[str] = None, country: Optional[str] = None, lang: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Envía una petición a la API para agendar la ejecución de una araña.

    Args:
        spider_name: El nombre de la araña a ejecutar (ej. 'zara').
        url: Opcional. La URL específica de un producto para ejecutar en modo de prueba.
        country: Opcional. Código de país para spiders multi-región (ej. 'us', 'es', 'fr').
        lang: Opcional. Código de idioma para spiders multi-región (ej. 'en', 'es', 'fr').

    Returns:
        Un diccionario con la información del trabajo si fue exitoso, o None si falló.
    """
    endpoint = f"{API_BASE_URL}/schedule"
    payload = {"spider_name": spider_name}
    
    # Construir spider_args si hay argumentos adicionales
    spider_args = {}
    if url:
        spider_args["url"] = url
    if country:
        spider_args["country"] = country
    if lang:
        spider_args["lang"] = lang
    
    if spider_args:
        payload["spider_args"] = spider_args

    # Mostrar información de lo que se va a ejecutar
    if url:
        print(f"Preparando trabajo para la araña '{spider_name}' en una URL específica...")
        if country or lang:
            print(f"  🌍 Configuración regional: país='{country or 'default'}', idioma='{lang or 'default'}'")
    else:
        print(f"Preparando trabajo para la araña '{spider_name}' (corrida completa)...")
        if country or lang:
            print(f"  🌍 Configuración regional: país='{country or 'default'}', idioma='{lang or 'default'}'")

    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        # Lanza una excepción si la respuesta es un error HTTP (4xx o 5xx)
        response.raise_for_status()
        
        job_info = response.json()
        print(f"✅ Trabajo agendado con éxito. ID del trabajo: {job_info.get('job_id')}")
        
        # Mostrar argumentos usados si los hay
        used_args = job_info.get('spider_args', {})
        if used_args:
            print(f"📝 Argumentos utilizados: {used_args}")
        
        return job_info

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: No se pudo conectar a la API en {endpoint}.", file=sys.stderr)
        print(f"   Asegúrate de que los contenedores de Docker estén corriendo (`docker-compose up`).", file=sys.stderr)
        print(f"   Error original: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al agendar el trabajo: {e}", file=sys.stderr)
        return None


def monitor_job(job_id: str, poll_interval: int = 10) -> bool:
    """
    Monitorea el estado de un trabajo de Scrapyd hasta que finalice.

    Args:
        job_id: El ID del trabajo a monitorear.
        poll_interval: Segundos a esperar entre cada verificación de estado.

    Returns:
        True si el trabajo finalizó con éxito, False en caso contrario.
    """
    endpoint = f"{API_BASE_URL}/status/{job_id}"
    print(f"\n🕵️  Monitoreando el trabajo {job_id}. Verificando estado cada {poll_interval} segundos...")
    
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 404:
                # Esto puede pasar si el trabajo termina muy rápido y ya no está en la lista de 'running'
                print("✅ El trabajo ha finalizado (ya no está en la lista de activos).")
                return True
            
            response.raise_for_status()
            status_data = response.json()
            current_state = status_data.get('state', 'unknown')
            
            elapsed_time = round(time.time() - start_time)
            print(f"   [+{elapsed_time}s] Estado actual: {current_state.upper()}")

            if current_state == 'finished':
                print("🎉 ¡Trabajo finalizado con éxito!")
                return True
            
            time.sleep(poll_interval)

        except requests.exceptions.RequestException as e:
            print(f"⚠️  No se pudo verificar el estado del trabajo (reintentando...): {e}", file=sys.stderr)
            time.sleep(poll_interval)
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado durante el monitoreo: {e}", file=sys.stderr)
            return False


def main():
    """
    Función principal para parsear argumentos y orquestar la ejecución.
    """
    parser = argparse.ArgumentParser(
        description="Cliente de línea de comandos para controlar el Scraper de Stylos.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Ejecutar Zara Colombia (por defecto)
  python control_scraper.py --spider zara

  # Ejecutar Zara Estados Unidos en inglés
  python control_scraper.py --spider zara --country us --lang en

  # Ejecutar Zara España en español
  python control_scraper.py --spider zara --country es --lang es

  # Ejecutar producto específico de Zara Francia
  python control_scraper.py --spider zara --country fr --lang fr --url "https://www.zara.com/fr/fr/product-url"

  # Ejecutar Mango (no requiere country/lang)
  python control_scraper.py --spider mango
        """
    )
    parser.add_argument(
        "--spider",
        required=True,
        help="El nombre de la araña que deseas ejecutar (ej: zara, mango)."
    )
    parser.add_argument(
        "--url",
        required=False,
        help="Opcional: La URL de un producto específico para realizar una prueba."
    )
    parser.add_argument(
        "--country",
        required=False,
        help="Opcional: Código de país para spiders multi-región (ej: us, es, fr, mx, gb)."
    )
    parser.add_argument(
        "--lang",
        required=False,
        help="Opcional: Código de idioma para spiders multi-región (ej: en, es, fr, de)."
    )
    args = parser.parse_args()

    # Validaciones específicas para Zara
    if args.spider == 'zara':
        # Valores por defecto para Zara
        country = args.country or 'co'
        lang = args.lang or 'es'
        
        # Mostrar configuración que se usará
        print(f"🎯 Spider: {args.spider}")
        print(f"🌍 País: {country}")
        print(f"🗣️  Idioma: {lang}")
        if args.url:
            print(f"🔗 URL específica: {args.url}")
        print()
        
        # Agenda el trabajo con parámetros regionales
        job = schedule_job(args.spider, args.url, country, lang)
    else:
        # Para otros spiders (mango, etc.), usar configuración simple
        if args.country or args.lang:
            print(f"⚠️  Nota: Los parámetros --country y --lang son específicos para Zara.")
            print(f"   Se ignorarán para el spider '{args.spider}'.")
        
        job = schedule_job(args.spider, args.url)

    # Si el trabajo se agendó correctamente, lo monitorea
    if job and job.get("job_id"):
        monitor_job(job.get("job_id"))
    else:
        print("\nNo se pudo iniciar el monitoreo porque el trabajo no fue agendado.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()