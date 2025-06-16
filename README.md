# Stylos Scraper 🕷️👗

**Parte del ecosistema Stylos** - Scraper inteligente para sitios de moda

<!-- GIF -->
![Zara Scraper Demo](media/zara-demo.gif)

## 🎯 Objetivo del Proyecto

Stylos Scraper es un componente clave del proyecto **Stylos**, una aplicación de inteligencia artificial que analiza la ropa de tu "armario" y aprende a combinarlas según diferentes estilos como:

- 💼 **Old Money** - Elegancia atemporal
- 🎩 **Formal** - Vestimenta profesional
- 🛹 **Streetwear** - Moda urbana y casual
- ✨ Y muchos más estilos personalizables

## 🚧 Estado Actual

**⚠️ Proyecto en Desarrollo Activo**

Este scraper está siendo desarrollado para recopilar datos de moda de diferentes retailers online, con el objetivo de entrenar modelos de IA que puedan:

1. Identificar prendas y sus características
2. Analizar combinaciones de ropa
3. Aprender patrones de estilo
4. Generar recomendaciones personalizadas

## 🛠️ Tecnologías Utilizadas

- **Framework Principal**: Scrapy 2.13.2
- **Navegación Dinámica**: Selenium WebDriver + Chrome
- **Navegación Avanzada**: Playwright (implementado)
- **Proxy/User Agent**: Fake UserAgent 2.2.0
- **Base de Datos**: MongoDB (PyMongo 4.13.1)
- **Lenguaje**: Python 3.x
- **Otros**: requests, lxml, css-select

## 📁 Estructura del Proyecto

```
stylos-scrapers/
├── stylos/
│   ├── spiders/
│   │   ├── __init__.py      # Configuración de spiders
│   │   ├── zara.py          # Spider para Zara (✅ Completo)
│   │   └── mango.py         # Spider para Mango (🚧 Básico)
│   ├── middlewares.py       # Middlewares personalizados
│   ├── settings.py          # Configuración del proyecto
│   ├── items.py            # Definición de items/datos
│   ├── pipelines.py        # Procesamiento de datos
│   └── __init__.py         
├── requirements.txt         # 58 dependencias especializadas
├── scrapy.cfg              # Configuración de despliegue
├── zara.json               # Datos scrapeados (ejemplo)
└── README.md               # Este archivo
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.7+
- Chrome Browser
- ChromeDriver (se instala automáticamente)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd stylos-scrapers
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Uso

### Ejecutar Spiders Disponibles

```bash
# Spider de Zara (completamente funcional)
scrapy crawl zara

# Spider de Mango (en desarrollo inicial)
scrapy crawl mango

# Guardar resultados en archivo JSON
scrapy crawl zara -o zara_productos.json
scrapy crawl mango -o mango_productos.json

# Ejecutar con configuración personalizada
scrapy crawl zara -s USER_AGENT='tu-user-agent'
scrapy crawl zara -s DOWNLOAD_DELAY=3
```

### 🔧 Características Avanzadas Implementadas

#### Spider de Zara (Avanzado)
- ✅ **Navegación dinámica de menús**: Automatiza clicks en hamburguesa y categorías
- ✅ **Scroll inteligente**: Carga productos de scroll infinito
- ✅ **Manejo de pestañas múltiples**: Abre productos en nuevas pestañas
- ✅ **Extracción de URLs**: Productos y categorías con regex patterns
- ✅ **Sistema anti-detección**: User agents rotativos y configuración stealth
- ⚠️ **Extracción de datos de productos**: En desarrollo

#### Middlewares Personalizados
- ✅ **BlocklistMiddleware**: Filtra URLs no deseadas (login, registro, etc.)
- ✅ **Configuración anti-bot**: Headers personalizados y user agents
- ✅ **Manejo de errores**: Screenshots automáticos para debugging

#### Configuración del Sistema
- ✅ **MongoDB**: Preparado para almacenamiento de datos
- ✅ **Selenium**: Para navegación dinámica
- ✅ **ROBOTSTXT_OBEY = False**: Para máxima flexibilidad

## 🎯 Retailers Soportados

### ✅ Completamente Implementados
- **Zara** (zara.py) - Spider avanzado con:
  - 🔄 Navegación completa de categorías (Mujer/Hombre)
  - 🕷️ 285 líneas de código optimizado
  - 🎯 Extracción de productos con patrones regex
  - 🚀 Selenium + ChromeDriver integrado
  - 📱 Manejo de scroll infinito y pestañas múltiples

### 🚧 En Desarrollo Inicial
- **Mango** (mango.py) - Spider básico:
  - 📝 Estructura inicial creada (13 líneas)
  - 🌐 Dominio configurado: shop.mango.com
  - ⚠️ Requiere implementación de lógica de scraping

### 🔄 Próximos en Desarrollo
- **H&M** - Fast fashion sueco
- **Uniqlo** - Minimalismo japonés  
- **Pull & Bear** - Grupo Inditex
- **Bershka** - Moda joven

### 📋 Roadmap Extendido
- **Nike** - Deportivo premium
- **Adidas** - Deportivo lifestyle
- **Massimo Dutti** - Elegancia premium
- **Stradivarius** - Moda femenina
- **Oysho** - Ropa interior y deportiva
- **Lefties** - Outlet Inditex

## 🤝 Contribución

Como el proyecto está en desarrollo activo, las contribuciones son bienvenidas:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📊 Datos Recopilados

### 🎯 Estructura de Datos Objetivo
Los spiders están diseñados para extraer y normalizar:

#### Información Básica del Producto
- **Identificación**: SKU, código de producto, URL original
- **Naming**: Nombre, descripción, marca
- **Pricing**: Precio actual, precio original, descuentos
- **Availability**: Stock, tallas disponibles

#### Metadatos de Categorización
- **Género**: Mujer, Hombre, Niños, Unisex
- **Tipo de prenda**: Camiseta, Pantalón, Vestido, Zapatos, etc.
- **Categoría**: Formal, Casual, Deportivo, Streetwear
- **Temporada**: Primavera/Verano, Otoño/Invierno
- **Estilo**: Old Money, Minimalist, Boho, etc.

#### Assets Visuales
- **Imágenes principales**: URLs de alta resolución
- **Imágenes secundarias**: Diferentes ángulos y detalles
- **Imágenes de outfit**: Combinaciones sugeridas
- **Color palette**: Colores dominantes extraídos

#### Datos Técnicos
- **Material**: Composición de telas
- **Cuidado**: Instrucciones de lavado
- **Origen**: País de fabricación
- **Sustainability**: Materiales eco-friendly

### 🗄️ Almacenamiento
- **Formato**: JSON estructurado + MongoDB
- **Pipeline**: Limpieza y normalización automática
- **Versionado**: Control de cambios de precios y stock

## ⚡ Próximos Pasos

1. **Completar extracción de datos** en spider de Zara
2. **Implementar spiders adicionales** para otros retailers
3. **Sistema de limpieza de datos** para normalizar información
4. **Pipeline de almacenamiento** para base de datos
5. **Integración con Stylos Core** para entrenamiento del modelo

## 🔧 Configuración de Desarrollo

### Variables de Entorno

```bash
# Configurar en tu .env (opcional)
CHROME_DRIVER_PATH=/path/to/chromedriver
HEADLESS_MODE=false
DOWNLOAD_DELAY=1
MONGODB_URI=mongodb://localhost:27017/stylos
CONCURRENT_REQUESTS=16
```

### 🛠️ Configuración Avanzada del Sistema

#### Settings.py - Configuraciones Clave
```python
# User Agent personalizado
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Robots.txt deshabilitado para flexibilidad
ROBOTSTXT_OBEY = False

# BlocklistMiddleware activo
DOWNLOADER_MIDDLEWARES = {
    "stylos.middlewares.BlocklistMiddleware": 544,
}
```

#### Middlewares Implementados
- **BlocklistMiddleware**: Filtra automáticamente URLs de login, registro y páginas no productivas
- **StylosSpiderMiddleware**: Middleware base para extensiones futuras
- **StylosDownloaderMiddleware**: Manejo de requests y responses

### 🔍 Debugging y Monitoreo

Para debugging efectivo:
- **Screenshots automáticos**: En `zara.py` línea ~120
- **Logs detallados**: `self.log()` en cada paso crítico
- **Modo no-headless**: Comentar línea 24 en `zara.py`
- **Inspect elements**: Usar selectores XPath y CSS específicos
- **Error handling**: Try-catch en navegación dinámica

## ⚠️ Advertencias y Mejores Prácticas

### 🚨 Aspectos Legales y Éticos
- **Respeta robots.txt** (actualmente deshabilitado para desarrollo)
- **Implementa delays apropiados** para no sobrecargar servidores
- **Usa proxies rotativos** en producción para distribución de carga
- **Monitorea cambios** frecuentes en estructuras de sitios web

### 🔧 Aspectos Técnicos
- **Chrome Driver**: Se actualiza automáticamente vía webdriver-manager
- **Memoria**: Selenium puede consumir mucha RAM con múltiples pestañas
- **Timeouts**: Configurados en 15-20 segundos para sitios lentos
- **Stale Elements**: Manejados con re-búsqueda de elementos

### 📊 Producción
- **Escalabilidad**: Considera usar Scrapy Cloud o Scrapyd
- **Monitoreo**: Implementa alertas para fallos de scraping
- **Datos**: Valida la calidad de datos extraídos regularmente
- **Backups**: Implementa versionado de datos scrapeados

## 📄 Licencia

Este proyecto es parte del ecosistema Stylos y está en desarrollo.

---

**Desarrollado con ❤️ para el futuro de la moda personalizada**

> **Nota**: Este es un proyecto en desarrollo activo. La documentación y funcionalidades pueden cambiar frecuentemente. 