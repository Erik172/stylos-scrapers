# Contribution Guide - Stylos Scrapers 🕷️👗

Thank you for your interest in contributing to the **Stylos Scrapers** project! This guide will help you set up your development environment and make effective contributions.

## 📋 Table of Contents

- [🚀 Initial Setup](#-initial-setup)
- [🏗️ Project Architecture](#️-project-architecture)
- [🛠️ Development Environment](#️-development-environment)
- [🕷️ Adding a New Retailer](#️-adding-a-new-retailer)
- [🧪 Testing and Validation](#-testing-and-validation)
- [📝 Code Standards](#-code-standards)
- [🔄 Pull Request Process](#-pull-request-process)
- [🐛 Reporting Bugs](#-reporting-bugs)
- [❓ Getting Help](#-getting-help)

## 🚀 Initial Setup

### Prerequisites

```bash
# Required tools
- Python 3.11+
- Docker and Docker Compose
- Git
- Recommended IDE: VS Code with Python/Docker extensions
```

### 1. Fork and Clone

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/stylos-scrapers.git
cd stylos-scrapers

# 3. Set up upstream
git remote add upstream https://github.com/erik172/stylos-scrapers.git
```

### 2. Environment Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Setup

```bash
# Create a .env file in the project root
cp .env.example .env

# Edit .env with your configuration
# Example content:
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=stylos_scrapers
MONGO_COLLECTION=products
SELENIUM_HUB_URL=http://localhost:4444
SELENIUM_MODE=remote
SENTRY_DSN=your-optional-sentry-dsn
```

## 🏗️ Project Architecture

### Directory Structure

```
stylos-scrapers/
├── 📁 app/                     # API Server (FastAPI)
│   ├── api_server.py          # Main server
│   └── startup.sh             # Startup script
├── 📁 stylos/                  # Main Scrapy module
│   ├── 📁 spiders/            # Scraping spiders
│   │   ├── zara.py           # Zara spider
│   │   └── mango.py          # Mango spider
│   ├── 📁 extractors/         # Modular extractors
│   │   ├── registry.py       # Extractor registry
│   │   ├── zara_extractor.py # Zara extractor
│   │   └── mango_extractor.py # Mango extractor
│   ├── items.py              # Item definitions
│   ├── pipelines.py          # Processing pipelines
│   ├── middlewares.py        # Custom middlewares
│   ├── settings.py           # Scrapy settings
│   └── processors.py         # Data processors
├── 📁 tests/                  # Unit tests
├── control_scraper.py        # CLI client
├── docker-compose.yml        # Docker orchestration
├── Dockerfile               # Main Docker image
├── requirements.txt         # Python dependencies
└── README.md               # Main documentation
```

### Main Components

#### 🌐 **API Server (FastAPI)**
- **Port**: 8000
- **Function**: Manages scraping jobs
- **Endpoints**: `/schedule`, `/status/{job_id}`

#### 🐙 **Scrapyd Server**
- **Port**: 6800
- **Function**: Executes Scrapy spiders
- **Management**: Jobs, logs, automatic deployment

#### 🕷️ **Selenium Grid**
- **Hub**: 4444
- **Function**: Orchestrates Chrome browsers
- **Scalability**: Configurable number of Chrome nodes

## 🛠️ Development Environment

### Option 1: Development with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Verify that all services are running
docker-compose ps

# View logs for a specific service
docker-compose logs -f api
docker-compose logs -f scrapyd

# Access the Selenium Grid web interface
# http://localhost:4444
```

### Option 2: Local Development (Without Docker)

```bash
# Terminal 1: Start only Selenium Grid
docker-compose up selenium-hub chrome -d

# Terminal 2: Run a spider directly
scrapy crawl zara

# Terminal 3: Run with arguments
scrapy crawl zara -a url="https://www.zara.com/us/en/example-product"
```

### Useful Development Commands

```bash
# Run a specific spider
python control_scraper.py --spider zara

# Run with a specific URL (test mode)
python control_scraper.py --spider zara --url "https://www.zara.com/us/en/product"

# Run with regional settings
python control_scraper.py --spider zara --country us --lang en

# Run tests
pytest tests/

# Check code style
flake8 stylos/
```

## 🕷️ Adding a New Retailer

### 1. Create the Spider

```python
# stylos/spiders/new_retailer.py
import scrapy
from scrapy.loader import ItemLoader
from stylos.items import ProductItem
from datetime import datetime

class NewRetailerSpider(scrapy.Spider):
    name = "new_retailer"
    allowed_domains = ["new-retailer.com"]
    start_urls = ["https://new-retailer.com/categories"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_menu,
                meta={
                    'selenium': True,  # Use Selenium if necessary
                    'extraction_type': 'menu'  # Extraction type for the middleware
                }
            )

    def parse_menu(self, response):
        # URLs are automatically extracted by the extractor
        extracted_urls = response.meta.get('extracted_urls', [])
        
        for url in extracted_urls:
            yield response.follow(
                url,
                callback=self.parse_category,
                meta={'selenium': True, 'extraction_type': 'category'}
            )

    def parse_category(self, response):
        # Extract product URLs
        product_urls = response.css('a.product-link::attr(href)').getall()
        
        for url in product_urls:
            yield response.follow(
                url,
                callback=self.parse_product,
                meta={'selenium': True, 'extraction_type': 'product'}
            )

    def parse_product(self, response):
        # Extract product data
        loader = ItemLoader(item=ProductItem(), selector=response)
        
        # Use data extracted by the middleware/extractor
        product_data = response.meta.get('product_data', {})
        extracted_images = response.meta.get('extracted_images', {})
        
        loader.add_value('url', response.url)
        loader.add_value('name', product_data.get('name', ''))
        loader.add_value('description', product_data.get('description', ''))
        loader.add_value('raw_prices', product_data.get('prices', []))
        loader.add_value('currency', product_data.get('currency', ''))
        
        # Process images by color
        images_by_color = self._process_images(extracted_images)
        loader.add_value('images_by_color', images_by_color)
        
        # System metadata
        loader.add_value('site', 'NEW_RETAILER')
        loader.add_value('datetime', datetime.now().isoformat())
        loader.add_value('last_visited', datetime.now().isoformat())
        
        yield loader.load_item()
    
    def _process_images(self, extracted_images):
        """Process images extracted by the extractor"""
        images_by_color = []
        
        for color_name, images in extracted_images.items():
            if images:
                from stylos.items import ImagenItem
                imagen_items = []
                
                for img_data in images:
                    imagen_item = ImagenItem()
                    imagen_item['src'] = img_data.get('src', '')
                    imagen_item['alt'] = img_data.get('alt', '')
                    imagen_item['img_type'] = img_data.get('type', 'product_image')
                    imagen_items.append(imagen_item)
                
                images_by_color.append({
                    'color': color_name,
                    'images': imagen_items
                })
        
        return images_by_color
```

### 2. Create the Extractor

```python
# stylos/extractors/new_retailer_extractor.py
from stylos.extractors import BaseExtractor, register_extractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@register_extractor('new_retailer')
class NewRetailerExtractor(BaseExtractor):
    """Extractor for New Retailer"""
    
    # Selector configuration
    SELECTORS = {
        'product_name': 'h1.product-title',
        'price': '.price-current',
        'original_price': '.price-original',
        'description': '.product-description',
        'images': '.product-image img',
        'currency': '.price-currency'
    }
    
    def extract_menu_data(self) -> dict:
        """Extract URLs from the main menu"""
        try:
            # Wait for the menu to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.menu-categories'))
            )
            
            # Extract category links
            category_links = self.driver.find_elements(By.CSS_SELECTOR, '.category-link')
            urls = [link.get_attribute('href') for link in category_links]
            
            return {
                'extracted_urls': urls
            }
        except Exception as e:
            self.spider.logger.error(f"Error extracting menu: {e}")
            return {'extracted_urls': []}

    def extract_category_data(self) -> dict:
        """Extract data from a category page with infinite scroll"""
        try:
            # Implement infinite scroll
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_attempts = 20
            
            while scroll_attempts < max_attempts:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
            
            return {
                'scroll_completed': True,
                'scroll_attempts': scroll_attempts
            }
        except Exception as e:
            self.spider.logger.error(f"Error extracting category: {e}")
            return {'scroll_completed': False, 'scroll_attempts': 0}

    def extract_product_data(self) -> dict:
        """Extract product data"""
        try:
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.SELECTORS['product_name']))
            )
            
            # Extract basic data
            name = self._safe_extract_text(self.SELECTORS['product_name'])
            description = self._safe_extract_text(self.SELECTORS['description'])
            
            # Extract prices
            current_price = self._safe_extract_text(self.SELECTORS['price'])
            original_price = self._safe_extract_text(self.SELECTORS['original_price'])
            currency = self._safe_extract_text(self.SELECTORS['currency'])
            
            # Extract images by color
            images_by_color = self._extract_images_by_color()
            
            return {
                'product_data': {
                    'name': name,
                    'description': description,
                    'prices': [current_price, original_price],
                    'currency': currency
                },
                'extracted_images': images_by_color
            }
        except Exception as e:
            self.spider.logger.error(f"Error extracting product: {e}")
            return {'product_data': {}, 'extracted_images': {}}

    def _extract_images_by_color(self) -> dict:
        """Extract product images organized by color"""
        try:
            images_by_color = {}
            
            # Get current color or use "Default" if no variants
            color_name = self._get_current_color() or "Default"
            
            # Extract images for the current color
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTORS['images'])
            images = []
            
            for img in image_elements:
                src = self._get_best_image_url(img)  # Use method from BaseExtractor
                alt = img.get_attribute('alt')
                if src and self._is_valid_image_src(src):
                    images.append({
                        'src': src,
                        'alt': alt or '',
                        'type': 'product_image'
                    })
            
            if images:
                images_by_color[color_name] = images
            
            return images_by_color
        except Exception as e:
            self.spider.logger.error(f"Error extracting images by color: {e}")
            return {}
    
    def _get_current_color(self) -> str:
        """Get the name of the current color"""
        try:
            color_element = self.driver.find_element(By.CSS_SELECTOR, '.product-color-name')
            return color_element.text.strip()
        except:
            return "Default"

    def _safe_extract_text(self, selector: str) -> str:
        """Safely extract text"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""
```

### 3. Automatic Extractor Registration

The extractor registration is **automatic** thanks to the `@register_extractor('new_retailer')` decorator.

You don't need to manually register the extractor. The decorator handles:
- Automatically registering the extractor in the `ExtractorRegistry`
- Associating the spider name with the extractor class
- Making it available to the Selenium middleware

```python
# Registration is automatic when you use:
@register_extractor('new_retailer')
class NewRetailerExtractor(BaseExtractor):
    # ... your implementation

# To verify it's registered, you can use:
from stylos.extractors import ExtractorRegistry
print(ExtractorRegistry.list_registered())
# Output: ['zara', 'mango', 'new_retailer']
```

### 4. Configure Domains (Optional)

```python
# stylos/spiders/new_retailer.py
# Configure allowed domains in the spider
class NewRetailerSpider(scrapy.Spider):
    name = "new_retailer"
    allowed_domains = ["new-retailer.com"]
    # ... rest of the code

# stylos/middlewares.py
# If you need to block specific URLs, add them to the BlocklistMiddleware
BLOCKLIST_TERMS = [
    # ... other terms
    '/new-retailer-promo',  # Example of a URL to block
]
```

## 🧪 Testing and Validation

### Test Structure

```python
# tests/test_new_retailer_extractor.py
import pytest
from unittest.mock import Mock, patch
from stylos.extractors.new_retailer_extractor import NewRetailerExtractor

class TestNewRetailerExtractor:
    
    def setup_method(self):
        """Set up mocks for each test"""
        self.mock_driver = Mock()
        self.mock_spider = Mock()
        self.mock_spider.logger = Mock()
        self.extractor = NewRetailerExtractor(self.mock_driver, self.mock_spider)
    
    def test_extract_product_data_success(self):
        """Test successful data extraction"""
        # Mock the HTML element
        mock_element = Mock()
        mock_element.text = "Test Product"
        
        self.mock_driver.find_element.return_value = mock_element
        
        # Run extraction
        result = self.extractor.extract_product_data()
        
        # Verify results
        assert result['product_data']['name'] == "Test Product"
        assert 'description' in result['product_data']
        assert 'prices' in result['product_data']
    
    def test_extract_product_data_error_handling(self):
        """Test error handling"""
        # Simulate a Selenium error
        self.mock_driver.find_element.side_effect = Exception("Element not found")
        
        # Run extraction
        result = self.extractor.extract_product_data()
        
        # Verify it returns an empty dict on error
        assert result == {'product_data': {}, 'extracted_images': {}}
        assert self.mock_spider.logger.error.called
```

### Testing Commands

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_new_retailer_extractor.py

# Run with coverage
pytest --cov=stylos tests/

# Run a specific test with verbose output
pytest -v tests/test_new_retailer_extractor.py::TestNewRetailerExtractor::test_extract_product_data_success
```

### Manual Validation

```bash
# Test an individual spider
scrapy crawl new_retailer -L INFO

# Test with a specific URL
scrapy crawl new_retailer -a url="https://new-retailer.com/product" -L DEBUG

# Test with output to a file
scrapy crawl new_retailer -o output.json -L INFO
```

## 📝 Code Standards

### Code Style

```python
# Follow PEP 8
# Use type hints
def extract_product_data(self) -> dict:
    """Extract product data with type hints"""
    pass

# Document methods with docstrings
def parse_product(self, response):
    """
    Parse an individual product page.
    
    Args:
        response: Scrapy HTTP response
        
    Yields:
        ProductItem: Item with product data
    """
    pass

# Use appropriate logging
self.spider.logger.info("Processing product: %s", response.url)
self.spider.logger.error("Error extracting data: %s", str(e))
```

### Naming Conventions

```python
# Spiders: new_retailer.py
# Extractors: new_retailer_extractor.py
# Classes: PascalCase
# Functions/variables: snake_case
# Constants: UPPER_SNAKE_CASE

# Examples
class ZaraExtractor:  # ✅ Correct
    SELECTORS = {}  # ✅ Constant
    
    def extract_product_data(self):  # ✅ Method
        product_url = "..."  # ✅ Variable
```

### Error Handling

```python
# Use specific try/except blocks
from selenium.common.exceptions import NoSuchElementException

try:
    element = self.driver.find_element(By.CSS_SELECTOR, selector)
    return element.text.strip()
except NoSuchElementException:
    self.spider.logger.warning(f"Element not found: {selector}")
    return ""
except Exception as e:
    self.spider.logger.error(f"Unexpected error: {e}")
    return ""
```

## 🔄 Pull Request Process

### 1. Prepare Your Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a branch for your feature
git checkout -b feature/new-retailer-hm

# Make atomic commits
git add .
git commit -m "feat: add spider for H&M

- Implement HMSpider with category navigation
- Create HMExtractor with specific selectors
- Add tests for H&M extractor
- Document specific configuration"
```

### 2. Quality Criteria

#### ✅ **PR Checklist**

- [ ] **Functional Code**: Spider extracts data correctly
- [ ] **Tests Passing**: `pytest tests/` runs without errors
- [ ] **Documentation**: Docstrings and comments are appropriate
- [ ] **Logging**: Use logger instead of print()
- [ ] **Configuration**: Environment variables are documented
- [ ] **Robust Selectors**: Not dependent on specific IDs
- [ ] **Error Handling**: Appropriate try/except blocks
- [ ] **Rate Limiting**: Respect for terms of service
- [ ] **Clean Data**: Normalization of prices/text

#### 🧪 **Required Tests**

- [ ] **Unit test** for the extractor
- [ ] **Integration test** for the spider
- [ ] **Error handling test**
- [ ] **Test with real data** (at least 5 products)

### 3. PR Description

```markdown
## 🆕 New Retailer: H&M Colombia

### 📋 Description
Complete implementation of the spider and extractor for H&M Colombia, including:
- Navigation through women's and men's categories
- Product extraction with prices in COP
- Image handling by color
- Infinite scroll for product loading

### 🔧 Technical Changes
- **New files:**
  - `stylos/spiders/hm.py` - Main spider
  - `stylos/extractors/hm_extractor.py` - Modular extractor
  - `tests/test_hm_extractor.py` - Unit tests

- **Modified files:**
  - `RETAILERS.md` - Updated documentation
  - `stylos/middlewares.py` - If changes to the blocklist are needed

### 🧪 Testing
- ✅ Unit tests: 15 tests, 100% coverage
- ✅ Manual test: 50+ products extracted correctly
- ✅ Rate limiting: 1 request/second respected
- ✅ Error handling: Timeouts and missing elements

### 📊 Extracted Data
- **Products**: Name, description, prices (COP)
- **Images**: Organized by color (max 20/color)
- **Categories**: Women, Men, Kids
- **Metadata**: Site, timestamp, canonical URL

### 🔍 Ethical Considerations
- Respects robots.txt: ✅
- Rate limiting implemented: ✅
- Public data only: ✅
- Transparent user agent: ✅

### 🎯 Next Steps
- [ ] Monitor performance in production
- [ ] Consider expansion to other regions
- [ ] Optimize selectors based on site changes
```

## 🐛 Reporting Bugs

### Issue Types

#### 🕷️ **Spider Bug**
```markdown
**Title:** [BUG] Zara spider fails to extract discounted prices

**Description:**
The Zara spider does not correctly extract prices when discounts are active.

**Steps to reproduce:**
1. Run: `python control_scraper.py --spider zara --url "URL_WITH_DISCOUNT"`
2. Check the `current_price` field in the output
3. Observe that it is empty

**Expected behavior:**
It should extract both the original price and the discounted price.

**Environment:**
- OS: Windows 10
- Python Version: 3.11.5
- Scrapy Version: 2.13.2
- Selenium Version: 4.33.0

**Logs:**
`​`​`
ERROR: Error extracting prices: NoSuchElementException
`​`​`

**Proposed solution:**
Update CSS selectors for the new price elements.
```

#### 🐳 **Infrastructure Bug**
```markdown
**Title:** [INFRA] Chrome nodes run out of memory

**Description:**
Chrome containers run out of memory after ~100 products.

**Symptoms:**
- Selenium timeouts
- Containers restarting
- Swap memory at 100%

**Configuration:**
`​`​`yaml
chrome:
  shm_size: '2g'
  deploy:
    resources:
      limits:
        memory: 4G
`​`​`

**Proposed solution:**
Increase memory and configure automatic session cleanup.
```

## ❓ Getting Help

### 📞 Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For general questions
- **Email**: stylos-dev@example.com for private inquiries

### 🆘 Frequently Asked Questions

#### **Q: How do I debug a spider that isn't working?**
```bash
# Run with maximum debug level
scrapy crawl zara -L DEBUG -s LOG_FILE=debug.log

# Use scrapy shell to test selectors
scrapy shell "https://www.zara.com/us/en/product"
>>> response.css('h1.product-title::text').get()
```

#### **Q: How do I update selectors when a site changes?**
```python
# 1. Use browser developer tools
# 2. Test selectors in scrapy shell
# 3. Implement alternative selectors
SELECTORS = {
    'name': [
        'h1.product-title',      # Main selector
        'h1.title',              # Alternative selector
        '.product-name h1'       # Fallback selector
    ]
}

# 4. Use the first one that works
def _safe_extract_text(self, selectors):
    for selector in selectors:
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            continue
    return ""
```

#### **Q: How do I handle rate limiting?**
```python
# In settings.py
DOWNLOAD_DELAY = 2  # 2 seconds between requests
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # Randomize ±50%

# In spider
def start_requests(self):
    for url in self.start_urls:
        yield scrapy.Request(
            url=url,
            meta={'download_delay': 3}  # Override delay for this request
        )
```

### 🎓 Learning Resources

- **Scrapy Documentation**: https://docs.scrapy.org/
- **Selenium Documentation**: https://selenium-python.readthedocs.io/
- **CSS Selectors**: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors
- **XPath Tutorial**: https://www.w3schools.com/xml/xpath_intro.asp

---

## 🎉 Thank You for Contributing!

Your contribution makes **Stylos Scrapers** better for the entire community.

**Ready to start?** 🚀

1.  **Fork** the repository
2.  **Create** your feature branch
3.  **Develop** with a love for clean code
4.  **Test** exhaustively
5.  **Document** your changes
6.  **Submit** your pull request

> "Well-written code is its own documentation." - Steve McConnell

---
**Maintained by:** Erik172 and the Stylos community 💙