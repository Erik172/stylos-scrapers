#!/usr/bin/env python3
"""
Utilidades para consultar cambios y estadísticas de productos
"""

import pymongo
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class ProductAnalyzer:
    """
    Clase para analizar cambios y estadísticas de productos
    """
    
    def __init__(self):
        # Configuración de MongoDB
        self.mongo_uri = os.getenv("MONGO_URI")
        self.mongo_db = os.getenv("MONGO_DATABASE", "stylos_scrapers")
        self.products_collection = os.getenv("MONGO_COLLECTION", "zara_products")
        self.history_collection = os.getenv("MONGO_HISTORY_COLLECTION", "product_history")
        
        # Conectar a MongoDB
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.products = self.db[self.products_collection]
        self.history = self.db[self.history_collection]
    
    def get_products_with_recent_changes(self, days=7):
        """
        Obtiene productos que han cambiado en los últimos N días
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        pipeline = [
            {
                "$match": {
                    "datetime": {"$gte": cutoff_iso}
                }
            },
            {
                "$project": {
                    "url": 1,
                    "name": 1,
                    "current_price": 1,
                    "has_discount": 1,
                    "datetime": 1,
                    "last_visited": 1
                }
            },
            {
                "$sort": {"datetime": -1}
            }
        ]
        
        return list(self.products.aggregate(pipeline))
    
    def get_price_changes(self, days=30):
        """
        Obtiene productos con cambios de precio en los últimos N días
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        return list(self.history.find({
            "change_date": {"$gte": cutoff_iso},
            "changes": {"$regex": "price"}
        }).sort("change_date", -1))
    
    def get_inactive_products(self, days=30):
        """
        Obtiene productos que no han sido visitados en los últimos N días
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        return list(self.products.find({
            "last_visited": {"$lt": cutoff_iso}
        }).sort("last_visited", 1))
    
    def get_statistics(self):
        """
        Obtiene estadísticas generales de la base de datos
        """
        stats = {}
        
        # Total de productos
        stats['total_products'] = self.products.count_documents({})
        
        # Productos con descuento
        stats['products_with_discount'] = self.products.count_documents({"has_discount": True})
        
        # Productos visitados hoy
        today = datetime.now().date().isoformat()
        stats['visited_today'] = self.products.count_documents({
            "last_visited": {"$regex": f"^{today}"}
        })
        
        # Total de cambios registrados
        stats['total_changes'] = self.history.count_documents({})
        
        # Cambios en la última semana
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        stats['changes_last_week'] = self.history.count_documents({
            "change_date": {"$gte": week_ago}
        })
        
        return stats
    
    def close(self):
        """Cerrar conexión"""
        self.client.close()

def print_statistics():
    """
    Función de utilidad para imprimir estadísticas
    """
    analyzer = ProductAnalyzer()
    
    try:
        print("🔍 ESTADÍSTICAS DE PRODUCTOS")
        print("=" * 40)
        
        stats = analyzer.get_statistics()
        
        print(f"📦 Total de productos: {stats['total_products']}")
        print(f"💰 Productos con descuento: {stats['products_with_discount']}")
        print(f"👀 Visitados hoy: {stats['visited_today']}")
        print(f"📋 Total de cambios: {stats['total_changes']}")
        print(f"🔄 Cambios última semana: {stats['changes_last_week']}")
        
        print("\n🔄 PRODUCTOS CON CAMBIOS RECIENTES")
        print("=" * 40)
        
        recent_changes = analyzer.get_products_with_recent_changes()
        for product in recent_changes[:5]:  # Mostrar solo los primeros 5
            print(f"• {product['name']}")
            print(f"  Precio: {product.get('current_price', 'N/A')}")
            print(f"  Última modificación: {product['datetime'][:10]}")
            print()
            
    finally:
        analyzer.close()

if __name__ == "__main__":
    print_statistics() 