import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def create_extractor(provider: Optional[str] = None, **kwargs) -> "AIExtractor":
    """
    Factory function to create the appropriate AI extractor.
    
    Auto-detection logic:
      1. If AI_PROVIDER env is set, use that.
      2. If ANTHROPIC_API_KEY env is set, use 'anthropic'.
      3. Otherwise default to 'ollama' (no API key needed).
    
    Args:
        provider: Override provider ('anthropic' | 'ollama')
        **kwargs: Passed through to the extractor constructor.
    
    Returns:
        A configured AIExtractor instance.
    """
    provider = provider or os.getenv("AI_PROVIDER", "")
    if not provider and os.getenv("ANTHROPIC_API_KEY"):
        provider = "anthropic"
    if not provider:
        provider = "ollama"

    if provider == "anthropic":
        return AnthropicExtractor(**kwargs)
    elif provider == "ollama":
        return OllamaExtractor(**kwargs)
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Use 'anthropic' or 'ollama'.")


class AIExtractor:
    """Unified interface for AI-based product data extraction."""

    PRODUCT_SCHEMA = {
        "product_id": "string (unique identifier)",
        "name": "string (product name)",
        "price_min": "number (minimum price in USD, null if not available)",
        "price_max": "number (maximum price in USD, null if not available)",
        "currency": "string (ISO 4217 currency code, e.g., USD, EUR)",
        "moq": "number (minimum order quantity)",
        "unit": "string (unit of measurement, e.g., pieces, kg, liters)",
        "supplier_name": "string (name of the supplier)",
        "supplier_rating": "number (rating out of 5, null if not available)",
        "supplier_location": "string (city, state, country)",
        "verified_supplier": "boolean (whether supplier is verified)",
        "response_rate": "number (percentage response rate, null if not available)",
        "certifications": "array of strings (list of certifications)",
        "keywords": "array of strings (relevant keywords)",
        "category": "string (product category)",
        "subcategory": "string (product subcategory)",
        "description": "string (product description)",
        "listing_url": "string (URL of the product listing)",
        "scraped_at": "number (timestamp of when data was scraped)",
    }

    def _build_extraction_prompt(self, html_content: str, url: str) -> str:
        limited_html = html_content[:50000] if len(html_content) > 50000 else html_content
        return f"""
Extract structured product information from the following HTML content of an e-commerce product listing.

HTML Content:
```html
{limited_html}
```

URL: {url}

Please extract the following fields and return them as a valid JSON object:
{json.dumps(self.PRODUCT_SCHEMA, indent=2)}

Important guidelines:
1. Extract prices in USD if possible. If prices are in other currencies, convert them to USD using approximate rates (1 USD = 83 INR, 1 USD = 7.2 CNY).
2. For price ranges, extract both min and max values. For single prices, set both min and max to the same value.
3. If a field is not found or not applicable, use null.
4. Ensure the product_id is unique - you can generate it based on the URL or content if not explicitly present.
5. Extract relevant keywords from the product name and description.
6. Categorize the product into one of these categories: Industrial Machinery, Electronics, Textiles, Chemicals, Agriculture.
7. Set scraped_at to the current Unix timestamp ({time.time():.0f}).
8. Return ONLY the JSON object, no additional text or explanations.

JSON Output:
"""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}")
            return {"error": "Failed to parse extraction result", "raw_response": response_text[:500]}

    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated = {}
        for field in ['product_id', 'name', 'currency', 'unit', 'supplier_name',
                       'supplier_location', 'description', 'listing_url', 'category', 'subcategory']:
            v = data.get(field)
            validated[field] = str(v).strip() if v is not None else None

        for field in ['price_min', 'price_max', 'moq', 'supplier_rating', 'response_rate']:
            v = data.get(field)
            if v is not None:
                try:
                    validated[field] = float(v)
                except (ValueError, TypeError):
                    validated[field] = None
            else:
                validated[field] = None

        verified = data.get('verified_supplier')
        if isinstance(verified, bool):
            validated['verified_supplier'] = verified
        elif isinstance(verified, str):
            validated['verified_supplier'] = verified.lower() in ('true', 'yes', '1')
        else:
            validated['verified_supplier'] = False

        for field in ['certifications', 'keywords']:
            v = data.get(field)
            if isinstance(v, list):
                validated[field] = [str(item).strip() for item in v if item is not None]
            elif isinstance(v, str):
                validated[field] = [item.strip() for item in v.split(',') if item.strip()]
            else:
                validated[field] = []

        validated['scraped_at'] = data.get('scraped_at', time.time())

        if validated.get('price_min') is not None and validated.get('price_max') is not None:
            if validated['price_min'] > validated['price_max']:
                validated['price_min'], validated['price_max'] = validated['price_max'], validated['price_min']
        elif validated.get('price_min') is not None:
            validated['price_max'] = validated['price_min']
        elif validated.get('price_max') is not None:
            validated['price_min'] = validated['price_max']

        return validated

    def extract_product_data(self, html_content: str, url: str = "") -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement extract_product_data")


class AnthropicExtractor(AIExtractor):
    """Extractor that uses Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        import anthropic
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var.")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def extract_product_data(self, html_content: str, url: str = "") -> Dict[str, Any]:
        prompt = self._build_extraction_prompt(html_content, url)
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                system="You are an expert data extraction specialist. Extract structured product information from HTML e-commerce pages and return valid JSON.",
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = message.content[0].text
            extracted = self._parse_response(response_text)
            return self._validate_and_clean_data(extracted)
        except Exception as e:
            logger.error(f"Anthropic extraction error: {e}")
            return {"error": str(e), "listing_url": url, "scraped_at": time.time()}


class OllamaExtractor(AIExtractor):
    """Extractor that uses a local Ollama model (e.g. Qwen 2.5)."""

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.api_url = f"{self.base_url}/api/chat"
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))

    def extract_product_data(self, html_content: str, url: str = "") -> Dict[str, Any]:
        prompt = self._build_extraction_prompt(html_content, url)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert data extraction specialist. Extract structured product information from HTML e-commerce pages and return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            body = resp.json()
            response_text = body.get("message", {}).get("content", "")
            if not response_text:
                logger.error(f"Ollama returned empty content. Full response: {body}")
                return {"error": "Ollama returned empty content", "listing_url": url, "scraped_at": time.time()}
            extracted = self._parse_response(response_text)
            return self._validate_and_clean_data(extracted)
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
            return {"error": "Ollama not reachable", "listing_url": url, "scraped_at": time.time()}
        except Exception as e:
            logger.error(f"Ollama extraction error: {e}")
            return {"error": str(e), "listing_url": url, "scraped_at": time.time()}
