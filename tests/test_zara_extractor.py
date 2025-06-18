"""
Suite de pruebas unitarias para la clase ZaraExtractor.

Este módulo prueba la lógica de extracción específica de Zara en aislamiento,
sin necesidad de una conexión de red o un navegador real. La estrategia
principal es simular ("mock") el objeto `driver` de Selenium para controlar
exactamente lo que el extractor "ve" y verificar cómo reacciona.

Las pruebas están organizadas de "abajo hacia arriba":
1.  Se prueban los métodos de utilidad más simples (que procesan texto).
2.  Se prueban los métodos que leen datos simples del `driver`.
3.  Se prueban los métodos que realizan interacciones complejas (scrolls, clics).
4.  Se prueban los métodos públicos que orquestan a los demás.
"""

import pytest
import time
from unittest.mock import MagicMock, PropertyMock, patch
from pathlib import Path

# Importa la clase que vamos a probar
from stylos.extractors.zara_extractor import ZaraExtractor

# --- Fixtures de Pytest: Nuestros "Ingredientes" para las Pruebas ---

@pytest.fixture
def mock_spider():
    """Crea un mock simple de un Spider para satisfacer el constructor del extractor."""
    spider = MagicMock()
    # Simula el método de log para que no falle si se llama
    spider.log = MagicMock()
    return spider

@pytest.fixture
def zara_pdp_html():
    """Carga el contenido del archivo HTML de una página de producto guardada localmente."""
    try:
        html_path = Path(__file__).parent.parent / 'tests/samples/zara_pdp.html'
        return html_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        pytest.fail("Asegúrate de tener el archivo 'zara_pdp.html' en la carpeta 'tests/samples/'")

@pytest.fixture
def mock_driver():
    """
    Crea un mock genérico del driver de Selenium.
    Este mock se configurará de forma específica en cada prueba.
    """
    driver = MagicMock()
    # Las funciones de Selenium a menudo devuelven el driver (ej. para encadenar)
    driver.execute_script.return_value = driver
    return driver


# --- Pruebas para los Métodos de Utilidad (El Nivel Más Bajo) ---

class TestZaraExtractorUtils:
    """Prueba los métodos auxiliares que no dependen (o casi no) del driver."""
    
    # Instanciamos una vez, ya que estos métodos no usan el estado del driver
    extractor = ZaraExtractor(driver=None, spider=MagicMock())

    def test_is_valid_image_src(self):
        """Verifica que la lógica de validación de URLs de imágenes es correcta."""
        # Casos válidos
        assert self.extractor._is_valid_image_src("https://static.zara.net/photos/a.jpg") is True
        assert self.extractor._is_valid_image_src("https://static.zara.net/assets/public/b.jpg") is True
        
        # Casos inválidos
        assert self.extractor._is_valid_image_src(None) is False
        assert self.extractor._is_valid_image_src("") is False
        assert self.extractor._is_valid_image_src("https://example.com/image.jpg") is False
        assert self.extractor._is_valid_image_src("data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=") is False
        assert self.extractor._is_valid_image_src("/assets/images/placeholder.png") is False

    def test_parse_srcset_url(self):
        """Verifica que se extrae la URL de mayor resolución de un atributo srcset."""
        srcset = "//a.jpg 320w, //b.jpg 720w, //c.jpg 1080w"
        assert self.extractor._parse_srcset_url(srcset) == "//c.jpg"
        
        srcset_simple = "//a.jpg, //b.jpg"
        assert self.extractor._parse_srcset_url(srcset_simple) == "//b.jpg"
        
        assert self.extractor._parse_srcset_url("") is None


# --- Pruebas para Extracción de Datos Simples ---

class TestZaraSimpleDataExtraction:
    """Prueba métodos que leen datos del `driver` sin realizar acciones complejas."""

    def test_extract_basic_product_info(self, mock_driver, mock_spider, zara_pdp_html, monkeypatch):
        """
        Verifica que la información básica del producto se extrae correctamente.
        La clave es configurar el `mock_driver` para que devuelva elementos simulados.
        """
        # Arrange
        # 1. Hacer que el driver "vea" nuestro HTML local
        type(mock_driver).page_source = PropertyMock(return_value=zara_pdp_html)
        
        # 2. Simular los WebElements que find_elements devolvería
        mock_name_element = MagicMock()
        mock_name_element.text = "CAMISA OVERSIZE"
        
        mock_price_element_1 = MagicMock()
        mock_price_element_1.text = "$ 259.900"
        mock_price_element_2 = MagicMock()
        mock_price_element_2.text = "$ 159.900"
        
        mock_desc_element = MagicMock()
        mock_desc_element.text = "Cuello solapa."

        # 3. Configurar el comportamiento de find_element(s)
        mock_driver.find_element.return_value = mock_name_element
        mock_driver.find_elements.side_effect = [
            [mock_price_element_1, mock_price_element_2], # La primera vez que se llame, devuelve precios
            [mock_desc_element]                            # La segunda vez, devuelve descripción
        ]
        
        extractor = ZaraExtractor(driver=mock_driver, spider=mock_spider)
        
        # 4. Aislamos la prueba: mockeamos el método auxiliar _get_current_color_name
        monkeypatch.setattr(extractor, '_get_current_color_name', lambda: "BLANCO ROTO")

        # Act
        product_data = extractor._extract_basic_product_info()
        
        # Assert
        assert product_data['name'] == "CAMISA OVERSIZE"
        assert product_data['prices'] == ["$ 259.900", "$ 159.900"]
        assert product_data['description'] == "Cuello solapa."
        assert product_data['current_color'] == "BLANCO ROTO"

# --- Pruebas para Métodos de Interacción ---

# En la clase TestZaraInteraction

# El decorador se elimina de la clase
class TestZaraInteraction:
    """Prueba métodos que interactúan con la página (scroll, clics)."""

    @patch('time.sleep', return_value=None)
    def test_extract_category_data_stops_scrolling(self, mock_sleep, mock_driver, mock_spider):
        """
        Verifica que el bucle de scroll infinito se detiene cuando la altura de la página
        deja de cambiar.
        """
        # Arrange
        # La lógica interna no cambia, sigue siendo correcta.
        mock_driver.execute_script.side_effect = [
            1000,  # 1. Altura inicial para last_height
            None,  # 2. Resultado de scrollTo en el 1er bucle
            2000,  # 3. Altura para new_height en el 1er bucle
            None,  # 4. Resultado de scrollTo en el 2do bucle
            2500,  # 5. Altura para new_height en el 2do bucle
            None,  # 6. Resultado de scrollTo en el 3er bucle
            2500   # 7. Altura para new_height en el 3er bucle (aquí se detiene)
        ]
        extractor = ZaraExtractor(driver=mock_driver, spider=mock_spider)

        # Act
        result = extractor.extract_category_data()
        
        # Assert
        assert mock_driver.execute_script.call_count == 7
        assert result['scroll_completed'] is True
        assert result['scroll_attempts'] == 2

        # Afirmación adicional: podemos verificar que time.sleep fue llamado
        # (ya que ahora tenemos el mock_sleep como argumento)
        assert mock_sleep.called is True
        assert mock_sleep.call_count == 3

# --- Pruebas para los Métodos Públicos (Orquestadores) ---

class TestZaraPublicAPI:
    """
    Prueba los métodos públicos del extractor, mockeando sus dependencias
    internas (los métodos auxiliares) para probar solo la lógica de orquestación.
    """

    def test_extract_product_data_orchestrates_calls(self, mock_driver, mock_spider, monkeypatch):
        """
        Verifica que `extract_product_data` llama a sus métodos auxiliares
        y combina sus resultados correctamente.
        """
        # Arrange
        extractor = ZaraExtractor(driver=mock_driver, spider=mock_spider)
        
        # 1. Definir los datos falsos que devolverán los métodos auxiliares
        fake_basic_info = {'name': 'Producto Test', 'prices': ['$100']}
        fake_images = {'AZUL': [{'src': 'test.jpg', 'alt': 'test'}]}

        # 2. Usar monkeypatch para reemplazar los métodos reales por funciones lambda
        # que devuelven nuestros datos falsos.
        monkeypatch.setattr(extractor, '_extract_basic_product_info', lambda: fake_basic_info)
        monkeypatch.setattr(extractor, '_extract_images_by_color', lambda: fake_images)
        
        # Mockeamos el wait.until para que no falle
        with patch('selenium.webdriver.support.ui.WebDriverWait') as mock_wait:
            # Act
            result = extractor.extract_product_data()

        # Assert
        # Verificamos que el resultado final es la combinación correcta de los datos falsos
        assert 'product_data' in result
        assert 'extracted_images' in result
        assert result['product_data']['name'] == 'Producto Test'
        assert result['extracted_images']['AZUL'][0]['src'] == 'test.jpg'