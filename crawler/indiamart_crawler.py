from .base_crawler import BaseCrawler
import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)

class IndiaMARTCrawler(BaseCrawler):
    """IndiaMART-specific crawler."""
    
    def __init__(self, rate_limit: float = 2.0):
        super().__init__("https://www.indiamart.com", rate_limit=rate_limit)
    
    def search_products(self, query: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products on IndiaMART.
        
        Args:
            query: Search query string
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product dictionaries
        """
        products = []
        for page in range(1, max_pages + 1):
            # IndiaMART search URL pattern
            search_url = f"https://www.indiamart.com/search.mp?ss={query}&page={page}"
            soup = self.fetch_page(search_url)
            if soup is None:
                logger.warning(f"Failed to fetch page {page} for query '{query}'")
                break
                
            page_products = self.parse_product_listing(soup)
            if not page_products:
                logger.info(f"No products found on page {page}, stopping")
                break
                
            products.extend(page_products)
            logger.info(f"Found {len(page_products)} products on page {page}")
            
        return products
    
    def parse_product_listing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse product listings from IndiaMART search results.
        
        Args:
            soup: BeautifulSoup object of the search results page
            
        Returns:
            List of product dictionaries with basic info
        """
        products = []
        # IndiaMART product cards are typically in divs with class 'card' or similar
        # Note: These selectors are examples and would need to be adjusted based on actual site structure
        product_cards = soup.find_all('div', class_=re.compile(r'card|product'))
        
        for card in product_cards:
            try:
                # Extract basic product info
                title_elem = card.find('a', class_=re.compile(r'title|name'))
                title = title_elem.get_text(strip=True) if title_elem else None
                product_url = title_elem.get('href') if title_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = urljoin(self.base_url, product_url)
                
                # Extract price if available
                price_elem = card.find('span', class_=re.compile(r'price'))
                price_text = price_elem.get_text(strip=True) if price_elem else None
                
                # Extract product ID from URL or data attribute
                product_id = None
                if product_url:
                    # Try to extract ID from URL
                    id_match = re.search(r'/product/([^/]+)', product_url)
                    if id_match:
                        product_id = id_match.group(1)
                    else:
                        # Fallback to using a hash of the URL
                        product_id = str(hash(product_url))
                
                product = {
                    'product_id': product_id,
                    'name': title,
                    'listing_url': product_url,
                    'price_raw': price_text,
                    'source': 'indiamart'
                }
                products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing product card: {e}")
                continue
                
        return products
    
    def parse_product_detail(self, soup: BeautifulSoup, product_id: str) -> Dict[str, Any]:
        """
        Parse detailed product information from IndiaMART product page.
        
        Args:
            soup: BeautifulSoup object of the product page
            product_id: Unique identifier for the product
            
        Returns:
            Dictionary with detailed product information
        """
        detail = {
            'product_id': product_id,
            'source': 'indiamart'
        }
        
        try:
            # Product name
            name_elem = soup.find('h1') or soup.find('div', class_=re.compile(r'product-name|title'))
            detail['name'] = name_elem.get_text(strip=True) if name_elem else None
            
            # Price
            price_elem = soup.find('span', class_=re.compile(r'price|amount'))
            price_text = price_elem.get_text(strip=True) if price_elem else None
            detail['price_raw'] = price_text
            
            # MOQ (Minimum Order Quantity)
            moq_elem = soup.find('text', string=re.compile(r'MOQ|Minimum Order', re.I))
            if moq_elem:
                moq_text = moq_elem.find_next().get_text(strip=True) if moq_elem.find_next() else moq_elem.get_text(strip=True)
                detail['moq_raw'] = moq_text
            
            # Unit
            unit_elem = soup.find('text', string=re.compile(r'Unit|Packaging', re.I))
            if unit_elem:
                unit_text = unit_elem.find_next().get_text(strip=True) if unit_elem.find_next() else unit_elem.get_text(strip=True)
                detail['unit'] = unit_text
            
            # Supplier name
            supplier_elem = soup.find('a', class_=re.compile(r'supplier|company'))
            detail['supplier_name'] = supplier_elem.get_text(strip=True) if supplier_elem else None
            
            # Supplier location
            location_elem = soup.find('span', class_=re.compile(r'location|city'))
            detail['supplier_location_raw'] = location_elem.get_text(strip=True) if location_elem else None
            
            # Description
            desc_elem = soup.find('div', class_=re.compile(r'description|about'))
            detail['description'] = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Certifications
            cert_elem = soup.find('div', class_=re.compile(r'certification|badge'))
            detail['certifications_raw'] = cert_elem.get_text(strip=True) if cert_elem else None
            
            # Scraped timestamp
            detail['scraped_at'] = time.time()
            
        except Exception as e:
            logger.warning(f"Error parsing product detail for {product_id}: {e}")
            
        return detail
