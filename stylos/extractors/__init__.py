"""
Sistema de extractors especializados por sitio web.
Cada sitio tiene su propio extractor con lógica específica.
"""

from abc import ABC, abstractmethod
from typing import Optional
from selenium.webdriver.remote.webelement import WebElement
import logging
import time

class BaseExtractor(ABC):
    """
    Clase base abstracta para todos los extractors.
    Define la interfaz común que deben implementar todos los extractors específicos.
    """
    
    def __init__(self, driver, spider):
        self.driver = driver
        self.spider = spider
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract_menu_data(self):
        """Extrae URLs del menú de navegación principal."""
        pass
    
    @abstractmethod
    def extract_category_data(self):
        """Realiza scroll y prepara datos de categoría."""
        pass
    
    @abstractmethod
    def extract_product_data(self):
        """Extrae datos completos del producto incluyendo imágenes por color."""
        pass
    
    # Métodos comunes que pueden ser sobrescritos
    def log(self, message, level='info'):
        """Helper para logging consistente."""
        getattr(self.spider, 'log', print)(message)
        getattr(self.logger, level)(message)
    
    def wait_for_element(self, selector, timeout=15, by_xpath=False):
        """Helper común para esperar elementos."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(self.driver, timeout)
        by = By.XPATH if by_xpath else By.CSS_SELECTOR
        return wait.until(EC.presence_of_element_located((by, selector)))
    
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
        y valida que sea una URL de imagen real de producto.

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
        
        # Validar que sea una URL válida (protocolo http/https)
        if not (src_lower.startswith('http://') or src_lower.startswith('https://')):
            return False
        
        # Validar que contenga extensiones de imagen comunes
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg']
        if any(ext in src_lower for ext in image_extensions):
            return True
            
        # Validar que contenga patrones típicos de URLs de imágenes de productos
        product_image_patterns = [
            '/photos/', '/images/', '/img/', '/assets/', '/static/',
            '/product/', '/items/', '/catalog/', '/media/'
        ]
        
        return any(pattern in src_lower for pattern in product_image_patterns)
    
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
                time.sleep(0.1)
                
                valid_url = self._get_best_image_url(img_element)
                if valid_url:
                    return valid_url
            except Exception as e:
                self.log(f"Intento {attempt + 1} de carga de imagen fallido: {e}", 'debug')
                time.sleep(0.2)
        return None


class ExtractorRegistry:
    """
    Registry para mapear spiders a sus extractors correspondientes.
    """
    _extractors = {}
    
    @classmethod
    def register(cls, spider_name, extractor_class):
        """Registra un extractor para un spider específico."""
        cls._extractors[spider_name] = extractor_class
    
    @classmethod
    def get_extractor(cls, spider_name, driver, spider):
        """Obtiene el extractor apropiado para un spider."""
        extractor_class = cls._extractors.get(spider_name)
        if not extractor_class:
            raise ValueError(f"No hay extractor registrado para el spider '{spider_name}'")
        return extractor_class(driver, spider)
    
    @classmethod
    def list_registered(cls):
        """Lista todos los extractors registrados."""
        return list(cls._extractors.keys())


def register_extractor(spider_name):
    """
    Decorador para registrar automáticamente extractors.
    
    Uso:
    @register_extractor('zara')
    class ZaraExtractor(BaseExtractor):
        ...
    """
    def decorator(extractor_class):
        ExtractorRegistry.register(spider_name, extractor_class)
        return extractor_class
    return decorator 