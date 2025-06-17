# -*- coding: utf-8 -*-
"""
Módulo de Procesadores de Datos para Scrapy.

Este archivo contiene funciones de ayuda reutilizables (processors) diseñadas
para limpiar, normalizar y transformar los datos extraídos por las arañas
antes de ser almacenados. Estas funciones se utilizan típicamente con
Item Loaders de Scrapy.
"""

import re
from typing import Any, Dict, Literal, Optional

from unidecode import unidecode


def normalize_text(text: Any, case: Literal['original', 'upper', 'lower'] = 'original') -> Any:
    """
    Limpia y normaliza una cadena de texto, manejando acentos, espacios y mayúsculas/minúsculas.

    Esta función realiza las siguientes operaciones en secuencia:
    1. Reemplaza los saltos de línea ('\\n') con espacios.
    2. Translitera los caracteres a su equivalente ASCII más cercano (ej. 'á' -> 'a') usando `unidecode`.
    3. Elimina espacios en blanco al principio y al final.
    4. Opcionalmente, convierte el texto a mayúsculas o minúsculas.

    Es segura para usar con datos que no son strings; si la entrada no es un
    string, la retorna sin modificar.

    Args:
        text (Any): La cadena de texto a procesar. Puede ser cualquier tipo.
        case (Literal['original', 'upper', 'lower']): El caso al que se debe
            convertir el texto. Por defecto es 'original'.

    Returns:
        Any: El texto procesado y normalizado, o el valor original si la entrada
             no era una cadena de texto.
    """
    if not isinstance(text, str):
        return text

    # La librería unidecode es efectiva para remover acentos y caracteres especiales.
    clean_text = unidecode(text.replace('\n', ' ')).strip()

    if case == 'upper':
        return clean_text.upper()
    elif case == 'lower':
        return clean_text.lower()
    
    return clean_text


def normalize_price(price_text: Optional[str]) -> Dict[str, Any]:
    """
    Parsea una cadena de texto de precio y la convierte en un diccionario estructurado.

    Esta función está diseñada para ser robusta y manejar diferentes formatos de
    precios comunes en e-commerce, incluyendo símbolos de moneda, separadores de
    miles y diferentes monedas.

    Args:
        price_text (Optional[str]): El texto crudo del precio (ej. '$ 249.900 COP').
            Maneja correctamente valores `None`.

    Returns:
        Dict[str, Any]: Un diccionario que contiene:
            - 'amount' (float | None): El valor numérico del precio.
            - 'currency' (str | None): El código de la moneda (ej. 'COP', 'USD').
            - 'original' (str): El texto de entrada original.
            - 'error' (str, opcional): Un mensaje de error si la conversión falla.

    Examples:
        >>> normalize_price('$ 249.900 COP')
        {'amount': 249900.0, 'currency': 'COP', 'original': '$ 249.900 COP'}

        >>> normalize_price('USD 1,234.56')
        {'amount': 1234.56, 'currency': 'USD', 'original': 'USD 1,234.56'}

        >>> normalize_price('€ 99,99')
        {'amount': 99.99, 'currency': 'COP', 'original': '€ 99,99'}
        
        >>> normalize_price('Artículo no disponible')
        {'amount': None, 'currency': 'COP', 'original': 'Artículo no disponible', 'error': ...}
    """
    if not isinstance(price_text, str) or not price_text.strip():
        return {'amount': None, 'currency': None, 'original': price_text}

    try:
        clean_text = price_text.strip()

        # 1. Extraer código de moneda (ej. 'COP', 'USD'). Busca una palabra de 3 letras mayúsculas.
        #    Si no la encuentra, asume 'COP' como valor por defecto.
        currency_match = re.search(r'\b([A-Z]{3})\b', clean_text)
        currency = currency_match.group(1) if currency_match else 'COP'

        # 2. Aislar la parte numérica del texto, eliminando símbolos y letras.
        number_part = re.sub(r'[^\d,.]', '', clean_text)

        # 3. Lógica de conversión para manejar separadores de miles y decimales.
        #    Esta lógica es crucial para formatos internacionales.
        if ',' in number_part and '.' in number_part:
            # Formato europeo/latinoamericano: 1.234,56 -> 1234.56
            number_part = number_part.replace('.', '').replace(',', '.')
        elif ',' in number_part:
            # Solo hay coma: se asume que es el separador decimal.
            # Formato: 1234,56 -> 1234.56
            number_part = number_part.replace(',', '.')
        elif '.' in number_part and len(number_part.split('.')[-1]) < 3:
             # Hay punto, pero el último segmento tiene menos de 3 dígitos, se asume decimal.
             # Formato: 1234.56 -> 1234.56
             pass # El formato ya es correcto para float()
        else:
            # No hay coma, y los puntos son probablemente separadores de miles.
            # Formato: 249.900 -> 249900
            number_part = number_part.replace('.', '')

        amount = float(number_part) if number_part else None

        return {'amount': amount, 'currency': currency, 'original': price_text}

    except (ValueError, AttributeError, IndexError) as e:
        # Si cualquier paso de la conversión falla, retorna una estructura de error.
        return {'amount': None, 'currency': None, 'original': price_text, 'error': str(e)}