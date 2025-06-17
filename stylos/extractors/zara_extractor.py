"""
Extractor específico para el sitio web de Zara.
Contiene toda la lógica de navegación y extracción específica para Zara.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from stylos.extractors import BaseExtractor, register_extractor


@register_extractor('zara')
class ZaraExtractor(BaseExtractor):
    """
    Extractor especializado para Zara.com
    Implementa navegación de menús, scroll infinito y extracción de productos.
    """
    
    # Configuración específica de Zara
    HAMBURGER_SELECTORS = [
        "//button[@aria-label='Abrir menú']",
        "//button[@aria-label='Abrir menú']//*[name()='svg']",
        ".layout-header-icon__icon",
        "//button[contains(@class, 'layout-header-icon')]",
    ]
    
    MENU_PANEL_XPATH = "//div[@aria-label='Menú de categorías']"
    
    CATEGORIES_CONFIG = [
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
    
    PRODUCT_SELECTORS = {
        'name': "h1[class*='product-detail-info__header-name']",
        'prices': "div.product-detail-info__price-amount.price span.money-amount__main",
        'description': "div[class='expandable-text__inner-content'] p",
        'color_buttons': ".product-detail-color-selector__colors li button",
        'product_images': "img.media-image__image.media__wrapper--media",
        'color_name_selectors': [
            ".product-color-extended-name.product-detail-color-selector__selected-color-name",
            ".product-color-extended-name.product-detail-info__color"
        ]
    }

    def extract_menu_urls(self):
        """
        Extrae URLs del menú de Zara navegando dinámicamente.
        """
        self.log("Iniciando extracción de menú de Zara")
        wait = WebDriverWait(self.driver, 15)
        extracted_urls = []

        try:
            # Abrir menú hamburguesa
            hamburger_button = self._find_hamburger_button(wait)
            if not hamburger_button:
                return {'extracted_urls': []}
            
            hamburger_button.click()
            self.log("Menú hamburguesa abierto exitosamente")
            
            # Esperar a que se abra el menú
            wait.until(EC.visibility_of_element_located((By.XPATH, self.MENU_PANEL_XPATH)))
            time.sleep(1)

            # Procesar cada categoría
            for category_config in self.CATEGORIES_CONFIG:
                urls = self._extract_category_urls(wait, category_config)
                extracted_urls.extend(urls)

        except Exception as e:
            self.log(f"Error en extracción de menú de Zara: {e}", 'error')

        self.log(f"Extracción de menú completada. Total URLs: {len(extracted_urls)}")
        return {'extracted_urls': extracted_urls}

    def extract_category_data(self):
        """
        Realiza scroll infinito en páginas de categoría de Zara.
        """
        self.log("Iniciando extracción de categoría de Zara con scroll")
        
        # Scroll infinito específico para Zara
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 20  # Límite de seguridad
        
        while scroll_attempts < max_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
                
            last_height = new_height
            scroll_attempts += 1
            
        self.log(f"Scroll infinito completado después de {scroll_attempts} intentos")
        return {'scroll_completed': True, 'scroll_attempts': scroll_attempts}

    def extract_product_data(self):
        """
        Extrae datos completos de producto de Zara incluyendo imágenes por color.
        """
        self.log("Iniciando extracción de producto de Zara")
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # Esperar carga de la página
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])))
            time.sleep(2)
            
            # Extraer datos básicos
            product_data = self._extract_basic_product_info()
            
            # Extraer imágenes por color
            images_by_color = self._extract_images_by_color()
            
            extracted_data = {
                'product_data': product_data,
                'extracted_images': images_by_color
            }
            
            self.log(f"Extracción de producto completada. Colores: {len(images_by_color)}")
            return extracted_data
            
        except Exception as e:
            self.log(f"Error en extracción de producto de Zara: {e}", 'error')
            return {'product_data': {}, 'extracted_images': {}}

    # Métodos auxiliares específicos de Zara
    
    def _find_hamburger_button(self, wait):
        """Encuentra el botón hamburguesa usando múltiples selectores."""
        for selector in self.HAMBURGER_SELECTORS:
            try:
                if selector.startswith("//"):
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                self.log(f"Botón hamburguesa encontrado con selector: {selector}")
                return element
            except:
                continue
        
        self.log("No se pudo encontrar el botón hamburguesa", 'error')
        return None

    def _extract_category_urls(self, wait, category_config):
        """Extrae URLs de una categoría específica."""
        urls = []
        try:
            category_name = category_config['name']
            self.log(f"Procesando categoría: {category_name}")
            
            # Hacer clic en la categoría
            category_element = wait.until(EC.element_to_be_clickable((By.XPATH, category_config['selector'])))
            category_element.click()
            time.sleep(0.8)
            
            # Extraer subcategorías
            subcategory_container = wait.until(EC.visibility_of_element_located((By.XPATH, category_config['subcategory_list'])))
            subcategory_links = subcategory_container.find_elements(By.XPATH, ".//a[@href]")
            
            for link in subcategory_links:
                href = link.get_attribute("href")
                if href and href.strip():
                    urls.append(href)
            
            self.log(f"Extraídas {len(subcategory_links)} subcategorías de {category_name}")
            
            # Cerrar la categoría
            try:
                category_element.click()
                time.sleep(0.5)
            except:
                pass

        except Exception as e:
            self.log(f"Error procesando categoría {category_config['name']}: {e}", 'error')
            
        return urls

    def _extract_basic_product_info(self):
        """Extrae información básica del producto."""
        product_data = {}
        
        try:
            # Nombre
            name_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])
            product_data['name'] = name_element.text.strip() if name_element else None
            
            # Precios
            price_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['prices'])
            product_data['prices'] = [elem.text.strip() for elem in price_elements if elem.text.strip()]
            
            # Descripción
            description_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['description'])
            descriptions = [elem.text.strip() for elem in description_elements if elem.text.strip()]
            product_data['description'] = ' '.join(descriptions) if descriptions else None
            
            # Color actual
            product_data['current_color'] = self._get_current_color_name()
                    
        except Exception as e:
            self.log(f"Error extrayendo datos básicos del producto: {e}", 'error')
            
        return product_data

    def _extract_images_by_color(self):
        """Extrae imágenes organizadas por color específico para Zara."""
        images_by_color = {}
        
        try:
            # Buscar botones de color
            color_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_buttons'])
            self.log(f"Encontrados {len(color_buttons)} colores disponibles")
            
            for i, color_button in enumerate(color_buttons):
                try:
                    # Hacer clic en el color
                    self.driver.execute_script("arguments[0].click();", color_button)
                    time.sleep(2)
                    
                    # Obtener nombre del color
                    color_name = self._get_current_color_name() or f"Color_{i+1}"
                    
                    # Extraer imágenes para este color
                    image_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['product_images'])
                    
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
                    
                    if images_for_color:
                        images_by_color[color_name] = images_for_color
                        self.log(f"Color '{color_name}': {len(images_for_color)} imágenes extraídas")
                        
                except Exception as e:
                    self.log(f"Error procesando color {i+1}: {e}", 'error')
                    continue
                    
        except Exception as e:
            self.log(f"Error en extracción de imágenes por color: {e}", 'error')
            
        return images_by_color

    def _get_current_color_name(self):
        """Obtiene el nombre del color actualmente seleccionado en Zara."""
        for selector in self.PRODUCT_SELECTORS['color_name_selectors']:
            try:
                color_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                color_name = color_element.text.strip()
                if color_name:
                    return color_name
            except:
                continue
                
        return None 