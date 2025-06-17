"""
Sistema de extractors especializados por sitio web.
Cada sitio tiene su propio extractor con lógica específica.
"""

from abc import ABC, abstractmethod
import logging

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
    def extract_menu_urls(self):
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