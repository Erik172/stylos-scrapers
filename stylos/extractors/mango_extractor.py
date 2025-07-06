"""
Extractor específico para el sitio web de Mango.
Ejemplo de implementación para un sitio diferente con selectores y lógica distintos.
"""

import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from stylos.extractors import BaseExtractor, register_extractor


@register_extractor('mango')
class MangoExtractor(BaseExtractor):
    """
    Extractor especializado para shop.mango.com
    Implementa navegación y extracción específica para Mango.
    """
    
    # XPATH para enlaces de categorías en el footer
    CATEGORY_LINKS_XPATH = "//div[@class='SeoBanner_root__8AHkS']//a"
    
    PRODUCT_SELECTORS = {
        'name': "h1[class*='ProductDetail_title___WrC_ texts_titleL__7qeP6']",
        'prices': "span[class^='SinglePrice_crossed'], meta[itemprop='price']",
        'currency': "meta[itemprop='priceCurrency']",
        'description': "div#truncate-text > p:first-of-type",
        'color_options': "ul[class^='ColorList'] li a",
        'product_images': "ul[class^='ImageGrid'] img",
        'color_name': "section[class='ProductDetail_pdp__WwWDn'] article p[class^='ColorsSelector']",
        'current_color': "p[class^='ColorsSelector_label']"
    }
    
    SCROLL_TRIGGER_SELECTOR = ".load-more-products, .infinite-scroll-trigger"

    def extract_menu_data(self):
        """
        Extrae URLs del menú de Mango haciendo scroll al final de la página.
        Los enlaces de categorías están en el footer de la página.
        """
        self.log("Iniciando extracción de menú de Mango")
        wait = WebDriverWait(self.driver, 15)
        extracted_urls = []

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, self.CATEGORY_LINKS_XPATH)))

            # Extraer enlaces de categorías usando el XPATH específico del footer
            category_links = self.driver.find_elements(By.XPATH, self.CATEGORY_LINKS_XPATH)
            self.log(f"Encontrados {len(category_links)} enlaces en el footer")
            
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
        Realiza scroll en páginas de una categoría de Mango.
        """
        self.log("Iniciando extracción de categoría de Mango")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 30  # Límite de seguridad para evitar bucles infinitos.

        while scroll_attempts < max_attempts:
            time.sleep(0.5)
            self.driver.execute_script(f"window.scrollTo(0, {last_height/2});")
            time.sleep(1.6)
            self.driver.execute_script(f"window.scrollTo(0, {last_height/1.4});")
            time.sleep(1.5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)
            self.driver.execute_script(f"window.scrollTo(0, {last_height/2});")
            time.sleep(0.5)
            self.driver.execute_script(f"window.scrollTo(0, {last_height/1.2});")

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                self.log("Se ha alcanzado el final de la página.")
                break
            
            last_height = new_height
            scroll_attempts += 1
            
        self.log(f"Scroll infinito completado después de {scroll_attempts} intentos.")
        return {'scroll_completed': True, 'scroll_attempts': scroll_attempts}

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

    def _extract_mango_product_info(self) -> Dict[str, Any]:
        """Extrae información básica del producto con selectores de Mango."""
        product_data: Dict[str, Any] = {
            'name': None,
            'prices': [],
            'currency': None,
            'description': None
        }
        wait = WebDriverWait(self.driver, 15)
        
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])))
            
            # Nombre (selector específico de Mango)
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])
                product_data['name'] = name_element.text.strip() if name_element else None
            except Exception as e:
                self.log(f"Error extrayendo nombre: {e}", 'error')
            
            # Precios
            try:
                price_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['prices'])
                product_data['prices'] = [elem.text.strip() for elem in price_elements if elem.text.strip()]
            except Exception as e:
                self.log(f"Error extrayendo precios: {e}", 'error')
            
            # currency
            try:
                currency_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['currency'])
                product_data['currency'] = currency_element.text.strip() if currency_element else None
            except Exception as e:
                self.log(f"Error extrayendo moneda: {e}", 'error')
            
            # Descripción
            try:
                description_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['description'])
                descriptions = [elem.text.strip() for elem in description_elements if elem.text.strip()]
                product_data['description'] = ' '.join(descriptions) if descriptions else None
            except Exception as e:
                self.log(f"Error extrayendo descripción: {e}", 'error')
                
            # current color
            try:
                current_color_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['current_color'])
                product_data['current_color'] = current_color_element.text.strip() if current_color_element else None
            except Exception as e:
                self.log(f"Error extrayendo color actual: {e}", 'error')
                    
        except Exception as e:
            self.log(f"Error extrayendo datos básicos del producto de Mango: {e}", 'error')
            
        return product_data

    def _extract_mango_images_by_color(self):
        """Extrae imágenes por color específico para Mango."""
        images_by_color: Dict[str, List[Dict[str, str]]] = {}
        
        try:
            # Buscar opciones de color
            color_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_options'])
            num_colors = len(color_buttons) if color_buttons else 1
            self.log(f"Encontrados {len(color_buttons)} colores disponibles.")
            
            for i in range(num_colors):
                
                
                # Obtener el nombre del color con manejo de errores mejorado
                try:
                    color_name_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['current_color'])
                    color_name = color_name_element.text.strip() if color_name_element else f"Color_{i+1}"
                except Exception as e:
                    self.log(f"Error obteniendo nombre del color {i}: {e}", 'warning')
                    color_name = f"Color_{i+1}"
                
                self.log(f"Procesando color {i+1}/{num_colors}: '{color_name}'")
                
                # Verificar si ya procesamos este color (evitar duplicados)
                if color_name in images_by_color:
                    self.log(f"Color '{color_name}' ya procesado, asignando nombre único", 'warning')
                    color_name = f"{color_name}_{i+1}"
                
                # Extraer imágenes para el color actual
                images = self._get_current_product_images()
                
                if images:
                    images_by_color[color_name] = images
                    self.log(f"Color '{color_name}': {len(images)} imágenes extraídas")
                else:
                    self.log(f"No se encontraron imágenes válidas para el color '{color_name}'", 'warning')
                    
                    
                if len(color_buttons) > 0:
                    try:
                        # Re-buscar los botones en cada iteración para evitar StaleElementReferenceException
                        current_color_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_options'])
                        if i >= len(current_color_buttons):
                            self.log(f"Índice {i} fuera de rango para botones de color ({len(current_color_buttons)} encontrados)", 'warning')
                            break
                            
                        current_color_button = current_color_buttons[i]
                        self.driver.execute_script("arguments[0].click();", current_color_button)
                        time.sleep(1.2)
                        
                        height = self.driver.execute_script("return document.body.scrollHeight")
                        self.driver.execute_script(f"window.scrollTo(0, {height/2});")
                        time.sleep(0.5)
                        self.driver.execute_script(f"window.scrollTo(0, 0);")
                    except Exception as e:
                        self.log(f"No se pudo hacer clic en el botón de color {i}: {e}", "warning")
                        continue
                
        except Exception as e:
            self.log(f"Error en extracción de imágenes por color de Mango: {e}", 'error')
            
        return images_by_color

    def _get_current_product_images(self):
        """Obtiene las imágenes del producto actualmente mostradas en Mango."""
        self.log("Iniciando extracción de imágenes de Mango")
        images = []
        seen_urls = set()  # Para evitar duplicados
        
        try:
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['product_images'])
            self.log(f"Encontrados {len(image_elements)} elementos de imagen para procesar")
            
            # Limitar el número de imágenes a procesar para evitar sobrecarga
            image_elements = image_elements[:15]  # Máximo 15 imágenes por color
            
            for img_index, img in enumerate(image_elements):
                try:
                    # Hacer scroll hasta el elemento para asegurar que esté en viewport
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                    time.sleep(0.3)  # Espera más tiempo para la carga
                    
                    # Usar la lógica mejorada de obtención de URL
                    src = self._wait_for_image_load(img, max_attempts=3)
                    
                    if src and src not in seen_urls:
                        alt_text = img.get_attribute("alt") or f"Imagen {img_index + 1}"
                        images.append({
                            'src': src,
                            'alt': alt_text,
                            'type': 'product_image'
                        })
                        seen_urls.add(src)
                        self.log(f"Imagen válida {img_index + 1} extraída: {src[:60]}...", 'debug')
                    else:
                        if src in seen_urls:
                            self.log(f"Imagen {img_index + 1} ignorada (duplicada)", 'debug')
                        else:
                            self.log(f"Imagen {img_index + 1} ignorada (URL inválida)", 'debug')
                            
                except Exception as e:
                    self.log(f"Error procesando imagen {img_index + 1}: {e}", 'warning')
                    continue
                    
        except Exception as e:
            self.log(f"Error obteniendo imágenes actuales de Mango: {e}", 'error')
        
        self.log(f"Extracción completada: {len(images)} imágenes válidas encontradas")
        return images