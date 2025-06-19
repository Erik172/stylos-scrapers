# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from itemadapter import ItemAdapter
from scrapy import Item, Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem
from typing import Dict, Any, List
from stylos.processors import normalize_price

class PricePipeline:
    """
    Pipeline para procesar y enriquecer los datos de precios de un item.
    
    Esta pipeline debe ejecutarse ANTES de las pipelines de base de datos.
    Procesa la lista raw_prices y determina precio original vs actual.
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # --- Procesamiento de Lista de Precios ---
        raw_prices = adapter.get('raw_prices', [])
        currency = adapter.get('currency', None)
        
        if raw_prices:
            price_info = self._process_price_list(raw_prices)
            
            # Asignar precio original y actual
            adapter['original_price'] = price_info['original_price']
            adapter['current_price'] = price_info['current_price']
            adapter['has_discount'] = price_info['has_discount']
        else:
            # Si no hay precios, usar valores por defecto
            adapter['original_price'] = None
            adapter['current_price'] = None
            adapter['has_discount'] = False
        
        # --- Normalización de Precios ---
        original_price_text = adapter.get('original_price')
        current_price_text = adapter.get('current_price')
        
        if original_price_text:
            price_data = normalize_price(original_price_text, currency)
            adapter['original_price'] = price_data['amount']
            adapter['currency'] = price_data['currency'] # Asigna la moneda del precio original
            
        if current_price_text:
            price_data = normalize_price(current_price_text, currency)
            adapter['current_price'] = price_data['amount']
            if not adapter.get('currency'):
                adapter['currency'] = price_data['currency'] # Si no había moneda, usa la del precio actual

        # --- Cálculo de Descuentos ---
        opa = adapter.get('original_price')
        cpa = adapter.get('current_price')

        if opa is not None and cpa is not None and opa > cpa:
            adapter['has_discount'] = True
            adapter['discount_amount'] = round(opa - cpa, 2)
            adapter['discount_percentage'] = round(((opa - cpa) / opa) * 100)
        else:
            adapter['has_discount'] = False
            adapter['discount_amount'] = 0
            adapter['discount_percentage'] = 0
            
        return item
    
    def _process_price_list(self, prices):
        """
        Procesa lista de precios y determina cuál es original y cuál es actual.
        Lógica: Si hay múltiples precios, el mayor es original y el menor es actual.
        """
        price_info = {
            'original_price': None,
            'current_price': None,
            'has_discount': False
        }
        
        if not prices:
            return price_info
            
        if len(prices) == 1:
            # Un solo precio - sin descuento
            price_info['original_price'] = prices[0]
            price_info['current_price'] = prices[0]
            price_info['has_discount'] = False
            
        elif len(prices) >= 2:
            # Múltiples precios - determinar por valor numérico
            normalized_prices = []
            for price_text in prices:
                norm = normalize_price(price_text)
                if norm['amount'] is not None:
                    normalized_prices.append((price_text, norm['amount']))
            
            if len(normalized_prices) >= 2:
                # Ordenar por monto (mayor a menor)
                normalized_prices.sort(key=lambda x: x[1], reverse=True)
                
                price_info['original_price'] = normalized_prices[0][0]  # Mayor precio (original)
                price_info['current_price'] = normalized_prices[1][0]   # Menor precio (actual)
                price_info['has_discount'] = True
            else:
                # Fallback: si no se pudieron normalizar, usar el primero
                price_info['original_price'] = prices[0]
                price_info['current_price'] = prices[0]
                price_info['has_discount'] = False
        
        return price_info

# --- CLASE BASE PARA LA CONEXIÓN A MONGODB ---

class MongoPipelineBase:
    """
    Clase base abstracta para gestionar una conexión a MongoDB.

    Esta clase implementa el patrón de diseño "Template Method". Centraliza la
    lógica común y reutilizable para la conexión a la base de datos (autenticación,
    apertura y cierre de la conexión), permitiendo que las clases hijas solo se

    enfoquen en su lógica específica de procesamiento de items.

    No está diseñada para ser instanciada directamente, sino para ser heredada.
    """

    def __init__(self, mongo_uri: str, mongo_db: str, mongo_username: str, mongo_password: str, mongo_auth_source: str):
        """
        Inicializa la pipeline con los parámetros de conexión.

        Este método es llamado por `from_crawler` con los valores de `settings.py`.
        """
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_username = mongo_username
        self.mongo_password = mongo_password
        self.mongo_auth_source = mongo_auth_source
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> 'MongoPipelineBase':
        """
        Punto de entrada de Scrapy para crear una instancia de la pipeline.

        Este método de clase lee la configuración de la base de datos desde el
        archivo `settings.py` del proyecto y la utiliza para instanciar la clase.

        Args:
            crawler: La instancia del Crawler, que contiene la configuración global.

        Returns:
            Una nueva instancia de la pipeline.
        """
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE"),
            mongo_username=crawler.settings.get("MONGO_USERNAME"),
            mongo_password=crawler.settings.get("MONGO_PASSWORD"),
            mongo_auth_source=crawler.settings.get("MONGO_AUTH_SOURCE", "admin")
        )

    def open_spider(self, spider: Spider) -> None:
        """
        Se ejecuta cuando la araña se abre. Establece la conexión con MongoDB.

        Crea el cliente de MongoDB, verifica la conexión con un 'ping' al servidor
        y selecciona la base de datos. Si la conexión falla, lanza una excepción
        para detener el proceso.

        Args:
            spider: La instancia de la araña que se está ejecutando.
        """
        spider.logger.info(f"Conectando pipeline '{self.__class__.__name__}' a MongoDB...")
        try:
            self.client = pymongo.MongoClient(
                self.mongo_uri,
                username=self.mongo_username,
                password=self.mongo_password,
                authSource=self.mongo_auth_source,
                serverSelectionTimeoutMS=5000  # Timeout para evitar bloqueos
            )
            # Verificar la conexión de forma temprana
            self.client.admin.command('ping')
            self.db = self.client[self.mongo_db]
            spider.logger.info(f"✅ Conexión a MongoDB exitosa. Base de datos: '{self.mongo_db}'")
        except Exception as e:
            spider.logger.error(f"❌ Error crítico conectando a MongoDB: {e}")
            # Elevar la excepción detiene el rastreo si la DB no está disponible
            raise

    def close_spider(self, spider: Spider) -> None:
        """
        Se ejecuta cuando la araña se cierra. Cierra la conexión a MongoDB.

        Args:
            spider: La instancia de la araña que se está ejecutando.
        """
        if self.client:
            self.client.close()
            spider.logger.info("Conexión a MongoDB cerrada correctamente.")

# --- PIPELINES PRINCIPALES ---

class MongoDBPipeline(MongoPipelineBase):
    """
    Pipeline principal para persistir los datos de productos.

    Esta pipeline se encarga de:
    1. Buscar si un producto ya existe en la base de datos usando su URL.
    2. Si existe, detectar si ha habido cambios en campos importantes.
    3. Si no hay cambios, solo actualiza la fecha de última visita.
    4. Si hay cambios, actualiza el documento completo.
    5. Si no existe, lo inserta como un nuevo documento.
    6. Añade metadatos al `item` para que pipelines posteriores (como HistoryPipeline)
       puedan actuar en consecuencia.
    """

    def open_spider(self, spider: Spider) -> None:
        """
        Extiende el método base para configurar la colección específica de productos.
        """
        super().open_spider(spider)  # Llama al método de la clase base para conectar
        collection_name = spider.settings.get("MONGO_COLLECTION", "products")
        self.collection = self.db[collection_name]
        spider.logger.info(f"Pipeline principal configurada para usar la colección: '{collection_name}'")

    def process_item(self, item: Item, spider: Spider) -> Item:
        """
        Procesa, compara y guarda cada item en la colección principal.

        Args:
            item: El item scrapeado por la araña.
            spider: La instancia de la araña.

        Returns:
            El item, para que pueda ser procesado por las siguientes pipelines en la cadena.

        Raises:
            DropItem: Si ocurre un error irrecuperable al interactuar con la base de datos.
        """
        adapter = ItemAdapter(item)
        item_dict = adapter.asdict()

        try:
            existing_item = self.collection.find_one({'url': item_dict['url']})

            if existing_item:
                changes_list = self._detect_changes(existing_item, item_dict)
                if changes_list:
                    # Actualiza el documento completo si se detectan cambios
                    self.collection.update_one({'_id': existing_item['_id']}, {'$set': item_dict})
                    spider.logger.info(f"✅ Producto actualizado (cambios detectados): {item_dict['url']}")
                    # Añade metadatos para la pipeline de historial
                    adapter['changes_detected'] = True
                    adapter['changes_list'] = changes_list
                else:
                    # Actualiza solo la fecha de visita si no hay cambios
                    self.collection.update_one({'_id': existing_item['_id']}, {'$set': {'last_visited': item_dict['last_visited']}})
                    adapter['changes_detected'] = False
            else:
                # Inserta un nuevo documento si el producto no existe
                self.collection.insert_one(item_dict)
                spider.logger.info(f"🆕 Producto nuevo guardado: {item_dict['url']}")

        except Exception as e:
            spider.logger.error(f"❌ Error en MongoDBPipeline para {item_dict.get('url')}: {e}")
            raise DropItem(f"Error en MongoDBPipeline, descartando item.")
        
        return item

    def _detect_changes(self, existing_item: Dict[str, Any], new_item: Dict[str, Any]) -> List[str]:
        """
        Compara un item existente con uno nuevo para detectar cambios significativos.

        Args:
            existing_item: El documento actual en la base de datos.
            new_item: El item recién scrapeado.

        Returns:
            Una lista de strings describiendo los cambios, o una lista vacía si no hay cambios.
        """
        # Campos clave a monitorizar para detectar cambios.
        important_fields = [
            'name', 'description', 'original_price_amount', 'current_price_amount',
            'currency', 'has_discount', 'images_by_color'
        ]
        changes_detected = []
        for field in important_fields:
            if existing_item.get(field) != new_item.get(field):
                change_detail = f"Campo '{field}' cambió de '{existing_item.get(field)}' a '{new_item.get(field)}'"
                changes_detected.append(change_detail)

        return changes_detected


class HistoryPipeline(MongoPipelineBase):
    """
    Crea un registro de auditoría para cada producto que ha sido modificado.

    Esta pipeline depende de los metadatos ('changes_detected', 'changes_list')
    añadidos por `MongoDBPipeline`. Por lo tanto, DEBE ejecutarse DESPUÉS
    de `MongoDBPipeline` en la configuración de `ITEM_PIPELINES`.
    """
    def open_spider(self, spider: Spider) -> None:
        """Extiende el método base para configurar la colección de historial."""
        super().open_spider(spider)
        collection_name = spider.settings.get("MONGO_HISTORY_COLLECTION", "product_history")
        self.collection = self.db[collection_name]
        spider.logger.info(f"Pipeline de historial configurada para usar la colección: '{collection_name}'")

    def process_item(self, item: Item, spider: Spider) -> Item:
        """Si el item fue modificado, crea y guarda un registro de historial."""
        adapter = ItemAdapter(item)
        if adapter.get('changes_detected'):
            try:
                history_record = {
                    'product_url': adapter.get('url'),
                    'change_date': adapter.get('datetime'),
                    'changes': adapter.get('changes_list', []),
                    'full_item_snapshot': adapter.asdict(),
                }
                self.collection.insert_one(history_record)
                spider.logger.info(f"📋 Registro histórico guardado para: {adapter.get('url')}")
            except Exception as e:
                spider.logger.error(f"❌ Error guardando historial para {adapter.get('url')}: {e}")
        
        return item

# --- PIPELINES AUXILIARES ---

class DuplicatesPipeline:
    """
    Filtra items duplicados por URL dentro de la misma ejecución de la araña.

    Utiliza un set en memoria para llevar un registro de las URLs visitadas.
    Nota: Este filtro se reinicia en cada ejecución de la araña. No previene
    duplicados entre ejecuciones diferentes. Para eso, la lógica de
    `MongoDBPipeline` que busca el item en la DB es la responsable.
    """
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item: Item, spider: Spider) -> Item:
        adapter = ItemAdapter(item)
        url = adapter.get('url')
        if not url:
            # Si un item no tiene URL, no se puede verificar. Se deja pasar.
            return item
        if url in self.urls_seen:
            raise DropItem(f"Item duplicado encontrado en esta ejecución: {url}")
        else:
            self.urls_seen.add(url)
            return item

class StylosPipeline:
    """
    Pipeline de plantilla o marcador de posición.

    En su estado actual, no realiza ninguna acción. Puede ser utilizada como
    base para futuras pipelines o eliminada si no es necesaria.
    """
    def process_item(self, item, spider):
        return item