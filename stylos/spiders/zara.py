from datetime import datetime
import re

import scrapy
from itemloaders import ItemLoader
from stylos.items import ProductItem, ImagenItem

class ZaraSpider(scrapy.Spider):
    """
    Spider refactorizado que solo procesa datos estructurados del middleware.
    No tiene dependencias directas con Selenium ni lógica de extracción compleja.
    """
    name = "zara"
    allowed_domains = ["zara.com", "www.zara.com", "zara.net", "static.zara.net", "zara.com.co"]
    start_urls = [
        "https://www.zara.com/co/",
    ]
    
    def start_requests(self):
        """
        Genera las peticiones iniciales.

        Si se provee el argumento '-a url=<URL_DEL_PRODUCTO>', la araña procesará
        únicamente esa URL. De lo contrario, iniciará el proceso de extracción
        completo desde el menú principal.
        """
        # --- MODO DE PRUEBA ---
        if hasattr(self, 'url'):
            self.logger.info(f"Ejecutando en modo de prueba para una sola URL: {self.url}")
            yield scrapy.Request(
                url=self.url,
                callback=self.parse_product, # Llama directamente al parser de producto
                meta={
                    'selenium': True,
                    'extraction_type': 'product'
                }
            )
        # --- MODO NORMAL ---
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
        """
        Procesa URLs extraídas dinámicamente por el middleware.
        Solo recibe datos estructurados y genera nuevas peticiones.
        """
        self.logger.info(f"Procesando URLs de menú desde: {response.url}")
        
        # Obtener URLs extraídas por el middleware
        extracted_urls = response.meta.get('extracted_urls', [])
        self.logger.info(f"Recibidas {len(extracted_urls)} URLs de subcategorías")
        
        # Procesar URLs únicas
        unique_urls = set(extracted_urls)
        self.logger.info(f"URLs únicas después de eliminar duplicados: {len(unique_urls)}")
        
        # Inicializar conjunto de URLs procesadas si no existe
        if not hasattr(self, 'processed_urls'):
            self.processed_urls = set()
        
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
        """
        Extrae URLs de productos de páginas de categoría.
        El middleware ya realizó el scroll infinito.
        """
        self.logger.info(f"Extrayendo productos de: {response.url}")
        
        # Extraer URLs de productos usando selectores estándar
        products_xpath = "//div[contains(@class, 'zds-carousel-item')]//a[@href] | //li[contains(@class, 'products-category-grid-block')]//a[@href]"
        product_urls = response.xpath(products_xpath).css('::attr(href)').getall()

        for href in set(product_urls):  # Eliminar duplicados
            if re.search(r'-p\d+\.html', href):
                # Es una página de producto
                yield response.follow(
                    href, 
                    callback=self.parse_product,
                    meta={
                        'selenium': True,
                        'extraction_type': 'product'  # Especifica extracción de producto
                    }
                )
            elif re.search(r'-l\d+\.html', href):
                # Es otra página de categoría
                yield response.follow(
                    href, 
                    callback=self.parse_category,
                    meta={
                        'selenium': True, 
                        'extraction_type': 'category'
                    }
                )
            
    def parse_product(self, response):
        """
        Procesa datos de producto extraídos por el middleware.
        Toda la lógica compleja se delega al ItemLoader.
        """
        self.logger.info(f"Procesando producto: {response.url}")
        
        # Obtener datos estructurados del middleware
        product_data = response.meta.get('product_data', {})
        extracted_images = response.meta.get('extracted_images', {})
        
        # Crear ItemLoader para manejo automático de datos
        loader = ItemLoader(item=ProductItem(), selector=response)
        
        # Datos básicos del producto (del middleware o fallback al response)
        loader.add_value('url', response.url)
        
        # Nombre: priorizar middleware, fallback a response
        if product_data.get('name'):
            loader.add_value('name', product_data['name'])
        else:
            try:
                loader.add_xpath('name', "//h1[contains(@class, 'product-detail-info__header-name')]/text()")
            except Exception as e:
                self.logger.warning(f"Error extrayendo nombre con XPath: {e}")
                # Fallback a CSS selector
                name_css = response.css("h1[class*='product-detail-info__header-name']::text").get()
                if name_css:
                    loader.add_value('name', name_css.strip())
        
        # Descripción: priorizar middleware, fallback a response
        if product_data.get('description'):
            loader.add_value('description', product_data['description'])
        else:
            try:
                description_texts = response.css("div[class='expandable-text__inner-content'] p::text").getall()
                if description_texts:
                    loader.add_value('description', ' '.join(description_texts).strip())
            except Exception as e:
                self.logger.warning(f"Error extrayendo descripción: {e}")
        
        # Precios: extraer como lista simple, el pipeline se encarga del resto
        prices = product_data.get('prices', [])
        if not prices:
            # Fallback a extracción del response
            prices = response.css("div.product-detail-info__price-amount.price span.money-amount__main::text").getall()
            prices = [p.strip() for p in prices if p.strip()]
        
        # Enviar precios como lista simple al pipeline
        loader.add_value('raw_prices', prices)
        
        # Procesar imágenes extraídas por el middleware
        images_by_color = self._process_images(extracted_images, response, product_data)
        loader.add_value('images_by_color', images_by_color)
        
        # Metadatos del sistema
        loader.add_value('site', 'ZARA')
        loader.add_value('datetime', datetime.now().isoformat())
        loader.add_value('last_visited', datetime.now().isoformat())
        
        # Generar item final con todos los procesadores aplicados
        yield loader.load_item()
    
    def _process_images(self, extracted_images, response, product_data):
        """
        Procesa imágenes extraídas por el middleware con fallback al response.
        """
        images_by_color = []
        
        # Procesar imágenes del middleware si están disponibles
        if extracted_images:
            for color_name, images in extracted_images.items():
                if images:  # Solo incluir colores que tienen imágenes
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
        
        # Fallback: extraer imágenes del response si no hay datos del middleware
        if not images_by_color:
            current_color = (
                product_data.get('current_color') or
                response.css(".product-color-extended-name.product-detail-color-selector__selected-color-name::text").get() or
                response.css(".product-color-extended-name.product-detail-info__color::text").get() or
                'default'
            )
            
            # Extraer imágenes del response
            fallback_images = response.css("img.media-image__image.media__wrapper--media::attr(src)").getall()
            fallback_alts = response.css("img.media-image__image.media__wrapper--media::attr(alt)").getall()
            
            if fallback_images:
                imagen_items = []
                for i, img_src in enumerate(fallback_images[:10]):  # Máximo 10 imágenes
                    alt_text = fallback_alts[i] if i < len(fallback_alts) else ''
                    
                    imagen_item = ImagenItem()
                    imagen_item['src'] = img_src
                    imagen_item['alt'] = alt_text
                    imagen_item['img_type'] = 'product_image'
                    imagen_items.append(imagen_item)
                
                images_by_color.append({
                    'color': current_color,
                    'images': imagen_items
                })
        
        return images_by_color
    
