from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re

import scrapy
from itemloaders import ItemLoader
from stylos.items import ProductItem, ImagenItem, normalize_price

class ZaraSpider(scrapy.Spider):
    name = "zara"
    allowed_domains = ["zara.com", "www.zara.com", "zara.net", "static.zara.net", "zara.com.co"]
    start_urls = [
        "https://www.zara.com/co/",
    ]
    
    async def start(self, response=None):
        """
        Inicia la navegación. Pide la página principal usando Selenium
        para poder interactuar con el menú de hamburguesa.
        """
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse_menu,
            meta={
                'selenium': True,
                'wait_for': self.wait_for_menu  # Función de espera personalizada
            }
        )
        
    def wait_for_menu(self, driver):
        """
        NAVEGADOR DINÁMICO DE MENÚ.
        Abre el menú, hace clic en cada categoría principal, y recolecta
        TODAS las subcategorías que aparecen dinámicamente.
        """
        self.log(f"Iniciando navegación dinámica de menú")
        wait = WebDriverWait(driver, 15)

        try:
            # --- PASO 1: ABRIR EL MENÚ DE HAMBURGUESA ---
            self.log("Buscando botón de hamburguesa...")
            
            # Múltiples selectores para el botón hamburguesa
            hamburger_selectors = [
                "//button[@aria-label='Abrir menú']",
                "//button[@aria-label='Abrir menú']//*[name()='svg']",
                ".layout-header-icon__icon",
                "//button[contains(@class, 'layout-header-icon')]",
            ]
            
            hamburger_button = None
            for selector in hamburger_selectors:
                try:
                    if selector.startswith("//"):
                        hamburger_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        hamburger_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    self.log(f"Botón hamburguesa encontrado con selector: {selector}")
                    break
                except:
                    continue
            
            if not hamburger_button:
                self.log("No se pudo encontrar el botón hamburguesa")
                return
            
            # Hacer clic en el botón hamburguesa
            hamburger_button.click()
            self.log("Clic en botón hamburguesa exitoso")
            
            # Esperar a que el menú se abra
            menu_panel_xpath = "//div[@aria-label='Menú de categorías']"
            wait.until(EC.visibility_of_element_located((By.XPATH, menu_panel_xpath)))
            time.sleep(1)  # Pausa para animaciones

        except Exception as e:
            self.log(f"No se pudo abrir el menú de hamburguesa. Error: {e}")
            return

        # --- PASO 2: PROCESAR CATEGORÍAS PRINCIPALES ---
        categories_config = [
            {
                'name': 'MUJER',
                'selector': "//span[@class='layout-categories-category__name'][normalize-space()='MUJER']",
                'subcategory_list': "(//ul[@class='layout-categories-category__subcategory-main'])[1]"
            },
            {
                'name': 'HOMBRE', 
                'selector': "//span[@class='layout-categories-category__name'][normalize-space()='HOMBRE']",
                'subcategory_list': "(//ul[@class='layout-categories-category__subcategory-main'])[2]"
            }
        ]
        
        # Almacenar URLs en el driver para que parse_menu las pueda acceder
        driver.extracted_urls = []

        for category_config in categories_config:
            try:
                category_name = category_config['name']
                self.log(f"Procesando categoría principal: '{category_name}'")
                
                # Buscar y hacer clic en la categoría
                category_element = wait.until(EC.element_to_be_clickable((By.XPATH, category_config['selector'])))
                category_element.click()
                self.log(f"Clic exitoso en categoría '{category_name}'")
                
                # Esperar a que aparezcan las subcategorías
                time.sleep(0.8)
                
                # Buscar las subcategorías usando el selector específico
                try:
                    subcategory_container = wait.until(EC.visibility_of_element_located((By.XPATH, category_config['subcategory_list'])))
                    
                    # Extraer todos los enlaces de subcategorías
                    subcategory_links = subcategory_container.find_elements(By.XPATH, ".//a[@href]")
                    
                    for link in subcategory_links:
                        href = link.get_attribute("href")
                        if href and href.strip():
                            driver.extracted_urls.append(href)
                    
                    self.log(f"Se encontraron {len(subcategory_links)} subcategorías para '{category_name}'")
                    
                except Exception as sub_error:
                    self.log(f"Error buscando subcategorías para '{category_name}': {sub_error}")
                
                # Intentar cerrar la categoría (hacer clic nuevamente)
                try:
                    category_element.click()
                    time.sleep(0.5)
                except:
                    pass

            except Exception as e:
                self.log(f"Error procesando categoría '{category_name}': {e}")
                continue

        self.log(f"Navegación de menú finalizada. Se recolectaron {len(driver.extracted_urls)} URLs en total.")
        
    def parse_menu(self, response):
        """
        ROL: PROCESAR URLS EXTRAÍDAS DINÁMICAMENTE.
        El middleware ya navegó por el menú y extrajo las URLs.
        Este método las procesa y envía a Scrapy.
        """
        self.log(f"Procesando URLs extraídas dinámicamente desde: {response.url}")
        
        # Obtener URLs extraídas por el middleware (guardadas en meta)
        extracted_urls = response.meta.get('extracted_urls', [])
        
        self.log(f"Se recibieron {len(extracted_urls)} URLs de subcategorías.")
        
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
                        'wait_for': self.wait_for_scroll # Función de scroll
                    }
                )
            
    def wait_for_scroll(self, driver):
        """
        Función de espera que realiza el scroll completo en la página.
        """
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
    def wait_for_product(self, driver):
        """
        Función de espera para productos que extrae imágenes por color.
        Hace clic en cada color disponible y recolecta sus imágenes.
        """
        wait = WebDriverWait(driver, 15)
        
        try:
            # Esperar a que se cargue la página del producto
            self.log("Esperando que se cargue la página del producto...")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[class*='product-detail-info__header-name']")))
            time.sleep(2)  # Pausa para que se cargue completamente
            
            # Diccionario para almacenar imágenes por color
            images_by_color = {}
            
            # Buscar todos los botones de color disponibles
            color_buttons_selector = ".product-detail-color-selector__colors li button"
            color_buttons = driver.find_elements(By.CSS_SELECTOR, color_buttons_selector)
            
            self.log(f"Se encontraron {len(color_buttons)} colores disponibles")
            
            for i, color_button in enumerate(color_buttons):
                try:
                    # Hacer clic en el botón de color
                    driver.execute_script("arguments[0].click();", color_button)
                    time.sleep(2)  # Esperar a que cambien las imágenes
                    
                    # Obtener el nombre del color actual (múltiples selectores)
                    color_name = None
                    color_selectors = [
                        ".product-color-extended-name.product-detail-color-selector__selected-color-name",  # Múltiples colores
                        ".product-color-extended-name.product-detail-info__color"  # Un solo color
                    ]
                    
                    for selector in color_selectors:
                        try:
                            color_name_element = driver.find_element(By.CSS_SELECTOR, selector)
                            color_name = color_name_element.text.strip()
                            if color_name:
                                break
                        except:
                            continue
                    
                    # Si no se encontró ningún color, usar fallback
                    if not color_name:
                        color_name = f"Color_{i+1}"
                    
                    # Extraer imágenes para este color usando los selectores correctos
                    # Buscar imágenes en la galería principal
                    image_elements = driver.find_elements(By.CSS_SELECTOR, "img.media-image__image.media__wrapper--media")
                    
                    images_for_color = []
                    for img in image_elements:
                        src = img.get_attribute("src")
                        alt = img.get_attribute("alt") or ""
                        if src:
                            images_for_color.append({
                                'src': src,
                                'alt': alt,
                                'type': 'product_image'
                            })
                    
                    images_by_color[color_name] = images_for_color
                    self.log(f"Color '{color_name}': {len(images_for_color)} imágenes extraídas")
                    
                except Exception as e:
                    self.log(f"Error procesando color {i+1}: {e}")
                    continue
            
            # Guardar las imágenes en el driver para que parse_product las acceda
            driver.extracted_images = images_by_color
            self.log(f"Extracción de imágenes completada. Total de colores: {len(images_by_color)}")
            
        except Exception as e:
            self.log(f"Error en wait_for_product: {e}")
            driver.extracted_images = {}
            
    def parse_category(self, response):
        """
        ROL: EXTRAER URLS DE PRODUCTOS.
        El middleware ya hizo scroll. Este método solo extrae las URLs de productos.
        """
        self.log(f"Extrayendo productos de: {response.url}")
        
        products_xpath = "//div[contains(@class, 'zds-carousel-item')]//a[@href] | //li[contains(@class, 'products-category-grid-block')]//a[@href]"
        product_urls = response.xpath(products_xpath).css('::attr(href)').getall()

        for href in set(product_urls): # Usar set para eliminar duplicados de la página actual
            if re.search(r'-p\d+\.html', href):
                # Para la página de producto, usamos Selenium con extracción de imágenes por color
                yield response.follow(
                    href, 
                    callback=self.parse_product,
                    meta={
                        'selenium': True,
                        'wait_for': self.wait_for_product  # Función para extraer imágenes por color
                    }
                )
            elif re.search(r'-l\d+\.html', href):
                # Es otra página de categoría, la volvemos a procesar
                yield response.follow(
                    href, 
                    callback=self.parse_category,
                    meta={'selenium': True, 'wait_for': self.wait_for_scroll}
                )
            
    def parse_product(self, response):
        """
        ROL: EXTRAER DATOS DEL PRODUCTO.
        Esta página se procesa con Selenium para manejar contenido dinámico.
        """
        self.log(f"Extrayendo datos de producto con Selenium: {response.url}")
        
        # Crear ItemLoader para aplicar procesadores automáticamente
        loader = ItemLoader(item=ProductItem(), response=response)
        
        # Extraer todos los precios disponibles (texto sin procesar)
        price_texts = response.css("div.product-detail-info__price-amount.price span.money-amount__main::text").getall()
        
        # Determinar precios según disponibilidad
        if len(price_texts) == 1:
            # Sin descuento - solo un precio
            current_price = original_price = price_texts[0].strip()
            has_discount = False
        elif len(price_texts) >= 2:
            # Con descuento - determinar cuál es cuál por valor numérico
            from stylos.items import normalize_price
            normalized_prices = [(price_text, normalize_price(price_text)) for price_text in price_texts]
            valid_prices = [(text, norm) for text, norm in normalized_prices if norm['amount'] is not None]
            
            if len(valid_prices) >= 2:
                # Ordenar por monto (mayor a menor)
                valid_prices.sort(key=lambda x: x[1]['amount'], reverse=True)
                original_price = valid_prices[0][0].strip()  # Mayor precio = original
                current_price = valid_prices[1][0].strip()   # Menor precio = con descuento
                has_discount = True
            else:
                # Fallback si no se pudieron normalizar
                current_price = original_price = price_texts[0].strip()
                has_discount = False
        else:
            # Sin precios encontrados
            current_price = original_price = None
            has_discount = False
        
        # Descripción del producto
        description_texts = response.css("div[class='expandable-text__inner-content'] p::text").getall()
        description_combined = ' '.join(description_texts).strip() if description_texts else None
        
        # Obtener imágenes extraídas por el middleware
        extracted_images = response.meta.get('extracted_images', {})
        
        # Estructurar imágenes por color usando ImagenItem
        images_by_color = []
        for color_name, images in extracted_images.items():
            if images:  # Solo incluir colores que tienen imágenes
                # Crear ImagenItem para cada imagen
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
        
        # Si no se extrajeron imágenes, intentar obtener al menos las del color actual
        if not images_by_color:
            # Intentar obtener el color con múltiples selectores
            current_color = (
                response.css(".product-color-extended-name.product-detail-color-selector__selected-color-name::text").get() or
                response.css(".product-color-extended-name.product-detail-info__color::text").get()
            )
            # Usar el mismo selector que en Selenium
            fallback_images = response.css("img.media-image__image.media__wrapper--media::attr(src)").getall()
            fallback_alts = response.css("img.media-image__image.media__wrapper--media::attr(alt)").getall()
            
            if fallback_images:
                imagen_items = []
                for i, img_src in enumerate(fallback_images[:10]):  # Máximo 10 imágenes
                    alt_text = fallback_alts[i] if i < len(fallback_alts) else ''
                    
                    # Crear ImagenItem para cada imagen
                    imagen_item = ImagenItem()
                    imagen_item['src'] = img_src
                    imagen_item['alt'] = alt_text
                    imagen_item['img_type'] = 'product_image'
                    imagen_items.append(imagen_item)
                
                images_by_color.append({
                    'color': current_color or 'default',
                    'images': imagen_items
                })
        
        # ===== USAR ITEMLOADER CON PROCESADORES AUTOMÁTICOS =====
        
        # Campos básicos
        loader.add_value('url', response.url)
        loader.add_xpath('name', "//h1[contains(@class, 'product-detail-info__header-name')]/text()")
        
        # Descripción (se procesa automáticamente con normalize_lowercase)
        if description_combined:
            loader.add_value('description', description_combined)
        
        # Precios originales (texto sin procesar)
        loader.add_value('original_price', original_price)
        loader.add_value('current_price', current_price)
        
        # ¡Precios normalizados automáticamente por ItemLoader!
        # Los procesadores extract_price_amount y extract_currency se ejecutan automáticamente
        loader.add_value('original_price_amount', original_price)
        loader.add_value('current_price_amount', current_price) 
        loader.add_value('currency', original_price)  # Extrae moneda automáticamente
        
        # Calcular descuento si es necesario (usando los procesadores)
        if has_discount and original_price and current_price:
            from stylos.items import normalize_price
            orig_norm = normalize_price(original_price)
            curr_norm = normalize_price(current_price)
            
            if orig_norm['amount'] and curr_norm['amount'] and orig_norm['amount'] > 0:
                discount_percentage = ((orig_norm['amount'] - curr_norm['amount']) / orig_norm['amount']) * 100
                discount_amount = orig_norm['amount'] - curr_norm['amount']
                
                loader.add_value('discount_percentage', round(discount_percentage, 2))
                loader.add_value('discount_amount', round(discount_amount, 2))
        
        loader.add_value('has_discount', has_discount)
        
        # Otros datos
        loader.add_value('images_by_color', images_by_color)
        loader.add_value('site', 'ZARA')
        loader.add_value('datetime', datetime.now().isoformat())
        loader.add_value('last_visited', datetime.now().isoformat())
        
        # Generar el item final con todos los procesadores aplicados automáticamente
        yield loader.load_item()
    
