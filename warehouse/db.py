import sqlite3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from .schema import Product, ProductCollection
import logging

logger = logging.getLogger(__name__)

class WarehouseManager:
    """Manages data storage in SQLite and Parquet formats."""
    
    def __init__(self, db_path: str = "data/warehouse.db", parquet_path: str = "data/warehouse.parquet"):
        """
        Initialize the warehouse manager.
        
        Args:
            db_path: Path to SQLite database file
            parquet_path: Path to Parquet file
        """
        self.db_path = db_path
        self.parquet_path = parquet_path
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with products table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price_min REAL,
                    price_max REAL,
                    currency TEXT DEFAULT 'USD',
                    moq INTEGER,
                    unit TEXT,
                    supplier_name TEXT,
                    supplier_rating REAL,
                    supplier_location TEXT,
                    verified_supplier BOOLEAN,
                    response_rate REAL,
                    certifications TEXT,  -- JSON array
                    keywords TEXT,        -- JSON array
                    category TEXT,
                    subcategory TEXT,
                    description TEXT,
                    listing_url TEXT,
                    scraped_at REAL,
                    
                    -- Geo enrichment fields
                    supplier_city TEXT,
                    supplier_state TEXT,
                    supplier_country TEXT,
                    supplier_region TEXT,
                    
                    -- NLP enrichment fields
                    entities TEXT,        -- JSON array
                    
                    -- Price normalization tracking
                    original_currency TEXT,
                    original_price_min REAL,
                    original_price_max REAL,
                    original_unit TEXT,
                    currency_conversion_failed BOOLEAN
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_location ON products(supplier_location)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_range ON products(price_min, price_max)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_at ON products(scraped_at)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def save_products(self, products: List[Dict[str, Any]]) -> bool:
        """
        Save products to both SQLite and Parquet storage.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not products:
            logger.warning("No products to save")
            return False
        
        try:
            # Validate products using Pydantic models
            validated_products = []
            for product_dict in products:
                try:
                    product = Product(**product_dict)
                    validated_products.append(product.dict())
                except Exception as e:
                    logger.warning(f"Failed to validate product {product_dict.get('product_id', 'unknown')}: {e}")
            
            if not validated_products:
                logger.error("No valid products to save after validation")
                return False
            
            # Save to SQLite
            sqlite_success = self._save_to_sqlite(validated_products)
            
            # Save to Parquet
            parquet_success = self._save_to_parquet(validated_products)
            
            if sqlite_success and parquet_success:
                logger.info(f"Successfully saved {len(validated_products)} products to warehouse")
                return True
            else:
                logger.error("Failed to save products to one or more storage formats")
                return False
                
        except Exception as e:
            logger.error(f"Error saving products to warehouse: {e}")
            return False
    
    def _save_to_sqlite(self, products: List[Dict[str, Any]]) -> bool:
        """
        Save products to SQLite database.
        
        Args:
            products: List of validated product dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for product in products:
                    # Convert list fields to JSON strings
                    product_copy = product.copy()
                    for field in ['certifications', 'keywords', 'entities']:
                        if field in product_copy and isinstance(product_copy[field], list):
                            product_copy[field] = json.dumps(product_copy[field])
                    
                    # Prepare SQL query
                    columns = ', '.join(product_copy.keys())
                    placeholders = ', '.join(['?' for _ in product_copy])
                    values = tuple(product_copy.values())
                    
                    # Use INSERT OR REPLACE to handle duplicates
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO products ({columns})
                        VALUES ({placeholders})
                    """, values)
                
                conn.commit()
                logger.info(f"Saved {len(products)} products to SQLite database")
                return True
                
        except Exception as e:
            logger.error(f"Error saving to SQLite: {e}")
            return False
    
    def _save_to_parquet(self, products: List[Dict[str, Any]]) -> bool:
        """
        Save products to Parquet file.
        
        Args:
            products: List of validated product dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(products)
            
            # Convert list fields to JSON strings for Parquet storage
            for field in ['certifications', 'keywords', 'entities']:
                if field in df.columns:
                    df[field] = df[field].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
            
            # Save to Parquet
            table = pa.Table.from_pandas(df)
            pq.write_table(table, self.parquet_path)
            
            logger.info(f"Saved {len(products)} products to Parquet file")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to Parquet: {e}")
            return False
    
    def load_products(self, limit: Optional[int] = None, 
                     category: Optional[str] = None,
                     min_price: Optional[float] = None,
                     max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Load products from SQLite database with optional filtering.
        
        Args:
            limit: Maximum number of products to return
            category: Filter by category
            min_price: Filter by minimum price
            max_price: Filter by maximum price
            
        Returns:
            List of product dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build query
                query = "SELECT * FROM products WHERE 1=1"
                params = []
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                if min_price is not None:
                    query += " AND price_min >= ?"
                    params.append(min_price)
                
                if max_price is not None:
                    query += " AND price_max <= ?"
                    params.append(max_price)
                
                query += " ORDER BY scraped_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                # Execute query
                df = pd.read_sql_query(query, conn, params=params)
                
                # Convert JSON fields back to lists
                for field in ['certifications', 'keywords', 'entities']:
                    if field in df.columns:
                        df[field] = df[field].apply(
                            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else x
                        )
                
                # Convert to list of dictionaries
                products = df.to_dict('records')
                
                logger.info(f"Loaded {len(products)} products from warehouse")
                return products
                
        except Exception as e:
            logger.error(f"Error loading products from warehouse: {e}")
            return []
    
    def get_product_count(self) -> int:
        """
        Get total number of products in the warehouse.
        
        Returns:
            Number of products
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products")
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics about the warehouse.
        
        Returns:
            Dictionary with warehouse statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total count
                cursor.execute("SELECT COUNT(*) FROM products")
                stats['total_products'] = cursor.fetchone()[0]
                
                # Count by category
                cursor.execute("""
                    SELECT category, COUNT(*) 
                    FROM products 
                    WHERE category IS NOT NULL 
                    GROUP BY category
                """)
                stats['by_category'] = dict(cursor.fetchall())
                
                # Price statistics
                cursor.execute("""
                    SELECT 
                        AVG(price_min) as avg_min_price,
                        AVG(price_max) as avg_max_price,
                        MIN(price_min) as min_price,
                        MAX(price_max) as max_price
                    FROM products 
                    WHERE price_min IS NOT NULL AND price_max IS NOT NULL
                """)
                price_stats = cursor.fetchone()
                if price_stats:
                    stats['price_statistics'] = {
                        'avg_min_price': price_stats[0],
                        'avg_max_price': price_stats[1],
                        'min_price': price_stats[2],
                        'max_price': price_stats[3]
                    }
                
                # Supplier statistics
                cursor.execute("""
                    SELECT 
                        AVG(supplier_rating) as avg_rating,
                        AVG(response_rate) as avg_response_rate,
                        SUM(CASE WHEN verified_supplier THEN 1 ELSE 0 END) as verified_count
                    FROM products 
                    WHERE supplier_rating IS NOT NULL
                """)
                supplier_stats = cursor.fetchone()
                if supplier_stats:
                    stats['supplier_statistics'] = {
                        'avg_rating': supplier_stats[0],
                        'avg_response_rate': supplier_stats[1],
                        'verified_suppliers': supplier_stats[2]
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting warehouse statistics: {e}")
            return {}

# Convenience functions for external use
def save_products_to_warehouse(products: List[Dict[str, Any]], 
                              db_path: str = "data/warehouse.db",
                              parquet_path: str = "data/warehouse.parquet") -> bool:
    """
    Save products to warehouse using default WarehouseManager.
    
    Args:
        products: List of product dictionaries
        db_path: Path to SQLite database
        parquet_path: Path to Parquet file
        
    Returns:
        True if successful, False otherwise
    """
    warehouse = WarehouseManager(db_path, parquet_path)
    return warehouse.save_products(products)

def load_products_from_warehouse(limit: Optional[int] = None,
                                category: Optional[str] = None,
                                min_price: Optional[float] = None,
                                max_price: Optional[float] = None,
                                db_path: str = "data/warehouse.db") -> List[Dict[str, Any]]:
    """
    Load products from warehouse using default WarehouseManager.
    
    Args:
        limit: Maximum number of products to return
        category: Filter by category
        min_price: Filter by minimum price
        max_price: Filter by maximum price
        db_path: Path to SQLite database
        
    Returns:
        List of product dictionaries
    """
    warehouse = WarehouseManager(db_path)
    return warehouse.load_products(limit, category, min_price, max_price)
