import scrapy
from scrapy_playwright.page import PageMethod
import json
import os

class ZaraSpider(scrapy.Spider):
    name = "zara"
    allowed_domains = ["zara.com", "www.zara.com", "zara.net", "static.zara.net", "zara.com.co"]
    start_urls = [
        "https://www.zara.com/co/es/hombre-lino-l708.html?v1=2431961",
    ]
    
    async def start(self, response=None):
        page_methods = [PageMethod('wait_for_timeout', 3000),]
        
        # Agregar múltiples scrolls
        for i in range(10):  # Aumenté a 5 scrolls
            page_methods.extend([
                PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                PageMethod('wait_for_timeout', 2000),
            ])
        
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={'playwright': True, 'playwright_page_methods': page_methods}
            )

    async def parse(self, response):
        processed_urls = set()
        
        products_xpath = "//div[contains(@class, 'zds-carousel-item')] | //li[contains(@class, 'products-category-grid-block')]"
        
        products = response.xpath(products_xpath)
        
        for product in products:
            product_url = product.xpath(".//a/@href").get()
            print(product_url)
            if product_url and product_url not in processed_urls:
                processed_urls.add(product_url)
                yield scrapy.Request(
                    product_url,
                    callback=self.parse_product,
                )
            
    async def parse_product(self, response):
        # XPath para encontrar el script que contiene los datos del producto
        # Buscamos un <script> de tipo "application/ld+json" o que contenga "window.zara.viewPayload"
        json_script_xpath = "//script[@type='application/ld+json']/text()"
        json_script = response.xpath(json_script_xpath).get()
        
        # # Guardar el JSON en un archivo
        # with open(f'zara_product_{hash(response.url)}.json', 'w', encoding='utf-8') as f:
        #     f.write(json_script)
        
        with open(f'zara_product_{hash(response.url)}.html', 'w', encoding='utf-8') as f:
            f.write(response.text)