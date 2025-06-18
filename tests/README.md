# Suite de Pruebas - Stylos Scrapers

Este directorio contiene la suite de pruebas unitarias para el proyecto Scrapy 'stylos'. Los tests están diseñados para validar el funcionamiento correcto de todas las pipelines del sistema de scraping.

## Estructura de Pruebas

### 📁 Archivos de Prueba

- **`test_pipelines.py`**: Suite completa de pruebas para todas las pipelines del proyecto

## Tecnologías Utilizadas

La suite de pruebas utiliza las siguientes librerías y técnicas:

- **pytest**: Framework principal para estructurar y ejecutar las pruebas
- **Fixtures de Pytest**: Para crear objetos reutilizables (spiders, items) manteniendo las pruebas limpias
- **unittest.mock.patch**: Para interceptar y simular el cliente de `pymongo`
- **mongomock**: Implementación en memoria de MongoDB para pruebas rápidas y fiables
- **pytest-monkeypatch**: Para modificar clases o funciones en tiempo de ejecución

## Suites de Pruebas

### 🏷️ TestPricePipeline

Pruebas para la pipeline que normaliza precios y calcula descuentos.

**Funcionalidades probadas:**
- ✅ Cálculo correcto de descuentos cuando el precio actual es menor que el original
- ✅ Manejo de items sin descuento (asignación de valores por defecto)
- ✅ Normalización de precios con diferentes formatos y monedas

**Tests incluidos:**
- `test_calculates_discount_correctly`: Verifica el cálculo de descuentos
- `test_handles_items_without_discount`: Maneja items sin precio original

### 🔄 TestDuplicatesPipeline  

Pruebas para la pipeline que filtra items duplicados por URL.

**Funcionalidades probadas:**
- ✅ Filtrado de URLs duplicadas en una misma ejecución
- ✅ Permitir el paso del primer item con URL única
- ✅ Descarte de items con URLs ya procesadas

**Tests incluidos:**
- `test_filters_duplicate_urls`: Verifica el filtrado de duplicados

### 🗄️ TestMongoDBInteraction

Pruebas para las pipelines que interactúan con MongoDB.

**Pipelines probadas:**
- **MongoDBPipeline**: Inserción y actualización de productos
- **HistoryPipeline**: Creación de registros de auditoría

**Funcionalidades probadas:**
- ✅ Inserción de nuevos productos en la base de datos
- ✅ Actualización de productos existentes cuando se detectan cambios
- ✅ Creación de registros de historial para cambios detectados
- ✅ Omisión de items sin cambios en el historial

**Tests incluidos:**
- `test_mongodb_pipeline_inserts_new_item`: Inserción de nuevos productos
- `test_mongodb_pipeline_updates_existing_item`: Actualización de productos existentes
- `test_history_pipeline_creates_record_on_change`: Creación de registros de historial
- `test_history_pipeline_skips_unchanged_item`: Omisión de items sin cambios

### 🛠️ TestAuxiliaryPipelines

Pruebas para pipelines auxiliares y de plantilla.

**Funcionalidades probadas:**
- ✅ Verificación de que las pipelines de plantilla no modifican los items

**Tests incluidos:**
- `test_stylos_pipeline_passthrough`: Verifica que la pipeline plantilla retorna items sin modificar

## Fixtures Disponibles

### 🎭 mock_spider
Crea un objeto simulado de Spider de Scrapy con configuración completa:
- Logger simulado
- Settings de MongoDB configurados
- Credenciales de prueba

### 📦 sample_item_class
Define una clase de Item de Scrapy con todos los campos necesarios:
- Campos de entrada del spider
- Campos generados por pipelines
- Metadatos de comunicación entre pipelines

## Ejecutar las Pruebas

### Ejecutar todas las pruebas
```bash
pytest tests/
```

### Ejecutar una suite específica
```bash
pytest tests/test_pipelines.py::TestPricePipeline
```

### Ejecutar con verbose y mostrar prints
```bash
pytest tests/ -v -s
```

### Generar reporte de cobertura
```bash
pytest tests/ --cov=stylos --cov-report=html
```

## Configuración

Las pruebas utilizan la configuración definida en `pytest.ini` en la raíz del proyecto.

## Patrón de Aislamiento

Todas las pruebas siguen el patrón **AAA** (Arrange-Act-Assert):

1. **Arrange**: Preparación del entorno y datos de prueba
2. **Act**: Ejecución de la funcionalidad a probar  
3. **Assert**: Verificación de los resultados esperados

Las pruebas están completamente aisladas de recursos externos mediante el uso de mocks y simuladores, garantizando:
- ⚡ Velocidad de ejecución
- 🔒 Fiabilidad (no dependen de servicios externos)
- 🧪 Reproducibilidad consistente 