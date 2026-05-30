from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class Product(BaseModel):
    """Pydantic model for product data validation."""
    
    # Core identification
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    
    # Pricing information
    price_min: Optional[float] = Field(None, description="Minimum price in USD")
    price_max: Optional[float] = Field(None, description="Maximum price in USD")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    
    # Order information
    moq: Optional[int] = Field(None, description="Minimum order quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    
    # Supplier information
    supplier_name: Optional[str] = Field(None, description="Supplier name")
    supplier_rating: Optional[float] = Field(None, ge=0, le=5, description="Supplier rating (0-5)")
    supplier_location: Optional[str] = Field(None, description="Supplier location (city, state, country)")
    verified_supplier: Optional[bool] = Field(None, description="Whether supplier is verified")
    response_rate: Optional[float] = Field(None, ge=0, le=100, description="Supplier response rate percentage")
    
    # Additional attributes
    certifications: Optional[List[str]] = Field(default_factory=list, description="List of certifications")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Extracted keywords")
    category: Optional[str] = Field(None, description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    description: Optional[str] = Field(None, description="Product description")
    
    # Metadata
    listing_url: Optional[str] = Field(None, description="URL of product listing")
    scraped_at: Optional[float] = Field(None, description="Unix timestamp of when data was scraped")
    
    # Geographical enrichment (added by geo_enricher)
    supplier_city: Optional[str] = Field(None, description="Supplier city")
    supplier_state: Optional[str] = Field(None, description="Supplier state")
    supplier_country: Optional[str] = Field(None, description="Supplier country")
    supplier_region: Optional[str] = Field(None, description="Supplier region")
    
    # NLP enrichment (added by nlp_enricher)
    entities: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Named entities from description")
    
    # Price normalization tracking
    original_currency: Optional[str] = Field(None, description="Original currency before normalization")
    original_price_min: Optional[float] = Field(None, description="Original minimum price")
    original_price_max: Optional[float] = Field(None, description="Original maximum price")
    original_unit: Optional[str] = Field(None, description="Original unit before normalization")
    currency_conversion_failed: Optional[bool] = Field(None, description="Whether currency conversion failed")
    
    @validator('price_min', 'price_max')
    def validate_prices(cls, v):
        """Validate that prices are non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v
    
    @validator('price_max')
    def validate_price_range(cls, v, values):
        """Validate that price_max >= price_min if both are provided."""
        if v is not None and values.get('price_min') is not None:
            if v < values['price_min']:
                raise ValueError('Price maximum must be greater than or equal to price minimum')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code format."""
        if v and not re.match(r'^[A-Z]{3}$', v):
            raise ValueError('Currency must be a valid 3-letter ISO 4217 code')
        return v.upper() if v else v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.timestamp()
        }
        json_schema_extra = {
            "example": {
                "product_id": "prod_12345",
                "name": "Industrial CNC Machine",
                "price_min": 5000.0,
                "price_max": 8000.0,
                "currency": "USD",
                "moq": 1,
                "unit": "pieces",
                "supplier_name": "ABC Manufacturing Ltd.",
                "supplier_rating": 4.5,
                "supplier_location": "Mumbai, Maharashtra, India",
                "verified_supplier": True,
                "response_rate": 85.0,
                "certifications": ["ISO 9001", "CE"],
                "keywords": ["cnc", "machine", "industrial", "manufacturing"],
                "category": "Industrial Machinery",
                "subcategory": "CNC Machines",
                "description": "High precision CNC machine for metal cutting operations",
                "listing_url": "https://example.com/product/prod_12345",
                "scraped_at": 1640995200.0
            }
        }

# Collection of products
class ProductCollection(BaseModel):
    """Collection of product records."""
    products: List[Product] = Field(default_factory=list, description="List of product objects")
    count: int = Field(..., description="Number of products in collection")
    
    @validator('count')
    def validate_count(cls, v, values):
        """Validate that count matches the number of products."""
        products = values.get('products', [])
        if v != len(products):
            raise ValueError('Count must match the number of products')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "products": [
                    {
                        "product_id": "prod_12345",
                        "name": "Industrial CNC Machine",
                        "price_min": 5000.0,
                        "price_max": 8000.0,
                        "currency": "USD",
                        "moq": 1,
                        "unit": "pieces",
                        "supplier_name": "ABC Manufacturing Ltd.",
                        "supplier_rating": 4.5,
                        "supplier_location": "Mumbai, Maharashtra, India",
                        "verified_supplier": True,
                        "response_rate": 85.0,
                        "certifications": ["ISO 9001", "CE"],
                        "keywords": ["cnc", "machine", "industrial", "manufacturing"],
                        "category": "Industrial Machinery",
                        "subcategory": "CNC Machines",
                        "description": "High precision CNC machine for metal cutting operations",
                        "listing_url": "https://example.com/product/prod_12345",
                        "scraped_at": 1640995200.0
                    }
                ],
                "count": 1
            }
        }
