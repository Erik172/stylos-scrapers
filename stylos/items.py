# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re
from unidecode import unidecode
from itemloaders.processors import TakeFirst, MapCompose, Join

def normalize_uppercase(text):
    return unidecode(text.replace('\n', ' ')).upper().strip()

def normalize_lowercase(text):
    return unidecode(text.replace('\n', ' ')).lower().strip()

def normalize_price(price_text):
    """
    Normaliza precios colombianos del formato '249.000 COP' a número y moneda
    Retorna un diccionario con 'amount' (float) y 'currency' (str)
    """
    if not price_text or not isinstance(price_text, str):
        return {'amount': None, 'currency': None, 'original': price_text}
    
    try:
        # Limpiar el texto del precio
        clean_text = price_text.strip()
        
        # Extraer moneda (últimas 3 letras usualmente)
        currency_match = re.search(r'([A-Z]{3})$', clean_text)
        currency = currency_match.group(1) if currency_match else 'COP'
        
        # Extraer solo números, puntos y comas
        number_part = re.sub(r'[^\d.,]', '', clean_text)
        
        # Manejar formato colombiano (puntos como separadores de miles)
        if '.' in number_part and ',' in number_part:
            # Formato: 1.234.567,89
            number_part = number_part.replace('.', '').replace(',', '.')
        elif '.' in number_part and len(number_part.split('.')[-1]) == 3:
            # Formato: 249.000 (punto como separador de miles)
            number_part = number_part.replace('.', '')
        elif ',' in number_part and len(number_part.split(',')[-1]) <= 2:
            # Formato: 1234,56 (coma como decimal)
            number_part = number_part.replace(',', '.')
        
        # Convertir a float
        amount = float(number_part)
        
        return {
            'amount': amount,
            'currency': currency,
            'original': price_text
        }
        
    except (ValueError, AttributeError) as e:
        return {
            'amount': None,
            'currency': None,
            'original': price_text,
            'error': str(e)
        }

def extract_price_amount(price_text):
    """Extrae solo el monto numérico del precio"""
    normalized = normalize_price(price_text)
    return normalized.get('amount')

def extract_currency(price_text):
    """Extrae solo la moneda del precio"""
    normalized = normalize_price(price_text)
    return normalized.get('currency')

class ImagenItem(scrapy.Item):
    """
    Define la estructura de una imagen individual.
    """
    src = scrapy.Field(output_processor = TakeFirst())
    alt = scrapy.Field(
        input_processor = MapCompose(normalize_uppercase),
        output_processor = TakeFirst()
    )
    img_type = scrapy.Field(output_processor = TakeFirst())

class ProductItem(scrapy.Item):
    """
    Define la estructura de un producto principal.
    Contendrá la información del producto y una lista de sus imágenes.
    """
    url = scrapy.Field(output_processor = TakeFirst())
    name = scrapy.Field(
        input_processor = MapCompose(normalize_uppercase),
        output_processor = TakeFirst()
    )
    description = scrapy.Field(
        input_processor = MapCompose(normalize_lowercase),
        output_processor = TakeFirst()
    )
    
    # Datos de precio (texto original)
    original_price = scrapy.Field(output_processor = TakeFirst())
    current_price = scrapy.Field(output_processor = TakeFirst())
    
    # Datos de precio normalizados (numéricos)
    original_price_amount = scrapy.Field(
        input_processor = MapCompose(extract_price_amount),
        output_processor = TakeFirst()
    )
    current_price_amount = scrapy.Field(
        input_processor = MapCompose(extract_price_amount),
        output_processor = TakeFirst()
    )
    currency = scrapy.Field(
        input_processor = MapCompose(extract_currency),
        output_processor = TakeFirst()
    )
    
    # Datos de descuento
    discount_percentage = scrapy.Field(output_processor = TakeFirst())
    discount_amount = scrapy.Field(output_processor = TakeFirst())  # Diferencia en números
    has_discount = scrapy.Field(output_processor = TakeFirst())
    
    # Campo para los datos anidados
    images_by_color = scrapy.Field() # Será una lista de diccionarios [{'color': '...', 'images': [ImageItem, ...]}]
    
    site = scrapy.Field(output_processor = TakeFirst())
    datetime = scrapy.Field(output_processor = TakeFirst())
    last_visited = scrapy.Field(output_processor = TakeFirst())