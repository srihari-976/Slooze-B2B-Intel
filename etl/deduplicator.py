import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)

class Deduplicator:
    """Handles deduplication of product records using fuzzy matching."""
    
    def __init__(self, name_threshold: float = 0.85, supplier_threshold: float = 0.8):
        """
        Initialize the deduplicator.
        
        Args:
            name_threshold: Similarity threshold for product names (0-1)
            supplier_threshold: Similarity threshold for supplier names (0-1)
        """
        self.name_threshold = name_threshold
        self.supplier_threshold = supplier_threshold
    
    def deduplicate(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate products based on fuzzy matching of name and supplier.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            List of deduplicated product dictionaries
        """
        if not products:
            return []
        
        # Sort by scraped_at (newest first) to keep most recent duplicates
        sorted_products = sorted(products, 
                               key=lambda x: x.get('scraped_at', 0), 
                               reverse=True)
        
        deduplicated = []
        seen_signatures = []
        
        for product in sorted_products:
            is_duplicate = False
            product_signature = self._create_signature(product)
            
            for seen_sig in seen_signatures:
                if self._is_similar(product_signature, seen_sig):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(product)
                seen_signatures.append(product_signature)
        
        logger.info(f"Deduplicated {len(products)} products to {len(deduplicated)} unique products")
        return deduplicated
    
    def _create_signature(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Create a signature for comparison based on name and supplier."""
        # Normalize name for comparison
        name = product.get('name', '') or ''
        name = re.sub(r'\s+', ' ', name.lower().strip())
        
        # Normalize supplier name
        supplier = product.get('supplier_name', '') or ''
        supplier = re.sub(r'\s+', ' ', supplier.lower().strip())
        
        return {
            'name': name,
            'supplier': supplier
        }
    
    def _is_similar(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> bool:
        """Check if two signatures are similar based on thresholds."""
        name_similarity = SequenceMatcher(None, sig1['name'], sig2['name']).ratio()
        supplier_similarity = SequenceMatcher(None, sig1['supplier'], sig2['supplier']).ratio()
        
        # Consider duplicate if both name and supplier are similar above thresholds
        return (name_similarity >= self.name_threshold and 
                supplier_similarity >= self.supplier_threshold)
