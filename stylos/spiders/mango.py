import scrapy
from scrapy.loader import ItemLoader
from stylos.items import ProductItem, ImagenItem
from datetime import datetime

class MangoSpider(scrapy.Spider):
    name = "mango"
    allowed_domains = ["shop.mango.com"]
    start_urls = [
        "https://shop.mango.com/co/es/h/mujer",
        "https://shop.mango.com/co/es/h/hombre",
    ]

    def start_requests(self):
        if hasattr(self, 'url'):
            self.logger.info(f"Ejecutando en modo de prueba para una sola URL: {self.url}")
            yield scrapy.Request(
                url=self.url,
                callback=self.parse_product,
                meta={
                    'selenium': True,
                    'extraction_type': 'product'
                }
            )
        else:
            self.logger.info("Iniciando rastreo completo desde el menú principal.")
            for url in self.start_urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_menu,
                    meta={
                    'selenium': True,
                    'extraction_type': 'menu'
                    }
                )

    def parse_menu(self, response):
        self.logger.info(f"Procesando URLs de menú desde: {response.url}")
        extracted_urls = response.meta.get('extracted_urls', [])
        
        unique_urls = set(extracted_urls)
        self.logger.info(f"URLs únicas después de eliminar duplicados: {len(unique_urls)}")
        
        # Inicializar conjunto de URLs procesadas si no existe
        if not hasattr(self, 'processed_urls'):
            self.processed_urls = set()
        
        # Procesar URLs únicas
        for url in unique_urls:
            if url not in self.processed_urls:
                self.processed_urls.add(url)
                yield response.follow(
                    url, 
                    callback=self.parse_category,
                    meta={
                        'selenium': True,
                        'extraction_type': 'category'  # Especifica scroll infinito
                    }
                )
                
    def parse_category(self, response):
        self.logger.info(f"Extrayendo productos de: {response.url}")
        
        products_xpath = "//ul[@class='Grid_grid__fLhp5 Grid_standard__xt7_3']/li//a[@href]"
        product_urls = response.xpath(products_xpath).css('::attr(href)').getall()
        
        for href in set(product_urls):  # Eliminar duplicados
            yield response.follow(
                href, 
                callback=self.parse_product,
                meta={
                    'selenium': True,
                    'extraction_type': 'product'  # Especifica extracción de producto
                }
            )
            
    def parse_product(self, response):
        self.logger.info(f"Extrayendo datos del producto: {response.url}")
        
        product_data = response.meta.get('product_data', {})
        extracted_images = response.meta.get('extracted_images', [])
        
        loader = ItemLoader(item=ProductItem(), selector=response)
        
        # Datos básicos del producto (del middleware o fallback al response)
        loader.add_value('url', response.url)
        loader.add_value('name', product_data.get('name', ''))
        loader.add_value('description', product_data.get('description', ''))
        
        prices = product_data.get('prices', [])
        currency = product_data.get('currency', '')
        loader.add_value('raw_prices', prices)
        loader.add_value('currency', currency)
        
        images_by_color = self._process_images(extracted_images, response, product_data)
        loader.add_value('images_by_color', images_by_color)
        
        # Metadatos del sistema
        loader.add_value('site', 'MANGO')
        loader.add_value('datetime', datetime.now().isoformat())
        loader.add_value('last_visited', datetime.now().isoformat())
        
        yield loader.load_item()
        
    def _process_images(self, extracted_images, response, product_data):
        images_by_color = []
        
        if extracted_images:
            for color_name, images in extracted_images.items():
                if images:
                    imagen_items = []
                    for img_data in images:
                        imagen_item = ImagenItem()
                        imagen_item['src'] = img_data.get('src', '')
                        imagen_item['alt'] = img_data.get('alt', '')
                        imagen_item['img_type'] = img_data.get('type', 'product_image')
                        imagen_items.append(imagen_item)
                        
                    images_by_color.append({
                        'color': color_name,
                        'images': imagen_items
                    })
        
        return images_by_color