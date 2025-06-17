"""
Extractor específico para el sitio web de Mango.
Ejemplo de implementación para un sitio diferente con selectores y lógica distintos.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from stylos.extractors import BaseExtractor, register_extractor


@register_extractor('mango')
class MangoExtractor(BaseExtractor):
    """
    Extractor especializado para shop.mango.com
    Implementa navegación y extracción específica para Mango.
    """
    
    # Configuración específica de Mango (completamente diferente a Zara)
    MENU_BUTTON_SELECTORS = [
        ".header-menu-button",
        "[data-testid='menu-button']",
        ".menu-toggle",
    ]
    
    MENU_CATEGORIES_SELECTOR = ".main-menu .category-link"
    
    PRODUCT_SELECTORS = {
        'name': ".product-name h1, .pdp-product-name",
        'prices': ".current-price, .price-current",
        'description': ".product-description p, .pdp-description",
        'color_options': ".color-selector .color-option",
        'product_images': ".product-gallery img, .pdp-images img",
        'color_name': ".selected-color-name, .color-name-selected"
    }
    
    SCROLL_TRIGGER_SELECTOR = ".load-more-products, .infinite-scroll-trigger"

    def extract_menu_urls(self):
        """
        Extrae URLs del menú de Mango (lógica específica diferente a Zara).
        """
        self.log("Iniciando extracción de menú de Mango")
        wait = WebDriverWait(self.driver, 15)
        extracted_urls = []

        try:
            # Buscar el botón de menú de Mango
            menu_button = self._find_menu_button(wait)
            if not menu_button:
                return {'extracted_urls': []}
            
            menu_button.click()
            self.log("Menú de Mango abierto exitosamente")
            time.sleep(1)

            # Extraer enlaces de categorías (diferente estructura que Zara)
            category_links = self.driver.find_elements(By.CSS_SELECTOR, self.MENU_CATEGORIES_SELECTOR)
            
            for link in category_links:
                href = link.get_attribute("href")
                if href and href.strip():
                    extracted_urls.append(href)

        except Exception as e:
            self.log(f"Error en extracción de menú de Mango: {e}", 'error')

        self.log(f"Extracción de menú de Mango completada. Total URLs: {len(extracted_urls)}")
        return {'extracted_urls': extracted_urls}

    def extract_category_data(self):
        """
        Realiza scroll en páginas de categoría de Mango (puede ser diferente a Zara).
        """
        self.log("Iniciando extracción de categoría de Mango")
        
        # Mango podría tener scroll diferente o paginación
        try:
            # Buscar si tiene botón "load more" o scroll infinito
            scroll_trigger = self.driver.find_elements(By.CSS_SELECTOR, self.SCROLL_TRIGGER_SELECTOR)
            
            if scroll_trigger:
                # Mango usa botón "load more"
                attempts = 0
                while attempts < 10:
                    try:
                        load_more_btn = self.driver.find_element(By.CSS_SELECTOR, self.SCROLL_TRIGGER_SELECTOR)
                        if load_more_btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", load_more_btn)
                            time.sleep(2)
                            attempts += 1
                        else:
                            break
                    except:
                        break
                        
                self.log(f"Carga de productos completada después de {attempts} clicks en 'load more'")
                return {'scroll_completed': True, 'load_more_clicks': attempts}
            else:
                # Fallback a scroll tradicional
                return self._traditional_scroll()
                
        except Exception as e:
            self.log(f"Error en extracción de categoría de Mango: {e}", 'error')
            return {'scroll_completed': False}

    def extract_product_data(self):
        """
        Extrae datos de producto de Mango (selectores diferentes a Zara).
        """
        self.log("Iniciando extracción de producto de Mango")
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # Esperar carga específica de Mango
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])))
            time.sleep(2)
            
            # Extraer datos básicos con selectores de Mango
            product_data = self._extract_mango_product_info()
            
            # Extraer imágenes por color (lógica específica de Mango)
            images_by_color = self._extract_mango_images_by_color()
            
            extracted_data = {
                'product_data': product_data,
                'extracted_images': images_by_color
            }
            
            self.log(f"Extracción de producto de Mango completada. Colores: {len(images_by_color)}")
            return extracted_data
            
        except Exception as e:
            self.log(f"Error en extracción de producto de Mango: {e}", 'error')
            return {'product_data': {}, 'extracted_images': {}}

    # Métodos auxiliares específicos de Mango
    
    def _find_menu_button(self, wait):
        """Encuentra el botón de menú usando selectores específicos de Mango."""
        for selector in self.MENU_BUTTON_SELECTORS:
            try:
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                self.log(f"Botón de menú de Mango encontrado con selector: {selector}")
                return element
            except:
                continue
        
        self.log("No se pudo encontrar el botón de menú de Mango", 'error')
        return None

    def _extract_mango_product_info(self):
        """Extrae información básica del producto con selectores de Mango."""
        product_data = {}
        
        try:
            # Nombre (selector específico de Mango)
            name_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])
            product_data['name'] = name_element.text.strip() if name_element else None
            
            # Precios (estructura diferente a Zara)
            price_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['prices'])
            product_data['prices'] = [elem.text.strip() for elem in price_elements if elem.text.strip()]
            
            # Descripción
            description_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['description'])
            descriptions = [elem.text.strip() for elem in description_elements if elem.text.strip()]
            product_data['description'] = ' '.join(descriptions) if descriptions else None
            
            # Color actual (selector específico de Mango)
            try:
                color_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_name'])
                product_data['current_color'] = color_element.text.strip()
            except:
                product_data['current_color'] = None
                    
        except Exception as e:
            self.log(f"Error extrayendo datos básicos del producto de Mango: {e}", 'error')
            
        return product_data

    def _extract_mango_images_by_color(self):
        """Extrae imágenes por color específico para Mango."""
        images_by_color = {}
        
        try:
            # Buscar opciones de color (diferente estructura que Zara)
            color_options = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_options'])
            self.log(f"Encontradas {len(color_options)} opciones de color en Mango")
            
            if not color_options:
                # Si no hay opciones de color, extraer imágenes del color por defecto
                color_name = "default"
                images = self._get_current_product_images()
                if images:
                    images_by_color[color_name] = images
            else:
                for i, color_option in enumerate(color_options):
                    try:
                        # Hacer clic en la opción de color
                        self.driver.execute_script("arguments[0].click();", color_option)
                        time.sleep(1.5)  # Mango puede ser más rápido que Zara
                        
                        # Obtener nombre del color (puede estar en atributo data)
                        color_name = (
                            color_option.get_attribute("data-color-name") or
                            color_option.get_attribute("title") or
                            f"Color_{i+1}"
                        )
                        
                        # Extraer imágenes
                        images = self._get_current_product_images()
                        
                        if images:
                            images_by_color[color_name] = images
                            self.log(f"Color '{color_name}': {len(images)} imágenes extraídas")
                            
                    except Exception as e:
                        self.log(f"Error procesando color {i+1} en Mango: {e}", 'error')
                        continue
                        
        except Exception as e:
            self.log(f"Error en extracción de imágenes por color de Mango: {e}", 'error')
            
        return images_by_color

    def _get_current_product_images(self):
        """Obtiene las imágenes del producto actualmente mostradas en Mango."""
        images = []
        try:
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['product_images'])
            
            for img in image_elements:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                alt = img.get_attribute("alt") or ""
                if src and "placeholder" not in src.lower():
                    images.append({
                        'src': src,
                        'alt': alt,
                        'type': 'product_image'
                    })
        except Exception as e:
            self.log(f"Error obteniendo imágenes actuales de Mango: {e}", 'error')
            
        return images

    def _traditional_scroll(self):
        """Scroll tradicional como fallback."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 15
        
        while scroll_attempts < max_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
                
            last_height = new_height
            scroll_attempts += 1
            
        self.log(f"Scroll tradicional completado después de {scroll_attempts} intentos")
        return {'scroll_completed': True, 'scroll_attempts': scroll_attempts} 