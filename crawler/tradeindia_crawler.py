from .base_crawler import BaseCrawler
import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)

class TradeIndiaCrawler(BaseCrawler):
    """TradeIndia-specific crawler."""
    
    def __init__(self, rate_limit: float = 2.0):
        super().__init__("https://www.tradeindia.com", rate_limit=rate_limit)
    
    def search_products(self, query: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products on TradeIndia.
        
        Args:
            query: Search query string
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product dictionaries
        """
        products = []
        for page in range(1, max_pages + 1):
            # TradeIndia search URL pattern
            search_url = f"https://www.tradeindia.com/search.html?keyword={query}&page={page}"
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
        Parse product listings from TradeIndia search results.
        
        Args:
            soup: BeautifulSoup object of the search results page
            
        Returns:
            List of product dictionaries with basic info
        """
        products = []
        # TradeIndia product cards - adjust selectors based on actual site structure
        product_cards = soup.find_all('div', class_=re.compile(r'product|item|result'))
        
        for card in product_cards:
            try:
                # Extract basic product info
                title_elem = card.find('a', class_=re.compile(r'title|name|product-name'))
                title = title_elem.get_text(strip=True) if title_elem else None
                product_url = title_elem.get('href') if title_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = urljoin(self.base_url, product_url)
                
                # Extract price if available
                price_elem = card.find('span', class_=re.compile(r'price|amount|cost'))
                price_text = price_elem.get_text(strip=True) if price_elem else None
                
                # Extract product ID from URL or data attribute
                product_id = None
                if product_url:
                    # Try to extract ID from URL
                    id_match = re.search(r'/product/([^/]+)|/([^/]+)\.html', product_url)
                    if id_match:
                        product_id = id_match.group(1) if id_match.group(1) else id_match.group(2)
                    else:
                        # Fallback to using a hash of the URL
                        product_id = str(hash(product_url))
                
                product = {
                    'product_id': product_id,
                    'name': title,
                    'listing_url': product_url,
                    'price_raw': price_text,
                    'source': 'tradeindia'
                }
                products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing product card: {e}")
                continue
                
        return products
    
    def parse_product_detail(self, soup: BeautifulSoup, product_id: str) -> Dict[str, Any]:
        """
        Parse detailed product information from TradeIndia product page.
        
        Args:
            soup: BeautifulSoup object of the product page
            product_id: Unique identifier for the product
            
        Returns:
            Dictionary with detailed product information
        """
        detail = {
            'product_id': product_id,
            'source': 'tradeindia'
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
            moq_elem = soup.find(text=re.compile(r'MOQ|Minimum Order', re.I))
            if moq_elem:
                # Find the parent or next element that contains the value
                parent = moq_elem.parent if hasattr(moq_elem, 'parent') else None
                if parent:
                    moq_text = parent.get_text(strip=True)
                    # Extract just the value part (after the label)
                    if ':' in moq_text:
                        moq_text = moq_text.split(':', 1)[1].strip()
                    detail['moq_raw'] = moq_text
            
            # Unit
            unit_elem = soup.find(text=re.compile(r'Unit|Packaging', re.I))
            if unit_elem:
                parent = unit_elem.parent if hasattr(unit_elem, 'parent') else None
                if parent:
                    unit_text = parent.get_text(strip=True)
                    if ':' in unit_text:
                        unit_text = unit_text.split(':', 1)[1].strip()
                    detail['unit'] = unit_text
            
            # Supplier name
            supplier_elem = soup.find('a', class_=re.compile(r'supplier|company|seller'))
            detail['supplier_name'] = supplier_elem.get_text(strip=True) if supplier_elem else None
            
            # Supplier location
            location_elem = soup.find('span', class_=re.compile(r'location|city|address'))
            detail['supplier_location_raw'] = location_elem.get_text(strip=True) if location_elem else None
            
            # Description
            desc_elem = soup.find('div', class_=re.compile(r'description|about|details'))
            detail['description'] = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Certifications
            cert_elem = soup.find('div', class_=re.compile(r'certification|badge|approval'))
            detail['certifications_raw'] = cert_elem.get_text(strip=True) if cert_elem else None
            
            # Supplier rating
            rating_elem = soup.find('span', class_=re.compile(r'rating|score'))
            rating_text = rating_elem.get_text(strip=True) if rating_elem else None
            if rating_text:
                try:
                    detail['supplier_rating'] = float(rating_text)
                except ValueError:
                    detail['supplier_rating'] = None
            
            # Response rate
            response_elem = soup.find(text=re.compile(r'Response Rate', re.I))
            if response_elem:
                parent = response_elem.parent if hasattr(response_elem, 'parent') else None
                if parent:
                    response_text = parent.get_text(strip=True)
                    if ':' in response_text:
                        response_text = response_text.split(':', 1)[1].strip()
                    # Remove % sign if present
                    response_text = response_text.replace('%', '')
                    try:
                        detail['response_rate'] = float(response_text)
                    except ValueError:
                        detail['response_rate'] = None
            
            # Verified supplier badge
            verified_elem = soup.find(text=re.compile(r'Verified|Trusted', re.I))
            detail['verified_supplier'] = verified_elem is not None
            
            # Scraped timestamp
            detail['scraped_at'] = time.time()
            
        except Exception as e:
            logger.warning(f"Error parsing product detail for {product_id}: {e}")
            
        return detail
