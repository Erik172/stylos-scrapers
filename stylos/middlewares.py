# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.exceptions import IgnoreRequest
from itemadapter import is_item, ItemAdapter

# --- Importaciones para Selenium ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
# webdriver-manager automatiza la gestión de chromedriver en modo local
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# --- Importaciones del Proyecto ---
from stylos.extractors.registry import ExtractorRegistry

# Importar sistema de extractors (esto registra automáticamente todos los extractors)
from stylos.extractors.registry import ExtractorRegistry

class SeleniumMiddleware:
    """
    Middleware de Scrapy que procesa peticiones usando un navegador Selenium.

    Esta clase es el núcleo de la interacción con páginas dinámicas. Actúa como
    un puente entre Scrapy y Selenium, permitiendo que la araña solicite
    acciones complejas (como abrir menús o hacer scroll) sin contener código
    de Selenium directamente.

    Funciona en dos modos, configurables desde `settings.py`:
    - 'remote': Se conecta a un Selenium Grid (ideal para Docker/producción).
    - 'local': Lanza una instancia de Chrome local (ideal para depuración).
    """
    
    def __init__(self, selenium_mode: str, selenium_hub_url: str):
        """
        Inicializa el middleware con la configuración del modo de ejecución.
        Nota: El driver no se crea aquí, sino en `open_spider`.
        """
        self.selenium_mode = selenium_mode
        self.selenium_hub_url = selenium_hub_url
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        """
        Método de fábrica de Scrapy para crear una instancia del middleware.

        Lee la configuración (SELENIUM_MODE, SELENIUM_HUB_URL) desde
        `settings.py` y la pasa al constructor. También conecta el método
        `spider_closed` a la señal correspondiente para asegurar que el
        navegador se cierre correctamente al finalizar el rastreo.
        """
        s = cls(
            selenium_mode=crawler.settings.get('SELENIUM_MODE', 'remote'),
            selenium_hub_url=crawler.settings.get('SELENIUM_HUB_URL')
        )
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s
    
    def open_spider(self, spider):
        """
        Se ejecuta cuando la araña empieza. Inicializa el driver de Selenium.
        """
        options = ChromeOptions()
        # Opciones estándar para hacer el scraping más robusto y menos detectable
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        if self.selenium_mode == 'remote':
            # --- MODO DOCKER / REMOTO ---
            spider.logger.info(f"Modo Remoto: Conectando a Selenium Grid en {self.selenium_hub_url}")
            if not self.selenium_hub_url:
                raise ValueError("SELENIUM_HUB_URL no está definido en settings.py para el modo remoto.")
            # En modo remoto, siempre es headless.
            options.add_argument("--headless")
            self.driver = webdriver.Remote(command_executor=self.selenium_hub_url, options=options)
        else:
            # --- MODO LOCAL ---
            spider.logger.info("Modo Local: Iniciando instancia local de Chrome.")
            # Descomenta la siguiente línea si quieres que el navegador local también sea invisible
            # options.add_argument("--headless")
            # webdriver-manager se encarga de descargar y proveer el chromedriver compatible.
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)


    def process_request(self, request, spider):
        """
        Procesa las peticiones marcadas con `meta['selenium'] = True`.
        """
        if not request.meta.get('selenium'):
            return None # Deja pasar las peticiones normales de Scrapy

        spider.logger.debug(f"Procesando con Selenium: {request.url}")
        
        try:
            self.driver.get(request.url)

            # Usa el sistema de registro para obtener el extractor correcto para el sitio (spider.name)
            extractor = ExtractorRegistry.get_extractor(spider.name, self.driver, spider.logger)
            extraction_type = request.meta.get('extraction_type', 'default')
            extracted_data = {}

            # Enruta la petición a la función de extracción correcta
            if hasattr(extractor, f"extract_{extraction_type}_data"):
                extraction_method = getattr(extractor, f"extract_{extraction_type}_data")
                extracted_data = extraction_method()
            else:
                spider.logger.warning(f"Tipo de extracción '{extraction_type}' no definido en el extractor para '{spider.name}'.")

            # Crea una nueva respuesta de Scrapy con el contenido de la página y los datos extraídos
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
            # Si hay un error, ignora la petición para no detener el rastreo completo
            raise IgnoreRequest(f"Selenium falló al procesar {request.url}")

    def spider_closed(self, spider):
        """
        Se ejecuta cuando la araña finaliza. Cierra el navegador.
        """
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
        """
        Este método es llamado por Scrapy para cada petición antes de ser descargada.
        """
        # Comprobamos si alguno de los términos de nuestra blocklist está en la URL de la petición
        if any(term in request.url for term in self.BLOCKLIST_TERMS):
            raise IgnoreRequest("URL bloqueada")
        return None