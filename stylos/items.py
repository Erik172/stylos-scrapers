import scrapy
from itemloaders.processors import MapCompose, TakeFirst

from .processors import normalize_text


class ImagenItem(scrapy.Item):
    """
    Representa una única imagen asociada a un producto.

    Este Item se utiliza comúnmente de forma anidada dentro de `ProductItem`
    para manejar galerías de imágenes.
    """
    # La URL (fuente) de la imagen.
    src = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El texto alternativo de la imagen, útil para SEO y accesibilidad. Se normaliza a mayúsculas.
    alt = scrapy.Field(
        input_processor=MapCompose(lambda text: normalize_text(text, case='upper')),
        output_processor=TakeFirst()
    )
    # Un campo para clasificar el tipo de imagen (ej: 'product_image', 'thumbnail', 'detail').
    img_type = scrapy.Field(
        output_processor=TakeFirst()
    )


class ProductItem(scrapy.Item):
    """
    Define el modelo de datos central para un producto extraído.

    Este item está diseñado para funcionar en conjunto con las Item Pipelines.
    Algunos campos se cargan directamente con datos crudos extraídos de la web,
    mientras que otros se dejan vacíos para ser calculados y enriquecidos
    posteriormente en pipelines (como `PricePipeline`).
    """

    # ----------------------------------------------------
    # --- Campos con Datos Crudos (Extraídos por la Araña)
    # ----------------------------------------------------

    # La URL canónica y única de la página del producto.
    url = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El nombre o título del producto. Se normaliza a mayúsculas.
    name = scrapy.Field(
        input_processor=MapCompose(lambda text: normalize_text(text, case='upper')),
        output_processor=TakeFirst()
    )
    # La descripción detallada del producto. Se normaliza a minúsculas.
    description = scrapy.Field(
        input_processor=MapCompose(lambda text: normalize_text(text, case='lower')),
        output_processor=TakeFirst()
    )
    # El precio original en formato de texto, tal como aparece en el sitio. Se usa como base para los cálculos.
    original_price = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El precio actual o de oferta en formato de texto.
    current_price = scrapy.Field(
        output_processor=TakeFirst()
    )

    # --------------------------------------------------------------------
    # --- Campos Enriquecidos (Calculados y Poblados por las Pipelines)
    # --------------------------------------------------------------------

    # El valor numérico (float) del precio original, procesado por PricePipeline.
    original_price_amount = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El valor numérico (float) del precio actual, procesado por PricePipeline.
    current_price_amount = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El código de la moneda (ej: 'COP', 'USD'), extraído del texto del precio.
    currency = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El porcentaje de descuento, calculado en PricePipeline.
    discount_percentage = scrapy.Field(
        output_processor=TakeFirst()
    )
    # El monto del descuento (diferencia numérica entre precios), calculado en PricePipeline.
    discount_amount = scrapy.Field(
        output_processor=TakeFirst()
    )
    # Un booleano que indica si el producto tiene un descuento activo.
    has_discount = scrapy.Field(
        output_processor=TakeFirst()
    )

    # ----------------------------------------------------
    # --- Campos para Datos Complejos o Anidados
    # ----------------------------------------------------

    # Campo para almacenar datos de imágenes, agrupadas por color.
    # Se espera que contenga una lista de diccionarios, ej:
    # [{'color': 'ROJO', 'images': [ImagenItem(), ...]}, ...]
    images_by_color = scrapy.Field()

    # ----------------------------------------------------
    # --- Campos de Metadatos
    # ----------------------------------------------------

    # Identificador del sitio web del que se extrajo el producto (ej: 'zara').
    site = scrapy.Field(
        output_processor=TakeFirst()
    )
    # La fecha y hora (timestamp) en que el item fue creado por primera vez.
    datetime = scrapy.Field(
        output_processor=TakeFirst()
    )
    # La fecha y hora (timestamp) de la última vez que la araña visitó esta URL.
    last_visited = scrapy.Field(
        output_processor=TakeFirst()
    )