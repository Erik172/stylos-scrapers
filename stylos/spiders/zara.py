from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from fake_useragent import UserAgent
from selenium import webdriver
import time
import re

import scrapy


class ZaraSpider(scrapy.Spider):
    name = "zara"
    allowed_domains = ["zara.com", "www.zara.com", "zara.net", "static.zara.net", "zara.com.co"]
    start_urls = [
        "https://www.zara.com/co/",
    ]
    
    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--blink-settings=imagesEnabled=false") # desactivar imagenes
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.processed_urls = set()
        self.main_window = None  # Para guardar referencia de la ventana principal
    
    def open_new_tab(self, url):
        """Abrir una nueva pestaña con la URL especificada"""
        # Guardar la ventana principal si no está guardada
        if not self.main_window:
            self.main_window = self.driver.current_window_handle
        
        # Abrir nueva pestaña
        self.driver.execute_script("window.open('');")
        
        # Cambiar a la nueva pestaña
        self.driver.switch_to.window(self.driver.window_handles[-1])
        
        # Navegar a la URL
        self.driver.get(url)
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        return self.driver.current_window_handle
    
    def close_current_tab_and_return_to_main(self):
        """Cerrar la pestaña actual y volver a la principal"""
        self.driver.close()
        if self.main_window:
            self.driver.switch_to.window(self.main_window)
        else:
            # Si no hay ventana principal guardada, ir a la primera disponible
            self.driver.switch_to.window(self.driver.window_handles[0])
    
    async def start(self, response=None):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
            )
            
    def parse(self, response):
        """
        ROL: NAVEGADOR DINÁMICO DE MENÚ.
        Abre el menú, hace clic en cada categoría principal, y recolecta
        TODAS las subcategorías que aparecen.
        """
        self.log(f"Iniciando navegación dinámica de menú en: {response.url}")
        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 15)

        try:
            # --- PASO 1: ABRIR EL MENÚ DE HAMBURGUESA ---
            self.log("Buscando botón de hamburguesa...")
            
            # Múltiples selectores para el botón hamburguesa basados en la información proporcionada
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
            self.driver.save_screenshot('error_menu_screenshot.png')
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
        
        all_found_urls = []

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
                            all_found_urls.append(href)
                    
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

        # --- PASO 3: ENVIAR TODAS LAS URLS RECOLECTADAS A SCRAPY ---
        self.log(f"Navegación de menú finalizada. Se recolectaron {len(all_found_urls)} URLs en total.")
        
        # Procesar URLs únicas
        unique_urls = set(all_found_urls)
        self.log(f"URLs únicas después de eliminar duplicados: {len(unique_urls)}")
        
        for url in unique_urls:
            if url not in self.processed_urls:
                self.processed_urls.add(url)
                yield scrapy.Request(url, callback=self.parse_category)
            
    def parse_category(self, response):
        self.log(f"Explorando y enrutando URLs desde: {response.url}")
        self.driver.get(response.url)
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Scroll inteligente
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Buscar productos y procesar directamente sin usar índices
        products_xpath = "//div[contains(@class, 'zds-carousel-item')] | //li[contains(@class, 'products-category-grid-block')]"
        
        # Obtener todos los productos DESPUÉS del scroll para evitar stale elements
        all_products = self.driver.find_elements(By.XPATH, products_xpath)
        self.log(f"Encontrados {len(all_products)} productos en la página.")
        
        # Extraer todas las URLs primero antes de procesarlas
        product_urls = []
        for idx, product in enumerate(all_products):
            try:
                link_elements = product.find_elements(By.XPATH, ".//a[@href]")
                
                if link_elements:
                    href = link_elements[0].get_attribute("href")
                    
                    if href and href not in self.processed_urls:
                        product_urls.append(href)
                        self.processed_urls.add(href)
                        
            except Exception as e:
                self.log(f"Error extrayendo URL del producto índice {idx}: {e}")
                continue
        
        # Ahora procesar las URLs extraídas
        for href in product_urls:
            if re.search(r'-p\d+\.html', href):
                yield scrapy.Request(
                    href,
                    callback=self.parse_product,
                )
            elif re.search(r'-l\d+\.html', href):
                yield scrapy.Request(
                    href,
                    callback=self.parse_category,
                )
            
    def parse_product(self, response):
        """Procesar producto en una nueva pestaña"""
        self.log(f"Procesando producto en nueva pestaña: {response.url}")
        
        try:
            # Abrir producto en nueva pestaña
            product_tab = self.open_new_tab(response.url)
            
            # Scroll inteligente en la nueva pestaña
            # last_height = self.driver.execute_script("return document.body.scrollHeight")
            # while True:
            #     self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            #     time.sleep(2)
            #     new_height = self.driver.execute_script("return document.body.scrollHeight")
            #     if new_height == last_height:
            #         break
            #     last_height = new_height
            time.sleep(1)
            
            # Cerrar pestaña y volver a la principal
            self.close_current_tab_and_return_to_main()
            
        except Exception as e:
            self.log(f"Error procesando producto en nueva pestaña {response.url}: {e}")
            # Intentar volver a la ventana principal en caso de error
            try:
                if self.main_window:
                    self.driver.switch_to.window(self.main_window)
            except:
                pass
        
        # Devolver datos básicos del producto
        yield {
            'url': response.url,
            'type': 'product',
        }
    
    def closed(self, reason):
        """Cerrar driver al finalizar"""
        if hasattr(self, 'driver'):
            self.driver.quit()