# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
import logging

class StylosPipeline:
    def process_item(self, item, spider):
        return item

class MongoDBPipeline:
    """
    Pipeline para almacenar items en MongoDB con autenticación
    """
    
    def __init__(self, mongo_uri, mongo_db, mongo_collection, mongo_username=None, mongo_password=None, mongo_auth_source=None):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db 
        self.mongo_collection = mongo_collection
        self.mongo_username = mongo_username
        self.mongo_password = mongo_password
        self.mongo_auth_source = mongo_auth_source
        
    @classmethod
    def from_crawler(cls, crawler):
        """
        Método para obtener configuración desde settings.py
        """
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE"),
            mongo_collection=crawler.settings.get("MONGO_COLLECTION"),
            mongo_username=crawler.settings.get("MONGO_USERNAME"),
            mongo_password=crawler.settings.get("MONGO_PASSWORD"),
            mongo_auth_source=crawler.settings.get("MONGO_AUTH_SOURCE")
        )
    
    def open_spider(self, spider):
        """
        Se ejecuta cuando inicia el spider
        """
        try:
            # Verificar si hay credenciales de autenticación
            if self.mongo_username and self.mongo_password:
                # Opción 1: URI con credenciales
                if not self.mongo_username in self.mongo_uri:
                    # Construir URI con credenciales
                    uri_parts = self.mongo_uri.split('://')
                    auth_uri = f"{uri_parts[0]}://{self.mongo_username}:{self.mongo_password}@{uri_parts[1]}"
                    if self.mongo_auth_source:
                        auth_uri += f"?authSource={self.mongo_auth_source}"
                    
                    self.client = pymongo.MongoClient(auth_uri)
                else:
                    # URI ya tiene credenciales
                    self.client = pymongo.MongoClient(self.mongo_uri)
                
                spider.logger.info(f"Conectando a MongoDB con autenticación: usuario={self.mongo_username}")
            else:
                # Sin autenticación
                self.client = pymongo.MongoClient(self.mongo_uri)
                spider.logger.info("Conectando a MongoDB sin autenticación")
            
            # Verificar conexión
            self.client.admin.command('ping')
            
            # Configurar base de datos y colección
            self.db = self.client[self.mongo_db]
            self.collection = self.db[self.mongo_collection]
            
            spider.logger.info(f"✅ Conectado exitosamente a MongoDB: {self.mongo_db}.{self.mongo_collection}")
            
        except Exception as e:
            spider.logger.error(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    def close_spider(self, spider):
        """
        Se ejecuta cuando termina el spider
        """
        self.client.close()
        spider.logger.info("Conexión a MongoDB cerrada")
    
    def process_item(self, item, spider):
        """
        Procesa cada item y lo guarda en MongoDB con detección de cambios
        """
        try:
            # Convertir item a diccionario
            item_dict = ItemAdapter(item).asdict()
            
            # Procesar imágenes por color para MongoDB
            if 'images_by_color' in item_dict:
                processed_images = []
                for color_data in item_dict['images_by_color']:
                    color_info = {
                        'color': color_data['color'],
                        'images': []
                    }
                    
                    # Convertir cada ImagenItem a diccionario
                    for img_item in color_data['images']:
                        img_dict = ItemAdapter(img_item).asdict()
                        color_info['images'].append(img_dict)
                    
                    processed_images.append(color_info)
                
                item_dict['images_by_color'] = processed_images
            
            # Verificar si el producto ya existe (por URL)
            existing_item = self.collection.find_one({'url': item_dict['url']})
            
            if existing_item:
                # Detectar si hay cambios significativos
                has_changes = self._detect_changes(existing_item, item_dict, spider)
                
                if has_changes:
                    # Actualizar con nueva información y nuevo datetime
                    update_data = item_dict.copy()
                    update_data['datetime'] = item_dict['datetime']  # Nueva fecha de modificación
                    update_data['last_visited'] = item_dict['last_visited']  # Actualizar última visita
                    
                    result = self.collection.update_one(
                        {'url': item_dict['url']},
                        {'$set': update_data}
                    )
                    spider.logger.info(f"✅ Producto actualizado (cambios detectados): {item_dict['url']}")
                    
                else:
                    # Solo actualizar el campo last_visited
                    result = self.collection.update_one(
                        {'url': item_dict['url']},
                        {'$set': {'last_visited': item_dict['last_visited']}}
                    )
                    spider.logger.info(f"📅 Producto visitado (sin cambios): {item_dict['url']}")
                
            else:
                # Insertar nuevo item
                result = self.collection.insert_one(item_dict)
                spider.logger.info(f"🆕 Producto nuevo guardado en MongoDB: {item_dict['url']}")
            
            return item
            
        except Exception as e:
            spider.logger.error(f"❌ Error guardando item en MongoDB: {e}")
            raise DropItem(f"Error guardando item: {e}")
    
    def _detect_changes(self, existing_item, new_item, spider):
        """
        Detecta si hay cambios significativos entre el item existente y el nuevo
        """
        # Campos importantes a comparar
        important_fields = [
            'name', 'description', 'original_price', 'current_price', 
            'original_price_amount', 'current_price_amount', 'currency',
            'discount_percentage', 'discount_amount', 'has_discount', 'images_by_color'
        ]
        
        changes_detected = []
        
        for field in important_fields:
            old_value = existing_item.get(field)
            new_value = new_item.get(field)
            
            # Comparación especial para imágenes (comparar solo cantidad y colores)
            if field == 'images_by_color':
                old_summary = self._summarize_images(old_value) if old_value else {}
                new_summary = self._summarize_images(new_value) if new_value else {}
                
                if old_summary != new_summary:
                    changes_detected.append(f"{field}: cambió configuración de imágenes")
            
            # Comparación estándar para otros campos
            elif old_value != new_value:
                changes_detected.append(f"{field}: '{old_value}' → '{new_value}'")
        
        if changes_detected:
            spider.logger.info(f"🔍 Cambios detectados en {new_item['url']}:")
            for change in changes_detected:
                spider.logger.info(f"   - {change}")
            return True
        
        return False
    
    def _summarize_images(self, images_by_color):
        """
        Crea un resumen de las imágenes para comparación eficiente
        """
        if not images_by_color:
            return {}
        
        summary = {}
        for color_data in images_by_color:
            color_name = color_data.get('color', 'unknown')
            images_count = len(color_data.get('images', []))
            # Crear hash simple de las URLs de imágenes para detectar cambios
            image_urls = [img.get('src', '') for img in color_data.get('images', [])]
            url_hash = hash(tuple(sorted(image_urls)))
            
            summary[color_name] = {
                'count': images_count,
                'url_hash': url_hash
            }
        
        return summary

class HistoryPipeline:
    """
    Pipeline para mantener un historial de cambios en productos
    """
    
    def __init__(self, mongo_uri, mongo_db, history_collection, mongo_username=None, mongo_password=None, mongo_auth_source=None):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db 
        self.history_collection = history_collection
        self.mongo_username = mongo_username
        self.mongo_password = mongo_password
        self.mongo_auth_source = mongo_auth_source
        
    @classmethod
    def from_crawler(cls, crawler):
        """
        Método para obtener configuración desde settings.py
        """
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE"),
            history_collection=crawler.settings.get("MONGO_HISTORY_COLLECTION", "product_history"),
            mongo_username=crawler.settings.get("MONGO_USERNAME"),
            mongo_password=crawler.settings.get("MONGO_PASSWORD"),
            mongo_auth_source=crawler.settings.get("MONGO_AUTH_SOURCE")
        )
    
    def open_spider(self, spider):
        """Conexión similar a MongoDBPipeline"""
        try:
            if self.mongo_username and self.mongo_password:
                if not self.mongo_username in self.mongo_uri:
                    uri_parts = self.mongo_uri.split('://')
                    auth_uri = f"{uri_parts[0]}://{self.mongo_username}:{self.mongo_password}@{uri_parts[1]}"
                    if self.mongo_auth_source:
                        auth_uri += f"?authSource={self.mongo_auth_source}"
                    self.client = pymongo.MongoClient(auth_uri)
                else:
                    self.client = pymongo.MongoClient(self.mongo_uri)
            else:
                self.client = pymongo.MongoClient(self.mongo_uri)
            
            self.client.admin.command('ping')
            self.db = self.client[self.mongo_db]
            self.collection = self.db[self.history_collection]
            spider.logger.info(f"✅ Pipeline de historial conectado: {self.mongo_db}.{self.history_collection}")
            
        except Exception as e:
            spider.logger.error(f"❌ Error conectando pipeline de historial: {e}")
            raise
    
    def close_spider(self, spider):
        """Cerrar conexión"""
        self.client.close()
    
    def process_item(self, item, spider):
        """
        Guarda un registro histórico si el item fue marcado como modificado
        """
        # Solo procesar si el item tiene metadatos de cambios
        if hasattr(item, 'meta') and item.meta.get('changes_detected'):
            try:
                item_dict = ItemAdapter(item).asdict()
                
                # Crear registro de historial
                history_record = {
                    'product_url': item_dict['url'],
                    'change_date': item_dict['datetime'],
                    'changes': item.meta.get('changes_list', []),
                    'new_data': item_dict,
                    'site': item_dict.get('site', 'unknown')
                }
                
                self.collection.insert_one(history_record)
                spider.logger.info(f"📋 Registro histórico guardado para: {item_dict['url']}")
                
            except Exception as e:
                spider.logger.error(f"❌ Error guardando historial: {e}")
        
        return item

class DuplicatesPipeline:
    """
    Pipeline para filtrar items duplicados
    """
    
    def __init__(self):
        self.urls_seen = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get('url') in self.urls_seen:
            raise DropItem(f"Duplicate item found: {item!r}")
        else:
            self.urls_seen.add(adapter.get('url'))
            return item