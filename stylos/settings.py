# Scrapy settings for stylos project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv, find_dotenv
from stylos.__version__ import __version__

# Busca el .env subiendo directorios desde settings.py hasta encontrarlo
load_dotenv(find_dotenv())

BOT_NAME = "stylos"

SPIDER_MODULES = ["stylos.spiders"]
NEWSPIDER_MODULE = "stylos.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "stylos (+http://www.yourdomain.com)"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Lee la URL del hub desde la variable de entorno
SELENIUM_HUB_URL = os.getenv('SELENIUM_HUB_URL', 'http://localhost:4444')
SELENIUM_MODE = os.getenv('SELENIUM_MODE', 'remote') # 'remote' es el valor por defecto, local si no queremos usar el hub

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# Número máximo de peticiones que Scrapy puede tener activas a la vez.
# Un buen punto de partida es (NÚMERO_DE_NODES_CHROME * NODE_MAX_SESSIONS)
# Si tienes 5 nodos chrome con 5 sesiones cada uno, podrías poner 25.
CONCURRENT_REQUESTS = 10

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
# Número de peticiones concurrentes por dominio.
CONCURRENT_REQUESTS_PER_DOMAIN = 8
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "stylos.middlewares.StylosSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # "stylos.middlewares.StylosDownloaderMiddleware": 543,
    "stylos.middlewares.SeleniumMiddleware": 543,
    "stylos.middlewares.BlocklistMiddleware": 544,
    "stylos.middlewares.SentryContextMiddleware": 545,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    "stylos.extensions.SentryLoggingExtension": 100,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "stylos.pipelines.DuplicatesPipeline": 100,   # Filtrar duplicados primero  
    "stylos.pipelines.PricePipeline": 200,        # Procesar precios primero
    "stylos.pipelines.MongoDBPipeline": 300,      # Guardar en MongoDB al final
    "stylos.pipelines.StylosPipeline": 400,       # Procesamiento general
}

# Activa el AutoThrottle para ajustar la velocidad dinámicamente según la carga
# del servidor de destino y el de Scrapy. Es un "control de crucero" inteligente.
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 16.0 # Intentará mantener esta concurrencia promedio
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# =============================================================================
# CONFIGURACIÓN DE MONGODB
# =============================================================================

# URI de conexión a MongoDB (incluye autenticación si es necesaria)
# Ejemplos:
# Sin autenticación: mongodb://localhost:27017
# Con autenticación: mongodb://username:password@localhost:27017
# Atlas MongoDB: mongodb+srv://username:password@cluster.mongodb.net
MONGO_URI = os.getenv("MONGO_URI")

# Nombre de la base de datos
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "stylos_scrapers")

# Nombre de la colección donde se guardarán los productos
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "products")

# Nombre de la colección para el historial de cambios (opcional)
MONGO_HISTORY_COLLECTION = os.getenv("MONGO_HISTORY_COLLECTION", "product_history")

# =============================================================================
# SENTRY CONFIGURATION
# =============================================================================

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.getenv('SCRAPY_ENV', 'development')
SENTRY_RELEASE = __version__