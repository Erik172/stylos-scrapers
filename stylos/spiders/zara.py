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
        Inicia la navegación solicitando extracción de menú.
        """
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_menu,
                meta={
                    'selenium': True,
                    'extraction_type': 'menu'  # Especifica el tipo de extracción
                }
            )
        
    def parse_menu(self, response):
        """
        Procesa URLs extraídas dinámicamente por el middleware.
        Solo recibe datos estructurados y genera nuevas peticiones.
        """
        self.log(f"Procesando URLs de menú desde: {response.url}")
        
        # Obtener URLs extraídas por el middleware
        extracted_urls = response.meta.get('extracted_urls', [])
        self.log(f"Recibidas {len(extracted_urls)} URLs de subcategorías")
        
        # Procesar URLs únicas
        unique_urls = set(extracted_urls)
        self.log(f"URLs únicas después de eliminar duplicados: {len(unique_urls)}")
        
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
        self.log(f"Extrayendo productos de: {response.url}")
        
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
        self.log(f"Procesando producto: {response.url}")
        
        # Obtener datos estructurados del middleware
        product_data = response.meta.get('product_data', {})
        extracted_images = response.meta.get('extracted_images', {})
        
        # Crear ItemLoader para manejo automático de datos
        loader = ItemLoader(item=ProductItem(), response=response)
        
        # Datos básicos del producto (del middleware o fallback al response)
        loader.add_value('url', response.url)
        
        # Nombre: priorizar middleware, fallback a response
        if product_data.get('name'):
            loader.add_value('name', product_data['name'])
        else:
            loader.add_xpath('name', "//h1[contains(@class, 'product-detail-info__header-name')]/text()")
        
        # Descripción: priorizar middleware, fallback a response
        if product_data.get('description'):
            loader.add_value('description', product_data['description'])
        else:
            description_texts = response.css("div[class='expandable-text__inner-content'] p::text").getall()
            if description_texts:
                loader.add_value('description', ' '.join(description_texts).strip())
        
        # Precios: usar datos del middleware si disponibles
        prices = product_data.get('prices', [])
        if not prices:
            # Fallback a extracción del response
            prices = response.css("div.product-detail-info__price-amount.price span.money-amount__main::text").getall()
            prices = [p.strip() for p in prices if p.strip()]
        
        # Procesamiento de precios simplificado
        price_info = self._process_prices(prices)
        
        # Aplicar precios al loader (ItemLoader aplicará procesadores automáticamente)
        loader.add_value('original_price', price_info['original_price'])
        loader.add_value('current_price', price_info['current_price'])
        loader.add_value('original_price_amount', price_info['original_price'])
        loader.add_value('current_price_amount', price_info['current_price'])
        loader.add_value('currency', price_info['original_price'])
        loader.add_value('has_discount', price_info['has_discount'])
        
        # Calcular descuentos si hay diferencia de precios
        if price_info['has_discount'] and price_info['discount_data']:
            loader.add_value('discount_percentage', price_info['discount_data']['percentage'])
            loader.add_value('discount_amount', price_info['discount_data']['amount'])
        
        # Procesar imágenes extraídas por el middleware
        images_by_color = self._process_images(extracted_images, response, product_data)
        loader.add_value('images_by_color', images_by_color)
        
        # Metadatos del sistema
        loader.add_value('site', 'ZARA')
        loader.add_value('datetime', datetime.now().isoformat())
        loader.add_value('last_visited', datetime.now().isoformat())
        
        # Generar item final con todos los procesadores aplicados
        yield loader.load_item()
    
    def _process_prices(self, prices):
        """
        Procesa lista de precios y determina original/actual y descuentos.
        Lógica centralizada y simplificada.
        """
        price_info = {
            'original_price': None,
            'current_price': None,
            'has_discount': False,
            'discount_data': None
        }
        
        if not prices:
            return price_info
        
        if len(prices) == 1:
            # Un solo precio - sin descuento
            price_info['original_price'] = prices[0]
            price_info['current_price'] = prices[0]
            price_info['has_discount'] = False
        elif len(prices) >= 2:
            # Múltiples precios - determinar cuál es cuál por valor numérico
            from stylos.items import normalize_price
            
            normalized_prices = []
            for price_text in prices:
                norm = normalize_price(price_text)
                if norm['amount'] is not None:
                    normalized_prices.append((price_text, norm))
            
            if len(normalized_prices) >= 2:
                # Ordenar por monto (mayor a menor)
                normalized_prices.sort(key=lambda x: x[1]['amount'], reverse=True)
                
                price_info['original_price'] = normalized_prices[0][0]  # Mayor precio
                price_info['current_price'] = normalized_prices[1][0]   # Menor precio
                price_info['has_discount'] = True
                
                # Calcular descuento
                orig_amount = normalized_prices[0][1]['amount']
                curr_amount = normalized_prices[1][1]['amount']
                
                if orig_amount > 0:
                    discount_percentage = ((orig_amount - curr_amount) / orig_amount) * 100
                    discount_amount = orig_amount - curr_amount
                    
                    price_info['discount_data'] = {
                        'percentage': round(discount_percentage, 2),
                        'amount': round(discount_amount, 2)
                    }
            else:
                # Fallback si no se pudieron normalizar
                price_info['original_price'] = prices[0]
                price_info['current_price'] = prices[0]
                price_info['has_discount'] = False
        
        return price_info
    
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
    
