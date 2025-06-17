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

class SeleniumMiddleware:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Actívalo en producción
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Deshabilitar imágenes
        
        self.driver = webdriver.Chrome(options=chrome_options)

    @classmethod
    def from_crawler(cls, crawler):
        # Este método es usado por Scrapy para crear tus middlewares.
        s = cls()
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        # Solo procesa las peticiones que marquemos con meta['selenium'] = True
        if not request.meta.get('selenium'):
            return None

        spider.log(f"Procesando con Selenium: {request.url}")
        self.driver.get(request.url)

        # Si una función de espera está definida en meta, la ejecutamos.
        # Esto nos da control sobre qué esperar en cada página.
        if request.meta.get('wait_for'):
            wait_function = request.meta['wait_for']
            wait_function(self.driver)
        else:
            # Espera por defecto
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

        # Devuelve el HTML renderizado para que Scrapy lo procese
        body = self.driver.page_source
        
        # Crear el response
        response = HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )
        
        # Si el driver tiene URLs extraídas (del método wait_for_menu), las pasamos al response
        if hasattr(self.driver, 'extracted_urls'):
            response.meta['extracted_urls'] = self.driver.extracted_urls
            spider.log(f"Pasando {len(self.driver.extracted_urls)} URLs extraídas al response")
            # Limpiar las URLs del driver para la próxima vez
            delattr(self.driver, 'extracted_urls')
            
        # Si el driver tiene imágenes extraídas (del método wait_for_product), las pasamos al response
        if hasattr(self.driver, 'extracted_images'):
            response.meta['extracted_images'] = self.driver.extracted_images
            spider.log(f"Pasando imágenes de {len(self.driver.extracted_images)} colores al response")
            # Limpiar las imágenes del driver para la próxima vez
            delattr(self.driver, 'extracted_images')
        
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
        # that it doesn’t have a response associated.

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