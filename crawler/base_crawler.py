import abc
import time
import random
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging
from typing import Optional, Dict, Any
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class BaseCrawler(abc.ABC):
    """Abstract base class for web crawlers."""
    
    def __init__(self, base_url: str, rate_limit: float = 1.0, max_retries: int = 3):
        """
        Initialize the crawler.
        
        Args:
            base_url: Base URL of the target site
            rate_limit: Minimum delay between requests (seconds)
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.ua = UserAgent()
        self.session = requests.Session()
        self.robot_parser = None
        self.last_request_time = 0
        
        # Initialize robots.txt parser
        self._setup_robots_txt()
    
    def _setup_robots_txt(self):
        """Setup robots.txt parser for the base URL."""
        try:
            parsed_url = urlparse(self.base_url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            self.robot_parser = RobotFileParser()
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
        except Exception as e:
            logger.warning(f"Could not load robots.txt for {self.base_url}: {e}")
            self.robot_parser = None
    
    def _respect_robots_txt(self, url: str) -> bool:
        """Check if we're allowed to fetch the URL according to robots.txt."""
        if not self.robot_parser:
            return True
        return self.robot_parser.can_fetch("*", url)
    
    def _adaptive_rate_limit(self):
        """Implement adaptive rate limiting with jitter."""
        elapsed = time.time() - self.last_request_time
        sleep_time = max(0, self.rate_limit - elapsed)
        # Add jitter to avoid thundering herd
        sleep_time += random.uniform(0, 0.5)
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _get_with_retry(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Fetch URL with retry logic and exponential backoff.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to requests.get
            
        Returns:
            Response object or None if failed
        """
        if not self._respect_robots_txt(url):
            logger.warning(f"Robots.txt disallows fetching {url}")
            return None
            
        headers = kwargs.pop('headers', {})
        headers.update({'User-Agent': self.ua.random})
        
        for attempt in range(self.max_retries):
            try:
                self._adaptive_rate_limit()
                response = self.session.get(url, headers=headers, timeout=10, **kwargs)
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limited (429) for {url}. Waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    
        return None
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a page.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        response = self._get_with_retry(url)
        if response is None:
            return None
            
        return BeautifulSoup(response.content, 'html.parser')
    
    @abc.abstractmethod
    def search_products(self, query: str, max_pages: int = 5) -> list[Dict[str, Any]]:
        """
        Search for products on the site.
        
        Args:
            query: Search query string
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product dictionaries
        """
        pass
    
    @abc.abstractmethod
    def parse_product_listing(self, soup: BeautifulSoup) -> list[Dict[str, Any]]:
        """
        Parse product listings from a search results page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of product dictionaries (basic info)
        """
        pass
    
    @abc.abstractmethod
    def parse_product_detail(self, soup: BeautifulSoup, product_id: str) -> Dict[str, Any]:
        """
        Parse detailed product information from a product page.
        
        Args:
            soup: BeautifulSoup object of the product page
            product_id: Unique identifier for the product
            
        Returns:
            Dictionary with detailed product information
        """
        pass
