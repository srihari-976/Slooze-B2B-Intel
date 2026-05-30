import random
import time
from typing import List, Dict, Any
from faker import Faker
import uuid

fake = Faker()

class MockDataGenerator:
    """Generates realistic mock product data for testing and development."""
    
    def __init__(self):
        """Initialize the mock data generator with domain-specific data."""
        # Define categories and subcategories
        self.categories = {
            'Industrial Machinery': [
                'CNC Machines', 'Conveyor Systems', 'Industrial Robots', 
                'Pumps & Valves', 'Material Handling', 'Welding Equipment'
            ],
            'Electronics': [
                'Semiconductors', 'PCB Assembly', 'Electronic Components',
                'Consumer Electronics', 'Telecom Equipment', 'Industrial Electronics'
            ],
            'Textiles': [
                'Fabrics', 'Yarn & Thread', 'Home Textiles',
                'Technical Textiles', 'Apparel', 'Textile Machinery'
            ],
            'Chemicals': [
                'Industrial Chemicals', 'Polymers', 'Specialty Chemicals',
                'Agrochemicals', 'Pharmaceutical Chemicals', 'Adhesives'
            ],
            'Agriculture': [
                'Farm Equipment', 'Irrigation Systems', 'Seeds & Fertilizers',
                'Animal Feed', 'Agricultural Chemicals', 'Greenhouse Equipment'
            ]
        }
        
        # Currency options
        self.currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'INR']
        
        # Units of measurement
        self.units = [
            'pieces', 'kg', 'grams', 'liters', 'meters', 'square meters',
            'tons', 'boxes', 'pallets', 'pairs', 'sets', 'rolls'
        ]
        
        # Common certifications by category
        self.certifications = {
            'Industrial Machinery': ['ISO 9001', 'CE', 'OSHA Compliant', 'API Certified'],
            'Electronics': ['UL Listed', 'FCC Compliant', 'RoHS', 'CE', 'ISO 13485'],
            'Textiles': ['OEKO-TEX', 'GOTS', 'ISO 9001', 'Fair Trade'],
            'Chemicals': ['REACH Compliant', 'ISO 9001', 'GMP', 'MSDS Available'],
            'Agriculture': ['USDA Organic', 'GLOBALG.A.P', 'ISO 9001', 'Fair Trade']
        }
        
        # Indian cities/states for supplier locations
        self.indian_locations = [
            ('Mumbai', 'Maharashtra', 'India'),
            ('Delhi', 'Delhi', 'India'),
            ('Bangalore', 'Karnataka', 'India'),
            ('Chennai', 'Tamil Nadu', 'India'),
            ('Hyderabad', 'Telangana', 'India'),
            ('Pune', 'Maharashtra', 'India'),
            ('Kolkata', 'West Bengal', 'India'),
            ('Ahmedabad', 'Gujarat', 'India'),
            ('Jaipur', 'Rajasthan', 'India'),
            ('Surat', 'Gujarat', 'India')
        ]
    
    def generate_product(self, category: str = None, subcategory: str = None) -> Dict[str, Any]:
        """
        Generate a single mock product.
        
        Args:
            category: Specific category to generate for (optional)
            subcategory: Specific subcategory to generate for (optional)
            
        Returns:
            Dictionary containing mock product data
        """
        # Select category
        if category is None:
            category = random.choice(list(self.categories.keys()))
        elif category not in self.categories:
            # Fallback to random if invalid category provided
            category = random.choice(list(self.categories.keys()))
        
        # Select subcategory
        if subcategory is None:
            subcategory = random.choice(self.categories[category])
        elif subcategory not in self.categories[category]:
            # Fallback to random if invalid subcategory provided
            subcategory = random.choice(self.categories[category])
        
        # Generate product ID
        product_id = str(uuid.uuid4())
        
        # Generate product name
        name = self._generate_product_name(category, subcategory)
        
        # Generate price (in various currencies, will be normalized later)
        currency = random.choice(self.currencies)
        if currency in ['JPY']:
            # Yen tends to have higher numbers
            price_min = round(random.uniform(1000, 500000), 2)
            price_max = round(price_min * random.uniform(1.0, 3.0), 2)
        elif currency in ['INR']:
            # Rupees
            price_min = round(random.uniform(100, 50000), 2)
            price_max = round(price_min * random.uniform(1.0, 3.0), 2)
        else:
            # USD, EUR, GBP, CNY
            price_min = round(random.uniform(10, 10000), 2)
            price_max = round(price_min * random.uniform(1.0, 3.0), 2)
        
        # Generate MOQ
        moq = random.randint(1, 1000)
        
        # Generate unit
        unit = random.choice(self.units)
        
        # Generate supplier info
        supplier_name = fake.company()
        supplier_rating = round(random.uniform(3.0, 5.0), 1)
        supplier_location = random.choice(self.indian_locations)
        supplier_location_str = f"{supplier_location[0]}, {supplier_location[1]}, {supplier_location[2]}"
        verified_supplier = random.choice([True, False])
        response_rate = round(random.uniform(60.0, 99.0), 1) if verified_supplier else round(random.uniform(30.0, 70.0), 1)
        
        # Generate certifications
        category_certs = self.certifications.get(category, ['ISO 9001'])
        num_certs = random.randint(0, len(category_certs))
        certifications = random.sample(category_certs, num_certs) if num_certs > 0 else []
        
        # Generate keywords
        keywords = self._generate_keywords(name, category, subcategory)
        
        # Generate description
        description = self._generate_description(name, category, subcategory, keywords)
        
        # Generate listing URL
        listing_url = f"https://example.com/product/{product_id}"
        
        # Scraped timestamp
        scraped_at = time.time() - random.randint(0, 30*24*60*60)  # Up to 30 days ago
        
        product = {
            'product_id': product_id,
            'name': name,
            'price_min': price_min,
            'price_max': price_max,
            'currency': currency,
            'moq': moq,
            'unit': unit,
            'supplier_name': supplier_name,
            'supplier_rating': supplier_rating,
            'supplier_location': supplier_location_str,
            'verified_supplier': verified_supplier,
            'response_rate': response_rate,
            'certifications': certifications,
            'keywords': keywords,
            'category': category,
            'subcategory': subcategory,
            'description': description,
            'listing_url': listing_url,
            'scraped_at': scraped_at
        }
        
        return product
    
    def generate_products(self, count: int, categories: List[str] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple mock products.
        
        Args:
            count: Number of products to generate
            categories: List of categories to generate from (optional)
            
        Returns:
            List of mock product dictionaries
        """
        products = []
        for _ in range(count):
            category = random.choice(categories) if categories else None
            product = self.generate_product(category=category)
            products.append(product)
        return products
    
    def _generate_product_name(self, category: str, subcategory: str) -> str:
        """Generate a realistic product name based on category and subcategory."""
        adjectives = ['High-Quality', 'Premium', 'Industrial', 'Heavy-Duty', 'Professional', 
                     'Efficient', 'Reliable', 'Durable', 'Advanced', 'Standard']
        materials = ['Steel', 'Aluminum', 'Plastic', 'Copper', 'Brass', 'Glass', 'Fabric', 
                    'Chemical', 'Electronic', 'Agricultural']
        
        # Category-specific prefixes/suffixes
        category_patterns = {
            'Industrial Machinery': ['{} Machine', '{} System', '{} Equipment', '{} Unit'],
            'Electronics': ['{} Module', '{} Board', '{} Device', '{} Component'],
            'Textiles': ['{} Fabric', '{} Yarn', '{} Textile', '{} Material'],
            'Chemicals': ['{} Compound', '{} Solution', '{} Chemical', '{} Formula'],
            'Agriculture': ['{} Equipment', '{} Tool', '{} System', '{} Product']
        }
        
        patterns = category_patterns.get(category, ['{} Product', '{} Item', '{} Unit'])
        pattern = random.choice(patterns)
        
        adj = random.choice(adjectives)
        mat = random.choice(materials)
        
        # Sometimes use just adjective + material, sometimes use subcategory
        if random.random() > 0.5:
            name = pattern.format(f"{adj} {mat}")
        else:
            name = pattern.format(subcategory)
        
        # Add model number sometimes
        if random.random() > 0.7:
            model = f"Model-{random.randint(100, 999)}{random.choice(['A', 'B', 'Pro', 'Max'])}"
            name = f"{name} {model}"
            
        return name
    
    def _generate_keywords(self, name: str, category: str, subcategory: str) -> List[str]:
        """Generate relevant keywords for the product."""
        keywords = []
        
        # Add category and subcategory
        keywords.append(category.lower())
        keywords.append(subcategory.lower().replace(' ', '_'))
        
        # Extract words from name
        name_words = [word.lower().strip(',-') for word in name.split() if len(word) > 2]
        keywords.extend(name_words[:3])  # Take first 3 meaningful words
        
        # Add some generic terms
        generic_terms = ['quality', 'durable', 'efficient', 'industrial', 'commercial']
        keywords.extend(random.sample(generic_terms, random.randint(1, 3)))
        
        # Remove duplicates and limit
        keywords = list(dict.fromkeys(keywords))  # Preserves order while removing dupes
        return keywords[:10]  # Limit to 10 keywords
    
    def _generate_description(self, name: str, category: str, subcategory: str, keywords: List[str]) -> str:
        """Generate a product description."""
        templates = [
            f"The {name} is a high-quality {subcategory.lower()} designed for {category.lower()} applications. "
            f"It features {random.choice(['advanced technology', 'superior durability', 'excellent performance'])} "
            f"and is suitable for {random.choice(['industrial use', 'commercial applications', 'manufacturing processes'])}.",
            
            f"Our {name} offers reliable performance in demanding {category.lower()} environments. "
            f"Constructed with premium materials, this {subcategory.lower()} provides {random.choice(['long service life', 'consistent results', 'optimal efficiency'])}. "
            f"Ideal for {random.choice(['production lines', 'processing facilities', 'heavy-duty operations'])}.",
            
            f"Introducing the {name} - a professional-grade {subcategory.lower()} that delivers {random.choice(['precision', 'reliability', 'value'])}. "
            f"Engineered for {category.lower()} professionals who demand {random.choice(['the best', 'consistent quality', 'superior performance'])}. "
            f"Features include {random.choice(['easy maintenance', 'energy efficiency', 'safety compliance'])}."
        ]
        
        return random.choice(templates)
