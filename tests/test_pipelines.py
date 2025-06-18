"""
Suite de pruebas unitarias para las pipelines del proyecto Scrapy 'stylos'.

Este módulo contiene pruebas para todas las pipelines definidas en 'stylos.pipelines.py'.
Se utiliza el framework 'pytest' para la ejecución y aserciones.

Técnicas y librerías clave utilizadas:
- Pytest: Framework principal para estructurar y ejecutar las pruebas.
- Fixtures de Pytest: Para crear objetos reutilizables (spiders, items) y mantener
  las pruebas limpias y centradas en su lógica (patrón D.R.Y.).
- unittest.mock.patch: Para interceptar y simular (`mock`) el cliente de `pymongo`,
  aislando las pruebas de una base de datos real.
- mongomock: Proporciona una implementación en memoria de un cliente de MongoDB,
  ideal para pruebas rápidas y fiables de la lógica de la base de datos.
- pytest-monkeypatch: Para modificar clases o funciones en tiempo de ejecución,
  usado aquí para simular la función externa `normalize_price`.
"""

import pytest
from unittest.mock import MagicMock, patch
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
import mongomock  # Para simular la conexión a MongoDB
from scrapy import Item, Field

# Importación de las pipelines a probar
from stylos.pipelines import (
    PricePipeline,
    MongoDBPipeline,
    HistoryPipeline,
    DuplicatesPipeline,
    StylosPipeline,
)

# --- Fixtures de Pytest: Preparación de datos y objetos reutilizables ---

@pytest.fixture
def mock_spider():
    """
    Crea un objeto simulado (mock) de un Spider de Scrapy.

    Este fixture es crucial porque las pipelines interactúan con el spider para
    acceder al logger y, más importante, a la configuración (`settings`).
    Simulamos los settings que el método `from_crawler` de las pipelines necesita
    para instanciarse correctamente.
    """
    spider = MagicMock()
    spider.logger = MagicMock()
    spider.settings = {
        "MONGO_URI": "mongodb://localhost:27017/",
        "MONGO_DATABASE": "test_db",
        "MONGO_COLLECTION": "test_products",
        "MONGO_HISTORY_COLLECTION": "test_history",
        "MONGO_USERNAME": "user",
        "MONGO_PASSWORD": "password",
        "MONGO_AUTH_SOURCE": "admin"
    }
    return spider

@pytest.fixture
def sample_item_class():
    """
    Define y retorna una clase de Item de Scrapy para usar como plantilla.

    Tener una clase definida asegura que todos los campos existen, evitando
    KeyErrors en las pruebas y permitiendo instanciar un item limpio para cada test.
    """
    class ProductItem(Item):
        # --- Campos de entrada del Spider ---
        original_price = Field()
        current_price = Field()
        url = Field()
        name = Field()
        description = Field()
        images_by_color = Field()
        datetime = Field()
        last_visited = Field()

        # --- Campos generados por las Pipelines ---
        original_price_amount = Field()
        current_price_amount = Field()
        currency = Field()
        has_discount = Field()
        discount_amount = Field()
        discount_percentage = Field()
        
        # --- Metadatos para comunicación entre pipelines ---
        changes_detected = Field()
        changes_list = Field()

    return ProductItem


# --- Suite de Pruebas para PricePipeline ---

class TestPricePipeline:
    """Pruebas para la pipeline que normaliza precios y calcula descuentos."""

    def test_calculates_discount_correctly(self, monkeypatch, sample_item_class):
        """
        Verifica que la pipeline calcula correctamente los campos de descuento
        cuando el precio actual es menor que el original.
        """
        # Arrange: Preparar el entorno de la prueba
        pipeline = PricePipeline()
        item = sample_item_class()
        item['original_price'] = "$ 200.000"
        item['current_price'] = "COP 150.000"

        # Se simula la función `normalize_price` para aislar la lógica de la pipeline
        # de la lógica de su dependencia.
        def mock_normalize_price(price_text):
            if "200.000" in price_text:
                return {'amount': 200000.0, 'currency': 'COP'}
            return {'amount': 150000.0, 'currency': 'COP'}
        monkeypatch.setattr('stylos.pipelines.normalize_price', mock_normalize_price)

        # Act: Ejecutar la acción que se está probando
        processed_item = pipeline.process_item(item, None)
        adapter = ItemAdapter(processed_item)

        # Assert: Verificar que los resultados son los esperados
        assert adapter['original_price_amount'] == 200000.0
        assert adapter['current_price_amount'] == 150000.0
        assert adapter['currency'] == 'COP'
        assert adapter['has_discount'] is True
        assert adapter['discount_amount'] == 50000.0
        assert adapter['discount_percentage'] == 25

    def test_handles_items_without_discount(self, monkeypatch, sample_item_class):
        """
        Verifica que la pipeline asigna valores por defecto para el descuento
        cuando no hay un precio original o no hay rebaja.
        """
        # Arrange
        pipeline = PricePipeline()
        item = sample_item_class()
        item['current_price'] = "100.00"

        # Simular que normalize_price siempre devuelve el mismo valor
        monkeypatch.setattr('stylos.pipelines.normalize_price', lambda text: {'amount': 100.0, 'currency': 'USD'})

        # Act
        processed_item = pipeline.process_item(item, None)
        adapter = ItemAdapter(processed_item)

        # Assert
        assert adapter['current_price_amount'] == 100.0
        assert adapter.get('original_price_amount') is None
        assert adapter['has_discount'] is False
        assert adapter['discount_amount'] == 0
        assert adapter['discount_percentage'] == 0


# --- Suite de Pruebas para DuplicatesPipeline ---

class TestDuplicatesPipeline:
    """Pruebas para la pipeline que filtra items duplicados por URL en una misma ejecución."""

    def test_filters_duplicate_urls(self):
        """
        Verifica que la pipeline deja pasar el primer item con una URL dada,
        pero descarta los siguientes con la misma URL.
        """
        # Arrange
        pipeline = DuplicatesPipeline()
        item1 = {'url': 'http://example.com/product1'}
        item2 = {'url': 'http://example.com/product2'}
        item3_duplicate = {'url': 'http://example.com/product1'}

        # Act & Assert
        # El primer item con una URL única debe pasar
        result1 = pipeline.process_item(item1, None)
        assert result1 == item1

        # Un segundo item con una URL diferente también debe pasar
        result2 = pipeline.process_item(item2, None)
        assert result2 == item2

        # Un tercer item con una URL ya vista debe ser descartado (lanzar DropItem)
        with pytest.raises(DropItem, match="Item duplicado encontrado"):
            pipeline.process_item(item3_duplicate, None)


# --- Suite de Pruebas para la Interacción con MongoDB ---

@patch('stylos.pipelines.pymongo.MongoClient', new=mongomock.MongoClient)
class TestMongoDBInteraction:
    """Pruebas para las pipelines que interactúan con MongoDB (MongoDBPipeline, HistoryPipeline)."""

    def test_mongodb_pipeline_inserts_new_item(self, mock_spider, sample_item_class):
        """
        Verifica que un producto que no existe en la base de datos es insertado correctamente.
        """
        # Arrange: Preparar la pipeline y el item a procesar
        pipeline = MongoDBPipeline.from_crawler(mock_spider)
        pipeline.open_spider(mock_spider)  # Establece la conexión con la DB simulada
        item = sample_item_class(url='http://new-item.com', name='Nuevo Producto')

        # Act: Procesar el item a través de la pipeline
        pipeline.process_item(item, mock_spider)

        # Assert: Verificar directamente en la base de datos simulada
        db = pipeline.client[mock_spider.settings['MONGO_DATABASE']]
        collection = db[mock_spider.settings['MONGO_COLLECTION']]
        saved_item = collection.find_one({'url': 'http://new-item.com'})

        assert saved_item is not None
        assert saved_item['name'] == 'Nuevo Producto'
        pipeline.close_spider(mock_spider)

    def test_mongodb_pipeline_updates_existing_item(self, mock_spider, sample_item_class):
        """
        Verifica que un producto existente es actualizado si se detectan cambios.
        """
        # Arrange
        pipeline = MongoDBPipeline.from_crawler(mock_spider)
        pipeline.open_spider(mock_spider)
        # 1. Pre-poblar la DB simulada con un producto existente
        collection = pipeline.collection
        collection.insert_one({'_id': '123', 'url': 'http://existing.com', 'name': 'Viejo Nombre', 'current_price_amount': 100})
        # 2. Crear el nuevo item con datos modificados
        item = sample_item_class(url='http://existing.com', name='Nombre Actualizado', current_price_amount=120)

        # Act
        processed_item = pipeline.process_item(item, mock_spider)

        # Assert
        # 1. Verificar que el documento en la DB simulada fue actualizado
        saved_item = collection.find_one({'url': 'http://existing.com'})
        assert saved_item['name'] == 'Nombre Actualizado'
        assert saved_item['current_price_amount'] == 120
        # 2. Verificar que el item procesado contiene los metadatos de los cambios
        adapter = ItemAdapter(processed_item)
        assert adapter['changes_detected'] is True
        assert len(adapter['changes_list']) > 0

        pipeline.close_spider(mock_spider)

    def test_history_pipeline_creates_record_on_change(self, mock_spider, sample_item_class):
        """
        Verifica que HistoryPipeline crea un registro de auditoría cuando un item
        ha sido marcado con `changes_detected = True`.
        """
        # Arrange
        pipeline = HistoryPipeline.from_crawler(mock_spider)
        pipeline.open_spider(mock_spider)
        item = sample_item_class(
            url='http://changed-item.com',
            changes_detected=True,
            changes_list=["Campo 'name' cambió"],
            datetime='2025-06-18'
        )

        # Act
        pipeline.process_item(item, mock_spider)

        # Assert    
        history_collection = pipeline.db[mock_spider.settings['MONGO_HISTORY_COLLECTION']]
        history_record = history_collection.find_one({'product_url': 'http://changed-item.com'})

        assert history_record is not None
        assert "Campo 'name' cambió" in history_record['changes']
        pipeline.close_spider(mock_spider)

    def test_history_pipeline_skips_unchanged_item(self, mock_spider, sample_item_class):
        """
        Verifica que HistoryPipeline ignora los items que no tienen cambios
        (es decir, `changes_detected` es False o no existe).
        """
        # Arrange
        pipeline = HistoryPipeline.from_crawler(mock_spider)
        pipeline.open_spider(mock_spider)
        item = sample_item_class(url='http://unchanged-item.com', changes_detected=False)

        # Act
        pipeline.process_item(item, mock_spider)

        # Assert
        history_collection = pipeline.db[mock_spider.settings['MONGO_HISTORY_COLLECTION']]
        history_record = history_collection.find_one({'product_url': 'http://unchanged-item.com'})

        assert history_record is None  # No se debe haber guardado nada
        pipeline.close_spider(mock_spider)


# --- Suite de Pruebas para Pipelines Auxiliares ---

class TestAuxiliaryPipelines:
    """Pruebas para pipelines de plantilla o de propósito general."""

    def test_stylos_pipeline_passthrough(self):
        """Verifica que la pipeline de plantilla simplemente retorna el item sin modificarlo."""
        # Arrange
        pipeline = StylosPipeline()
        item = {"data": 123}

        # Act & Assert
        assert pipeline.process_item(item, None) == item