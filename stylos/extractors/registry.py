"""
Archivo de registro automático de extractors.
Importa todos los extractors para que se registren automáticamente.
"""

# Importar todos los extractors para registro automático
from stylos.extractors.zara_extractor import ZaraExtractor
from stylos.extractors.mango_extractor import MangoExtractor

# También re-exportar el registry para conveniencia
from stylos.extractors import ExtractorRegistry

# Función de utilidad para listar extractors registrados
def list_available_extractors():
    """Lista todos los extractors disponibles."""
    registered = ExtractorRegistry.list_registered()
    print("🕷️ Extractors registrados:")
    for spider_name in registered:
        print(f"  - {spider_name}")
    return registered

# Auto-registro al importar
if __name__ == "__main__":
    list_available_extractors() 