import json
import random
import math
import itertools

random.seed(42)

CATEGORIES = {
    "Industrial Machinery": {
        "subcategories": ["CNC Machines", "Conveyor Systems", "Industrial Robots", "Pumps & Valves", "Material Handling", "Welding Equipment"],
        "price_range": (500, 50000),
        "moq_range": (1, 50),
        "keywords": ["cnc", "machinery", "industrial", "automation", "heavy-duty"]
    },
    "Electronics": {
        "subcategories": ["Semiconductors", "PCB Assembly", "Electronic Components", "Consumer Electronics", "Telecom Equipment"],
        "price_range": (10, 5000),
        "moq_range": (10, 1000),
        "keywords": ["electronic", "circuit", "component", "digital", "semiconductor"]
    },
    "Textiles": {
        "subcategories": ["Fabrics", "Yarn & Thread", "Home Textiles", "Technical Textiles", "Apparel", "Textile Machinery"],
        "price_range": (5, 500),
        "moq_range": (50, 5000),
        "keywords": ["fabric", "textile", "woven", "cotton", "polyester"]
    },
    "Chemicals": {
        "subcategories": ["Industrial Chemicals", "Polymers", "Specialty Chemicals", "Agrochemicals", "Pharmaceutical Chemicals", "Adhesives"],
        "price_range": (50, 10000),
        "moq_range": (5, 500),
        "keywords": ["chemical", "compound", "solution", "polymer", "industrial-grade"]
    },
    "Agriculture": {
        "subcategories": ["Farm Equipment", "Irrigation Systems", "Seeds & Fertilizers", "Animal Feed", "Agricultural Chemicals", "Greenhouse Equipment"],
        "price_range": (20, 2000),
        "moq_range": (10, 200),
        "keywords": ["agriculture", "farming", "irrigation", "fertilizer", "equipment"]
    }
}

ADJECTIVES = ["Premium", "Industrial", "High-Grade", "Professional", "Heavy-Duty", "Advanced", "Standard", "Economy", "Commercial", "Heavy-Grade"]
MATERIALS = ["Steel", "Aluminum", "Stainless Steel", "Carbon Steel", "Polymer", "Composite", "Titanium", "Copper", "Brass", "Alloy"]

CITIES = [
    ("Mumbai", "Maharashtra", "West India"),
    ("Pune", "Maharashtra", "West India"),
    ("Delhi", "Delhi", "North India"),
    ("Bangalore", "Karnataka", "South India"),
    ("Chennai", "Tamil Nadu", "South India"),
    ("Hyderabad", "Telangana", "South India"),
    ("Kolkata", "West Bengal", "East India"),
    ("Ahmedabad", "Gujarat", "West India"),
    ("Jaipur", "Rajasthan", "North India"),
    ("Surat", "Gujarat", "West India"),
    ("Lucknow", "Uttar Pradesh", "North India"),
    ("Kanpur", "Uttar Pradesh", "North India"),
    ("Nagpur", "Maharashtra", "West India"),
    ("Indore", "Madhya Pradesh", "Central India"),
    ("Bhopal", "Madhya Pradesh", "Central India"),
    ("Vadodara", "Gujarat", "West India"),
    ("Visakhapatnam", "Andhra Pradesh", "South India"),
    ("Coimbatore", "Tamil Nadu", "South India"),
    ("Chandigarh", "Punjab", "North India"),
    ("Guwahati", "Assam", "Northeast India"),
    ("Kochi", "Kerala", "South India"),
    ("Thiruvananthapuram", "Kerala", "South India"),
    ("Rajkot", "Gujarat", "West India"),
    ("Raipur", "Chhattisgarh", "Central India"),
    ("Ranchi", "Jharkhand", "East India"),
    ("Bhubaneswar", "Odisha", "East India"),
    ("Patna", "Bihar", "East India"),
    ("Agra", "Uttar Pradesh", "North India"),
    ("Varanasi", "Uttar Pradesh", "North India"),
    ("Amritsar", "Punjab", "North India"),
    ("Jodhpur", "Rajasthan", "North India"),
    ("Udaipur", "Rajasthan", "North India"),
    ("Nashik", "Maharashtra", "West India"),
    ("Aurangabad", "Maharashtra", "West India"),
    ("Madurai", "Tamil Nadu", "South India"),
    ("Tirupati", "Andhra Pradesh", "South India"),
    ("Mysore", "Karnataka", "South India"),
    ("Hubli", "Karnataka", "South India"),
    ("Vijayawada", "Andhra Pradesh", "South India"),
    ("Guntur", "Andhra Pradesh", "South India"),
    ("Salem", "Tamil Nadu", "South India"),
    ("Trichy", "Tamil Nadu", "South India"),
    ("Warangal", "Telangana", "South India"),
    ("Gwalior", "Madhya Pradesh", "Central India"),
    ("Jabalpur", "Madhya Pradesh", "Central India"),
    ("Ujjain", "Madhya Pradesh", "Central India"),
    ("Kota", "Rajasthan", "North India"),
    ("Bikaner", "Rajasthan", "North India"),
    ("Shimla", "Himachal Pradesh", "North India"),
    ("Dehradun", "Uttarakhand", "North India"),
]

SUPPLIER_NAMES = [
    "Apex Industrial Solutions", "Precision Tech Industries", "Bharat Machinery Works",
    "Sahyadri Engineering", "Ganges Metal Works", "Konkan Precision Tools",
    "Malabar Industrial Corp", "Coromandel Engineering", "Konark Machine Tools",
    "Himalaya Industrial Products", "Vindhya Engineering Works", "Sahyadri Fabricators",
    "Tata Industrial Systems", "Adani Engineering Works", "Reliance Industrial Products",
    "Birla Precision Tools", "JSW Industrial Solutions", "Mahindra Engineering",
    "L&T Heavy Machinery", "Godrej Industrial Systems", "Bajaj Engineering Works",
    "Ashok Leyland Industrial", "TVS Engineering Solutions", "Amul Machineries",
    "Nestle Industrial Equipment", "Marico Engineering Works", "Dabur Industrial Systems",
    "HUL Engineering Solutions", "P&G Industrial Products", "ITC Engineering Works",
    "Wipro Industrial Solutions", "Infosys Engineering", "TCS Industrial Systems",
    "Tech Mahindra Works", "HCL Engineering Solutions", "Lupin Industrial Products",
    "Cipla Engineering Works", "Dr Reddy's Industrial", "Sun Pharma Systems",
    "Aurobindo Engineering", "Divis Industrial Solutions", "Mankind Engineering Works",
    "Glenmark Industrial Systems", "Torrent Engineering", "Zydus Industrial Products",
    "UltraTech Cement Engineering", "Grasim Industrial Works", "Hindalco Engineering",
    "Vedanta Industrial Solutions", "JSW Steel Engineering"
]

def generate_product_name(cat, subcat):
    adj = random.choice(ADJECTIVES)
    mat = random.choice(MATERIALS)
    pattern = random.choice([
        f"{adj} {subcat}",
        f"{mat} {subcat.split()[0]} {cat.split()[0]}",
        f"{adj} {mat} {subcat.split()[0]}",
        f"Super {adj} {subcat}",
        f"{subcat} {adj} Grade"
    ])
    model = f"MOD-{random.randint(100,999)}-{random.choice(['A','B','C','X','Z','Pro','Elite','Max'])}{random.randint(1,9)}"
    return f"{pattern} {model}"

def generate_certifications(cat):
    cert_pool = {
        "Industrial Machinery": ["ISO 9001:2015", "CE Certified", "OSHA Compliant", "API 6D", "ASME Certified"],
        "Electronics": ["RoHS Compliant", "FCC Certified", "UL Listed", "CE Mark", "ISO 13485"],
        "Textiles": ["OEKO-TEX 100", "GOTS Certified", "ISO 9001:2015", "Fair Trade Certified"],
        "Chemicals": ["REACH Compliant", "GMP Certified", "ISO 9001:2015", "MSDS Available", "FDA Approved"],
        "Agriculture": ["USDA Organic", "GLOBALG.A.P.", "ISO 9001:2015", "Fair Trade Certified", "Non-GMO Verified"]
    }
    pool = cert_pool.get(cat, ["ISO 9001:2015"])
    k = random.randint(0, min(len(pool), 4))
    return sorted(random.sample(pool, k)) if k else []

def generate_description(name, cat, subcat, keywords):
    templates = [
        f"The {name} is a high-quality {subcat.lower()} designed for demanding {cat.lower()} applications. Manufactured using premium-grade materials and advanced manufacturing processes, this product delivers exceptional performance and reliability in the most challenging environments.",
        f"Our {name} offers industry-leading performance for {cat.lower()} professionals. Built with precision engineering and rigorous quality control, this {subcat.lower()} ensures consistent results and long-lasting durability for your operations.",
        f"Introducing the {name} — a cutting-edge {subcat.lower()} solution engineered for modern {cat.lower()} facilities. Featuring advanced technology and robust construction, it provides outstanding value and operational efficiency.",
        f"The {name} represents the pinnacle of {subcat.lower()} technology in the {cat.lower()} sector. With superior build quality, exceptional performance metrics, and comprehensive support, it's the preferred choice for discerning professionals.",
        f"Engineered for excellence, the {name} delivers unmatched performance in {cat.lower()} environments. This {subcat.lower()} combines innovative design with proven reliability to meet the most demanding industrial requirements."
    ]
    return random.choice(templates)

def main():
    products = []
    product_id = 1

    for cat, cat_info in CATEGORIES.items():
        count_per_subcat = max(6, random.randint(6, 14))
        for subcat in cat_info["subcategories"]:
            for _ in range(count_per_subcat):
                city, state, region = random.choice(CITIES)
                supplier = random.choice(SUPPLIER_NAMES)
                price_min = round(random.uniform(*cat_info["price_range"]), 2)
                price_max = round(price_min * random.uniform(1.05, 2.5), 2)
                moq = random.randint(*cat_info["moq_range"])
                moq = moq if moq <= 5000 else 5000
                rating = round(random.uniform(3.0, 5.0), 1)
                response_rate = round(random.uniform(50, 98), 1)
                verified = random.random() < 0.55

                if verified and rating >= 4.5:
                    tier = "Gold"
                elif verified and rating >= 3.5:
                    tier = "Silver"
                else:
                    tier = "Unverified"

                name = generate_product_name(cat, subcat)
                keywords = random.sample(cat_info["keywords"] + subcat.lower().split(), min(5, len(cat_info["keywords"]) + len(subcat.split())))
                description = generate_description(name, cat, subcat, keywords)
                certifications = generate_certifications(cat)

                scraped_at = 1716854400 + random.randint(0, 30 * 86400)

                quality_score = round(random.uniform(60, 99), 1)

                product = {
                    "product_id": f"PROD-{product_id:04d}",
                    "name": name,
                    "category": cat,
                    "subcategory": subcat,
                    "price_min": price_min,
                    "price_max": price_max,
                    "currency": "USD",
                    "moq": moq,
                    "unit": random.choice(["pieces", "kg", "liters", "meters", "units", "boxes", "tons", "sets"]),
                    "supplier_name": supplier,
                    "supplier_rating": rating,
                    "supplier_city": city,
                    "supplier_state": state,
                    "supplier_region": region,
                    "supplier_country": "India",
                    "verified_supplier": verified,
                    "response_rate": response_rate,
                    "supplier_tier": tier,
                    "certifications": certifications,
                    "keywords": keywords,
                    "description": description,
                    "quality_score": quality_score,
                    "scraped_at": scraped_at
                }
                products.append(product)
                product_id += 1

    print(f"Total products generated: {len(products)}")
    
    # Write the data as a variable assignment for embedding
    with open("product_data.js", "w", encoding="utf-8") as f:
        f.write("const PRODUCTS = ")
        json.dump(products, f, indent=2, ensure_ascii=False)
        f.write(";")
    
    print("Written to product_data.js")

if __name__ == "__main__":
    main()
