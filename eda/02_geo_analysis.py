#!/usr/bin/env python3
"""
02_geo_analysis.ipynb equivalent as Python script
Geographic Analysis of Suppliers
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from warehouse.db import load_products_from_warehouse

# Load data
print("Loading data from warehouse...")
df = load_products_from_warehouse(limit=1000)  # Adjust limit as needed
print(f"Loaded {len(df)} products")

# Convert to DataFrame for analysis
if df:
    df = pd.DataFrame(df)
    
    # Geographic analysis
    print("\n=== Geographic Analysis ===")
    
    # Country distribution
    if 'supplier_country' in df.columns:
        country_counts = df['supplier_country'].value_counts()
        print("Supplier Country Distribution:")
        print(country_counts.head(10))
        
        # Plot top countries
        plt.figure(figsize=(12, 6))
        country_counts.head(10).plot(kind='bar')
        plt.title('Top 10 Supplier Countries')
        plt.xlabel('Country')
        plt.ylabel('Number of Suppliers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('supplier_countries.png')
        plt.show()
    
    # State/Region distribution (for India-focused data)
    if 'supplier_state' in df.columns:
        state_counts = df['supplier_state'].value_counts()
        print("\nSupplier State Distribution:")
        print(state_counts.head(10))
        
        # Plot top states
        plt.figure(figsize=(12, 6))
        state_counts.head(10).plot(kind='bar')
        plt.title('Top 10 Supplier States')
        plt.xlabel('State')
        plt.ylabel('Number of Suppliers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('supplier_states.png')
        plt.show()
    
    if 'supplier_region' in df.columns:
        region_counts = df['supplier_region'].value_counts()
        print("\nSupplier Region Distribution:")
        print(region_counts)
        
        # Plot regions
        plt.figure(figsize=(10, 6))
        region_counts.plot(kind='bar')
        plt.title('Supplier Regions')
        plt.xlabel('Region')
        plt.ylabel('Number of Suppliers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('supplier_regions.png')
        plt.show()
    
    # Price vs Geography
    if 'price_min' in df.columns and 'supplier_country' in df.columns:
        print("\n=== Price by Geography ===")
        # Remove rows with missing price or country
        price_geo_df = df[['price_min', 'supplier_country']].dropna()
        
        if len(price_geo_df) > 0:
            # Get top countries by count
            top_countries = price_geo_df['supplier_country'].value_counts().head(8).index
            price_geo_df_top = price_geo_df[price_geo_df['supplier_country'].isin(top_countries)]
            
            plt.figure(figsize=(14, 8))
            sns.boxplot(data=price_geo_df_top, x='supplier_country', y='price_min')
            plt.title('Price Distribution by Top Supplier Countries')
            plt.xlabel('Country')
            plt.ylabel('Minimum Price (USD)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('price_by_country.png')
            plt.show()
    
    # Supplier density heatmap (if we had lat/long, we'll approximate with state counts)
    if 'supplier_state' in df.columns and len(df['supplier_state'].dropna()) > 0:
        print("\n=== Supplier Density ===")
        state_counts = df['supplier_state'].value_counts()
        
        # Create a simple bar plot as proxy for density
        plt.figure(figsize=(14, 8))
        state_counts.head(15).plot(kind='bar')
        plt.title('Supplier Density by State (Top 15)')
        plt.xlabel('State')
        plt.ylabel('Number of Suppliers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('supplier_density.png')
        plt.show()

else:
    print("No data loaded from warehouse")

print("\n=== Geographic Analysis Complete ===")