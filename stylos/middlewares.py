from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.exceptions import IgnoreRequest

# --- Importaciones para Selenium ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
# webdriver-manager automatiza la gestión de chromedriver en modo local
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# --- Importaciones del Proyecto ---
from stylos.extractors.registry import ExtractorRegistry

class SeleniumMiddleware:
    """
    Middleware de Scrapy que procesa peticiones usando un navegador Selenium.
    Funciona en dos modos, configurables desde `settings.py`:
    - 'remote': Se conecta a un Selenium Grid (ideal para Docker/producción).
    - 'local': Lanza una instancia de Chrome local (ideal para depuración).
    """

    def __init__(self, selenium_mode: str, selenium_hub_url: str):
        """Inicializa el middleware con la configuración del modo de ejecución."""
        self.selenium_mode = selenium_mode
        self.selenium_hub_url = selenium_hub_url
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        """
        Método de fábrica de Scrapy. Lee la configuración y conecta las señales.
        """
        s = cls(
            selenium_mode=crawler.settings.get('SELENIUM_MODE', 'remote'),
            selenium_hub_url=crawler.settings.get('SELENIUM_HUB_URL')
        )
        # Conectar ambas señales: apertura y cierre del spider
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def spider_opened(self, spider):
        """Se ejecuta cuando la araña empieza. Inicializa el driver de Selenium."""
        spider.logger.info(f"Configuración recibida - Modo: {self.selenium_mode}, Hub URL: {self.selenium_hub_url}")
        
        try:
            spider.logger.info("Configurando opciones de Chrome...")
            options = ChromeOptions()
            options.add_argument('--window-size=1920x1080')
            options.add_argument("--start-maximized")
            
            # User Agent consistente y moderno (evitar user agents aleatorios)
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-features=LazyImageLoading,LazyFrameLoading") # Deshabilitar la carga perezosa de imágenes y frames
            
            # Configuraciones adicionales para sitios modernos
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument("--disable-translate")
            
            # Configuraciones de idioma para consistencia
            options.add_argument('--lang=es-CO')
            options.add_experimental_option('prefs', {
                'intl.accept_languages': 'es-CO,es',
                'profile.managed_default_content_settings.images': 1
            })
            
            spider.logger.info(f"Modo Selenium: {self.selenium_mode}")
            if self.selenium_mode == 'remote':
                # MODO DOCKER: Conectarse al Selenium Grid
                spider.logger.info(f"Modo Remoto: Conectando a Selenium Grid en {self.selenium_hub_url}")
                if not self.selenium_hub_url:
                    raise ValueError("SELENIUM_HUB_URL no está definido en settings.py para el modo remoto.")
                # options.add_argument("--headless")
                spider.logger.info("Creando driver remoto...")
                self.driver = webdriver.Remote(command_executor=self.selenium_hub_url, options=options)
            else:
                # MODO LOCAL: Iniciar un navegador en tu propia máquina
                spider.logger.info("Modo Local: Iniciando instancia local de Chrome.")
                spider.logger.info("Instalando ChromeDriver...")
                service = ChromeService(ChromeDriverManager().install())
                spider.logger.info("Creando driver local...")
                options.add_argument("--headless") # descomentar para que no se vea el navegador
                self.driver = webdriver.Chrome(service=service, options=options)
                
            spider.logger.info(f"✅ Driver de Selenium inicializado correctamente en modo '{self.selenium_mode}'")
            
        except Exception as e:
            spider.logger.error(f"❌ Error crítico inicializando el driver de Selenium: {e}")
            spider.logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            spider.logger.error(f"Traceback completo: {traceback.format_exc()}")
            self.driver = None
            raise

    def process_request(self, request, spider):
        """Procesa las peticiones marcadas con `meta['selenium'] = True`."""
        if not request.meta.get('selenium'):
            return None

        # Verificar que el driver esté inicializado
        if self.driver is None:
            spider.logger.error("El driver de Selenium no está inicializado")
            raise IgnoreRequest(f"Driver no inicializado para {request.url}")

        spider.logger.debug(f"Procesando con Selenium: {request.url}")
        
        try:
            self.driver.get(request.url)

            # Usa el sistema de registro para obtener el extractor correcto
            extractor = ExtractorRegistry.get_extractor(spider.name, self.driver, spider)
            extraction_type = request.meta.get('extraction_type', 'default')
            extracted_data = {}

            # Enruta la petición a la función de extracción correcta
            if hasattr(extractor, f"extract_{extraction_type}_data"):
                extraction_method = getattr(extractor, f"extract_{extraction_type}_data")
                extracted_data = extraction_method()
            else:
                spider.logger.warning(f"Tipo de extracción '{extraction_type}' no definido.")

            body = self.driver.page_source
            response = HtmlResponse(
                self.driver.current_url,
                body=body,
                encoding='utf-8',
                request=request
            )
            response.meta.update(extracted_data)
            return response
        except Exception as e:
            spider.logger.error(f"Error fatal en SeleniumMiddleware para {request.url}: {e}")
            raise IgnoreRequest(f"Selenium falló al procesar {request.url}")

    def spider_closed(self, spider):
        """Se ejecuta cuando la araña finaliza. Cierra el navegador."""
        spider.logger.info("Cerrando el driver de Selenium.")
        if self.driver:
            self.driver.quit()

class BlocklistMiddleware:
    BLOCKLIST_TERMS = [
        'zara-50-anniversary-film-mkt15654.html',
        '/login',
        '/register',
        'mailto:'
    ]
    
    def process_request(self, request, spider):
        if any(term in request.url for term in self.BLOCKLIST_TERMS):
            raise IgnoreRequest(f"URL bloqueada por BlocklistMiddleware: {request.url}")
        return None