"""
Módulo Extractor para Zara.com (zara).

Este archivo contiene toda la lógica de web scraping específica para el sitio web
de Zara. Hereda de `BaseExtractor` y se encarga de:
- Navegar la estructura de menús dinámicos.
- Manejar el scroll infinito en las páginas de categorías.
- Extraer datos detallados de los productos, incluyendo imágenes por color.
"""

import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from stylos.extractors import BaseExtractor, register_extractor

@register_extractor('zara')
class ZaraExtractor(BaseExtractor):
    """
    Extractor especializado para el sitio web de Zara.

    Implementa la lógica de extracción para `zara.com`, manejando sus
    características dinámicas como menús desplegables, carga de imágenes por
    lazy-loading y selección de variantes de color.

    El decorador `@register_extractor('zara')` permite que la fábrica de
    extractores instancie esta clase cuando se requiera procesar una URL de Zara.
    """
    
    # --- Selectores y Configuración Específica para Zara ---
    # Se usan múltiples selectores para el menú hamburguesa para dar robustez
    # frente a posibles cambios en el frontend del sitio y diferencias de idioma.
    HAMBURGER_SELECTORS: List[str] = [
        "//button[@aria-label='Abrir menú']",  # Español
        "//button[@aria-label='Open menu']",   # Inglés
        "//button[@aria-label='Abrir menú']//*[name()='svg']",
        "//button[@aria-label='Open menu']//*[name()='svg']",
        ".layout-header-icon__icon",
        "//button[contains(@class, 'layout-header-icon')]",
        "//button[contains(@class, 'header-menu')]",
        "[data-testid='hamburger-menu']",
        "[data-qa='hamburger-menu']",
        ".hamburger-menu",
        "//button[contains(@class, 'menu-toggle')]",
        "//button[@role='button'][contains(@class, 'layout-header')]",
    ]
    
    MENU_PANEL_XPATH = "//div[@aria-label='Menú de categorías']"
    
    # Configuración para navegar las categorías principales. Cada diccionario
    # define el nombre de la categoría, el selector para hacerle clic y el
    # XPath del contenedor de sus subcategorías.
    CATEGORIES_CONFIG: List[Dict[str, str]] = [
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
    
    # Diccionario de selectores para la página de detalle de producto (PDP).
    PRODUCT_SELECTORS: Dict[str, Any] = {
        'name': "h1[class*='product-detail-info__header-name']",
        'prices': "div.product-detail-info__price-amount.price span.money-amount__main",
        'description': "div[class='expandable-text__inner-content'] p",
        'color_buttons': ".product-detail-color-selector__colors li button",
        'product_images': [
            "ul.product-detail-view__extra-images img",
            ".product-detail-view__extra-images img",
            ".product-detail-images img",
            "ul[class*='product-detail-images'] img"
        ],
        'color_name_selectors': [
            ".product-color-extended-name.product-detail-color-selector__selected-color-name",
            ".product-color-extended-name.product-detail-info__color"
        ]
    }

    def extract_menu_data(self) -> Dict[str, List[str]]:
        """
        Extrae todas las URLs de las subcategorías desde el menú principal.

        El proceso consiste en:
        1. Localizar y hacer clic en el botón del menú "hamburguesa".
        2. Esperar a que el panel del menú sea visible.
        3. Iterar sobre la configuración de categorías (HOMBRE, MUJER).
        4. Para cada categoría, hacer clic, extraer las URLs de sus subcategorías
           y luego cerrarla para proceder con la siguiente.
        5. Agregar todas las URLs encontradas a una lista.

        Returns:
            Dict[str, List[str]]: Un diccionario con la clave 'extracted_urls'
            conteniendo una lista de las URLs de subcategorías encontradas.
        """
        self.log("Iniciando extracción de menú de Zara")
        wait = WebDriverWait(self.driver, 15)
        extracted_urls: List[str] = []

        try:
            hamburger_button = self._find_hamburger_button(wait)
            if not hamburger_button:
                self.log("No se pudo abrir el menú, finalizando extracción de URLs.", 'warning')
                return {'extracted_urls': []}

            hamburger_button.click()
            self.log("Menú hamburguesa abierto exitosamente")

            wait.until(EC.visibility_of_element_located((By.XPATH, self.MENU_PANEL_XPATH)))
            time.sleep(1)  # Pausa breve para asegurar que las animaciones terminen.

            for category_config in self.CATEGORIES_CONFIG:
                urls = self._extract_category_urls(wait, category_config)
                extracted_urls.extend(urls)

        except Exception as e:
            self.log(f"Error crítico durante la extracción de menú de Zara: {e}", 'error')

        self.log(f"Extracción de menú completada. Total URLs: {len(extracted_urls)}")
        return {'extracted_urls': extracted_urls}

    def extract_category_data(self) -> Dict[str, Any]:
        """
        Realiza scroll infinito en una página de categoría para cargar todos los productos.

        Este método simula el comportamiento de un usuario que desciende por la
        página. Compara la altura del `scrollHeight` del documento antes y después
        de hacer scroll. Si la altura deja de aumentar, asume que ha llegado
        al final de la página.

        Returns:
            Dict[str, Any]: Un diccionario que confirma la finalización y el
            número de scrolls realizados.
        """
        self.log("Iniciando extracción de categoría de Zara con scroll infinito.")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 20  # Límite de seguridad para evitar bucles infinitos.

        while scroll_attempts < max_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Espera a que los nuevos productos se carguen.

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                self.log("Se ha alcanzado el final de la página.")
                break
            
            last_height = new_height
            scroll_attempts += 1
            
        self.log(f"Scroll infinito completado después de {scroll_attempts} intentos.")
        return {'scroll_completed': True, 'scroll_attempts': scroll_attempts}

    def extract_product_data(self) -> Dict[str, Any]:
        """
        Extrae la información completa de un producto, incluyendo detalles y las
        imágenes asociadas a cada color disponible.

        Orquesta la extracción llamando a métodos auxiliares para obtener:
        1. Información básica (nombre, precio, descripción).
        2. Imágenes por color, manejando la interacción con los selectores de color.

        Returns:
            Dict[str, Any]: Un diccionario con 'product_data' (información básica)
            y 'extracted_images' (imágenes agrupadas por color). En caso de error,
            devuelve diccionarios vacíos.
        """
        self.log("Iniciando extracción de datos de producto de Zara.")
        wait = WebDriverWait(self.driver, 15)

        try:
            # Esperar a que el elemento clave (nombre del producto) esté presente.
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])))

            product_data = self._extract_basic_product_info()
            images_by_color = self._extract_images_by_color()

            extracted_data = {
                'product_data': product_data,
                'extracted_images': images_by_color
            }
            
            self.log(f"Extracción de producto completada. Colores encontrados: {len(images_by_color)}")
            return extracted_data
            
        except Exception as e:
            self.log(f"Error crítico en la extracción de producto de Zara: {e}", 'error')
            return {'product_data': {}, 'extracted_images': {}}


    # --- Métodos auxiliares específicos de Zara ---
    def _find_hamburger_button(self, wait: WebDriverWait) -> Optional[WebElement]:
        """
        Encuentra el botón del menú hamburguesa usando una lista de selectores.

        Intenta localizar el elemento con cada selector de la lista `HAMBURGER_SELECTORS`
        hasta que uno tenga éxito.

        Args:
            wait (WebDriverWait): Instancia de WebDriverWait para esperas explícitas.

        Returns:
            Optional[WebElement]: El elemento del botón encontrado o `None` si no
            se localiza con ninguno de los selectores.
        """
        for selector in self.HAMBURGER_SELECTORS:
            try:
                by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
                element = wait.until(EC.element_to_be_clickable((by, selector)))
                self.log(f"Botón hamburguesa encontrado con el selector: {selector}")
                return element
            except Exception:
                continue
        
        self.log("No se pudo encontrar el botón hamburguesa con ninguno de los selectores.", 'error')
        return None

    def _extract_category_urls(self, wait: WebDriverWait, category_config: Dict[str, str]) -> List[str]:
        """
        Extrae las URLs de las subcategorías para una categoría dada.

        Args:
            wait (WebDriverWait): Instancia de WebDriverWait.
            category_config (Dict[str, str]): Diccionario con la configuración
                de la categoría a procesar.

        Returns:
            List[str]: Una lista de URLs de las subcategorías encontradas.
        """
        urls: List[str] = []
        category_name = category_config['name']
        self.log(f"Procesando categoría: {category_name}")
        
        try:
            category_element = wait.until(EC.element_to_be_clickable((By.XPATH, category_config['selector'])))
            category_element.click()
            time.sleep(0.3)  # Pausa para la animación de despliegue.

            subcategory_container = wait.until(EC.visibility_of_element_located((By.XPATH, category_config['subcategory_list'])))
            subcategory_links = subcategory_container.find_elements(By.XPATH, ".//a[@href]")

            for link in subcategory_links:
                href = link.get_attribute("href")
                if href and href.strip():
                    urls.append(href)
            
            self.log(f"Extraídas {len(urls)} subcategorías de '{category_name}'.")

            # Volver a hacer clic para cerrar el menú de la categoría actual
            # y evitar interferencias con la siguiente.
            try:
                category_element.click()
                time.sleep(0.4)
            except Exception:
                pass  # Si falla, no es crítico.

        except Exception as e:
            self.log(f"Error procesando la categoría '{category_name}': {e}", 'error')
        return urls

    def _extract_basic_product_info(self) -> Dict[str, Any]:
        """
        Extrae la información básica del producto: nombre, precios y descripción.

        Returns:
            Dict[str, Any]: Un diccionario con los datos básicos del producto.
        """
        product_data: Dict[str, Any] = {}
        wait = WebDriverWait(self.driver, 15)
        
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])))
            
            name_element = self.driver.find_element(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['name'])
            product_data['name'] = name_element.text.strip() if name_element else None
            
            price_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['prices'])
            product_data['prices'] = [elem.text.strip() for elem in price_elements if elem.text.strip()]
            
            description_elements = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['description'])
            descriptions = [elem.text.strip() for elem in description_elements if elem.text.strip()]
            product_data['description'] = ' '.join(descriptions) if descriptions else None
            
            product_data['current_color'] = self._get_current_color_name()
        
        except Exception as e:
            self.log(f"Error extrayendo datos básicos del producto: {e}", 'error')
        
        return product_data

    def _extract_images_by_color(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Orquesta la extracción de imágenes para cada variante de color del producto.

        Este es un proceso complejo que implica:
        1. Realizar un scroll sistemático para forzar la carga de todos los elementos (lazy-loading).
        2. Localizar los botones de selección de color.
        3. Iterar sobre cada botón, hacer clic para cambiar de color.
        4. Obtener el nombre del color actual.
        5. Forzar de nuevo el scroll para cargar las imágenes del nuevo color.
        6. Recolectar todas las URLs de imagen únicas y válidas para ese color.
        7. Agrupar las imágenes en un diccionario por nombre de color.

        Returns:
            Dict[str, List[Dict[str, str]]]: Un diccionario donde cada clave es
            el nombre de un color y el valor es una lista de diccionarios de imagen
            (ej. {'src': 'url', 'alt': 'texto'}).
        """
        images_by_color: Dict[str, List[Dict[str, str]]] = {}
        
        try:
            self._force_systematic_scroll()
            
            color_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_buttons'])
            num_colors = len(color_buttons) if color_buttons else 1
            self.log(f"Encontrados {len(color_buttons)} colores disponibles.")

            for i in range(num_colors):
                if len(color_buttons) > 0:
                    try:
                        # Se vuelven a buscar los botones en cada iteración para evitar StaleElementReferenceException
                        current_color_button = self.driver.find_elements(By.CSS_SELECTOR, self.PRODUCT_SELECTORS['color_buttons'])[i]
                        self.driver.execute_script("arguments[0].click();", current_color_button)
                        time.sleep(1.8)  # Espera para que el DOM se actualice con las nuevas imágenes.
                    except Exception as e:
                        self.log(f"No se pudo hacer clic en el botón de color {i}: {e}", "warning")
                        continue

                color_name = self._get_current_color_name() or f"Color_{i+1}"
                self._force_systematic_scroll()
                
                all_image_selectors = ", ".join(self.PRODUCT_SELECTORS['product_images'])
                image_elements = self.driver.find_elements(By.CSS_SELECTOR, all_image_selectors)
                
                # Filtrar elementos duplicados que pueden ser capturados por múltiples selectores.
                unique_elements: List[WebElement] = []
                seen_elements = set()
                for elem in image_elements:
                    if elem not in seen_elements:
                        unique_elements.append(elem)
                        seen_elements.add(elem)
                
                image_elements = unique_elements[:20]  # Limitar a 20 imágenes por si acaso.
                self.log(f"Procesando color '{color_name}'. Encontrados {len(image_elements)} elementos <img> únicos.")

                images_for_color: List[Dict[str, str]] = []
                seen_urls = set()

                for img_index, img_element in enumerate(image_elements):
                    try:
                        valid_src = self._wait_for_image_load(img_element, max_attempts=5)
                        
                        if valid_src and valid_src not in seen_urls:
                            alt_text = img_element.get_attribute("alt") or f"{color_name} - Imagen {img_index}"
                            images_for_color.append({
                                'src': valid_src,
                                'alt': alt_text,
                                'img_type': 'product_image'
                            })
                            seen_urls.add(valid_src)
                            self.log(f"Imagen válida extraída para {color_name}: {valid_src[:80]}...", 'debug')
                        else:
                            self.log(f"Imagen ignorada (duplicada o inválida) para {color_name}", 'debug')
                    except Exception as e:
                        self.log(f"Error procesando imagen {img_index} del color '{color_name}': {e}", 'warning')
                
                if images_for_color:
                    images_by_color[color_name] = images_for_color
                    self.log(f"Color '{color_name}': {len(images_for_color)} imágenes válidas extraídas.")
                else:
                    self.log(f"No se encontraron imágenes válidas para el color '{color_name}'.", 'warning')
        except Exception as e:
            self.log(f"Error mayor en la extracción de imágenes por color: {e}", 'error')
            
        return images_by_color

    def _force_systematic_scroll(self) -> None:
        """
        Realiza un scroll sistemático (mitad > final > inicio) para activar
        la carga de todos los elementos 'lazy-loaded' en la página.
        """
        try:
            self.log("Ejecutando scroll sistemático para forzar carga de imágenes...")
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script(f"window.scrollTo(0, {total_height // 2});")
            time.sleep(0.2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.2)
        except Exception as e:
            self.log(f"Error durante el scroll sistemático: {e}", "warning")

    def _wait_for_image_load(self, img_element: WebElement, max_attempts: int = 10) -> Optional[str]:
        """
        Espera a que una imagen se cargue completamente y devuelve su URL.

        Hace scroll hasta el elemento para asegurar que esté en el viewport, lo que
        activa su carga. Luego, intenta obtener una URL válida repetidamente.

        Args:
            img_element (WebElement): El elemento `<img>` a procesar.
            max_attempts (int): Número máximo de intentos para obtener la URL.

        Returns:
            Optional[str]: La URL de la imagen si se carga correctamente, sino `None`.
        """
        for attempt in range(max_attempts):
            try:
                # Asegura que la imagen esté en el viewport para que se cargue.
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
                time.sleep(0.2)
                
                valid_url = self._get_best_image_url(img_element)
                if valid_url:
                    return valid_url
                
                time.sleep(0.2)
            except Exception as e:
                self.log(f"Intento {attempt + 1} de carga de imagen fallido: {e}", 'debug')
                time.sleep(0.2)
        return None

    def _get_best_image_url(self, element: WebElement) -> Optional[str]:
        """
        Obtiene la mejor URL de imagen de un elemento, priorizando atributos
        de alta resolución o de carga diferida.

        La jerarquía de búsqueda es: `data-srcset`, `srcset`, `data-src`, `src`.

        Args:
            element (WebElement): El elemento `<img>` del cual extraer la URL.

        Returns:
            Optional[str]: La mejor URL encontrada o `None`.
        """
        try:
            for attr in ['data-srcset', 'srcset']:
                srcset = element.get_attribute(attr)
                if srcset:
                    url = self._parse_srcset_url(srcset)
                    if self._is_valid_image_src(url):
                        return url
            
            for attr in ['data-src', 'src']:
                src = element.get_attribute(attr)
                if self._is_valid_image_src(src):
                    return src
        except Exception as e:
            self.log(f"Error al extraer URL de imagen del elemento: {e}", 'debug')
        return None

    def _parse_srcset_url(self, srcset: str) -> Optional[str]:
        """
        Analiza un atributo `srcset` y devuelve la URL de mayor resolución.

        Generalmente, la última URL en la lista `srcset` es la de mayor calidad.
        Si se especifican anchos ('w'), busca la URL con el mayor ancho.

        Args:
            srcset (str): El contenido del atributo `srcset`.

        Returns:
            Optional[str]: La URL de mayor resolución o `None` si hay un error.
        """
        try:
            parts = [part.strip().split() for part in srcset.strip().split(',')]
            if not parts:
                return None

            best_url = parts[-1][0]
            max_width = 0

            if all(len(p) == 2 and p[1].endswith('w') for p in parts):
                for url, width_desc in parts:
                    try:
                        width_num = int(width_desc[:-1])
                        if width_num > max_width:
                            max_width = width_num
                            best_url = url
                    except (ValueError, IndexError):
                        continue
            return best_url
        except Exception as e:
            self.log(f"Error al parsear srcset: '{srcset}'. Error: {e}", 'debug')
            return None

    def _is_valid_image_src(self, src: Optional[str]) -> bool:
        """
        Verifica si una URL de imagen es válida y no un placeholder.

        Filtra URLs vacías, placeholders (imágenes transparentes, de carga, etc.)
        y asegura que la URL pertenezca al dominio de imágenes de Zara.

        Args:
            src (Optional[str]): La URL de la imagen a validar.

        Returns:
            bool: `True` si la URL es válida, `False` en caso contrario.
        """
        if not src or not isinstance(src, str) or not src.strip():
            return False
            
        invalid_patterns = [
            'transparent', 'placeholder', 'loading', 'spinner', 'blank', 'empty',
            'data:image/svg+xml', 'data:image/gif;base64'
        ]
        
        src_lower = src.lower()
        if any(pattern in src_lower for pattern in invalid_patterns):
            return False
        
        # Criterio final: debe ser una URL de imagen de producto real de Zara.
        if 'static.zara.net/photos' in src_lower or 'static.zara.net/assets/public' in src_lower:
            return True
            
        return False

    def _get_current_color_name(self) -> Optional[str]:
        """
        Obtiene el nombre del color actualmente seleccionado en la página.

        Prueba varios selectores definidos en la configuración hasta encontrar
        el nombre del color.

        Returns:
            Optional[str]: El nombre del color como texto, o `None` si no se encuentra.
        """
        for selector in self.PRODUCT_SELECTORS['color_name_selectors']:
            try:
                color_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                color_name = color_element.text.strip()
                if color_name:
                    return color_name
            except Exception:
                continue
        return None