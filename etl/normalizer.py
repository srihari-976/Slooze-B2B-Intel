import logging
from typing import Dict, Any, Optional
from forex_python.converter import CurrencyRates
import re

logger = logging.getLogger(__name__)

class Normalizer:
    """Handles price normalization and unit standardization."""
    
    def __init__(self, target_currency: str = "USD"):
        """
        Initialize the normalizer.
        
        Args:
            target_currency: Target currency for price normalization (default: USD)
        """
        self.target_currency = target_currency.upper()
        self.currency_rates = CurrencyRates()
        
        # Common currency symbols to ISO codes mapping
        self.currency_symbols = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',  # Could be JPY or CNY, but we'll assume JPY for now
            '₹': 'INR',
            '¥': 'CNY',  # Chinese Yuan
        }
        
        # Common unit variations mapping to standard units
        self.unit_mappings = {
            # Weight/mass
            'kg': 'kg',
            'kgs': 'kg',
            'kilogram': 'kg',
            'kilograms': 'kg',
            'g': 'grams',
            'gram': 'grams',
            'grams': 'grams',
            'mg': 'milligrams',
            'milligram': 'milligrams',
            'milligrams': 'milligrams',
            'lb': 'pounds',
            'lbs': 'pounds',
            'pound': 'pounds',
            'pounds': 'pounds',
            'oz': 'ounces',
            'ounce': 'ounces',
            'ounces': 'ounces',
            
            # Length/distance
            'meter': 'meters',
            'meters': 'meters',
            'm': 'meters',
            'cm': 'centimeters',
            'centimeter': 'centimeters',
            'centimeters': 'centimeters',
            'mm': 'millimeters',
            'millimeter': 'millimeters',
            'millimeters': 'millimeters',
            'km': 'kilometers',
            'kilometer': 'kilometers',
            'kilometers': 'kilometers',
            'inch': 'inches',
            'inches': 'inches',
            'in': 'inches',
            'foot': 'feet',
            'feet': 'feet',
            'ft': 'feet',
            'yard': 'yards',
            'yards': 'yards',
            'yd': 'yards',
            
            # Volume
            'liter': 'liters',
            'liters': 'liters',
            'l': 'liters',
            'ml': 'milliliters',
            'milliliter': 'milliliters',
            'milliliters': 'milliliters',
            'gallon': 'gallons',
            'gallons': 'gallons',
            'gal': 'gallons',
            'quart': 'quarts',
            'quarts': 'quarts',
            'qt': 'quarts',
            'pint': 'pints',
            'pints': 'pints',
            'pt': 'pints',
            
            # Area
            'square meter': 'square meters',
            'square meters': 'square meters',
            'sqm': 'square meters',
            'm2': 'square meters',
            'square foot': 'square feet',
            'square feet': 'square feet',
            'sqft': 'square feet',
            'ft2': 'square feet',
            'acre': 'acres',
            'acres': 'acres',
            
            # Count
            'piece': 'pieces',
            'pieces': 'pieces',
            'pc': 'pieces',
            'pcs': 'pieces',
            'unit': 'units',
            'units': 'units',
            'set': 'sets',
            'sets': 'sets',
            'pair': 'pairs',
            'pairs': 'pairs',
            'box': 'boxes',
            'boxes': 'boxes',
            'pallet': 'pallets',
            'pallets': 'pallets',
            'roll': 'rolls',
            'rolls': 'rolls',
            'sheet': 'sheets',
            'sheets': 'sheets',
            'kg': 'kg',
            'ton': 'tons',
            'tons': 'tons',
            'tonne': 'tons',
            'tonnes': 'tons'
        }
    
    def normalize_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a product record (price to target currency, standardize units).
        
        Args:
            product: Product dictionary to normalize
            
        Returns:
            Normalized product dictionary
        """
        normalized = product.copy()
        
        # Normalize prices
        normalized = self._normalize_prices(normalized)
        
        # Normalize unit
        normalized = self._normalize_unit(normalized)
        
        return normalized
    
    def _normalize_prices(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Convert prices to target currency."""
        # Extract price fields
        price_min = product.get('price_min')
        price_max = product.get('price_max')
        currency = product.get('currency')
        
        # If no price data, return as-is
        if price_min is None and price_max is None:
            return product
        
        # If currency is already target currency, no conversion needed
        if currency and currency.upper() == self.target_currency:
            return product
        
        # Determine source currency
        source_currency = self._extract_currency_code(currency) if currency else 'USD'
        
        # If source currency is same as target, no conversion
        if source_currency.upper() == self.target_currency:
            return product
        
        try:
            # Convert prices
            if price_min is not None:
                price_min_usd = self._convert_currency(price_min, source_currency, self.target_currency)
                product['price_min'] = round(price_min_usd, 2)
            
            if price_max is not None:
                price_max_usd = self._convert_currency(price_max, source_currency, self.target_currency)
                product['price_max'] = round(price_max_usd, 2)
            
            # Update currency to target
            product['currency'] = self.target_currency
            
            # Add original currency info for reference
            product['original_currency'] = currency
            product['original_price_min'] = price_min
            product['original_price_max'] = price_max
            
        except Exception as e:
            logger.warning(f"Failed to convert currency {source_currency} to {self.target_currency}: {e}")
            # If conversion fails, keep original values but mark as unconverted
            product['currency_conversion_failed'] = True
        
        return product
    
    def _extract_currency_code(self, currency_input: Any) -> str:
        """Extract ISO currency code from various currency representations."""
        if not currency_input:
            return 'USD'
        
        currency_str = str(currency_input).strip().upper()
        
        # If it's already a valid ISO code (3 letters)
        if len(currency_str) == 3 and currency_str.isalpha():
            return currency_str
        
        # Check if it's a currency symbol
        if currency_str in self.currency_symbols:
            return self.currency_symbols[currency_str]
        
        # Handle common currency names
        currency_names = {
            'US DOLLAR': 'USD',
            'USD': 'USD',
            'DOLLAR': 'USD',
            'EURO': 'EUR',
            'EUR': 'EUR',
            'BRITISH POUND': 'GBP',
            'GBP': 'GBP',
            'POUND': 'GBP',
            'JAPANESE YEN': 'JPY',
            'JPY': 'JPY',
            'YEN': 'JPY',
            'INDIAN RUPEE': 'INR',
            'INR': 'INR',
            'RUPEE': 'INR',
            'CHINESE YUAN': 'CNY',
            'CNY': 'CNY',
            'YUAN': 'CNY'
        }
        
        return currency_names.get(currency_str, 'USD')
    
    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount from one currency to another."""
        if from_currency == to_currency:
            return amount
        
        # Use forex-python to get conversion rate
        rate = self.currency_rates.get_rate(from_currency, to_currency)
        return amount * rate
    
    def _normalize_unit(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize unit representation."""
        unit = product.get('unit')
        
        if not unit:
            return product
        
        # Clean and standardize unit
        unit_clean = str(unit).strip().lower()
        
        # Remove extra spaces and punctuation
        unit_clean = re.sub(r'[^\w\s]', '', unit_clean)
        unit_clean = re.sub(r'\s+', ' ', unit_clean)
        
        # Map to standard unit if possible
        standard_unit = self.unit_mappings.get(unit_clean, unit_clean)
        
        if standard_unit != unit_clean:
            product['unit'] = standard_unit
            product['original_unit'] = unit
        
        return product
