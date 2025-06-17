# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import IgnoreRequest

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import time
import logging

# Importar sistema de extractors (esto registra automáticamente todos los extractors)
from stylos.extractors.registry import ExtractorRegistry

class SeleniumMiddleware:
    """
    Middleware centralizado para toda la lógica de extracción con Selenium.
    El spider solo especifica el tipo de extracción requerida y recibe datos estructurados.
    """
    
    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless") # Actívalo en producción
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Deshabilitar imágenes
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        # Solo procesa las peticiones que marquemos con meta['selenium'] = True
        if not request.meta.get('selenium'):
            return None

        spider.log(f"Procesando con Selenium: {request.url}")
        self.driver.get(request.url)

        # Obtener el extractor específico para este spider
        extraction_type = request.meta.get('extraction_type', 'default')
        extracted_data = {}
        
        try:
            # Usar el sistema de extractors específicos por sitio
            extractor = ExtractorRegistry.get_extractor(spider.name, self.driver, spider)
            
            if extraction_type == 'menu':
                extracted_data = extractor.extract_menu_urls()
            elif extraction_type == 'category':
                extracted_data = extractor.extract_category_data()
            elif extraction_type == 'product':
                extracted_data = extractor.extract_product_data()
            else:
                # Espera por defecto
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
        except ValueError as e:
            spider.log(f"Error: {e}. Usando extracción por defecto.", 'warning')
            # Fallback a espera estándar si no hay extractor registrado
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            spider.log(f"Error en extracción {extraction_type}: {e}")
            
        # Crear el response con datos extraídos
        body = self.driver.page_source
        response = HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )
        
        # Pasar todos los datos extraídos al response.meta
        response.meta.update(extracted_data)
        
        return response



    def spider_closed(self):
        self.driver.quit()



class StylosSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class StylosDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

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