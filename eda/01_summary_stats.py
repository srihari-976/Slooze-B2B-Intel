#!/usr/bin/env python3
"""
01_summary_stats.ipynb equivalent as Python script
Summary Statistics and Data Overview
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
    
    # Basic info
    print("\n=== Dataset Info ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Data types
    print("\n=== Data Types ===")
    print(df.dtypes)
    
    # Missing values
    print("\n=== Missing Values ===")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    missing_df = pd.DataFrame({
        'Missing Count': missing,
        'Missing Percentage': missing_pct
    })
    print(missing_df[missing_df['Missing Count'] > 0])
    
    # Basic statistics for numeric columns
    print("\n=== Numeric Columns Summary ===")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    print(df[numeric_cols].describe())
    
    # Categorical columns summary
    print("\n=== Categorical Columns Summary ===")
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols[:5]:  # Limit to first 5
        print(f"\n{col}:")
        print(df[col].value_counts().head())
    
    # Price analysis
    if 'price_min' in df.columns and 'price_max' in df.columns:
        print("\n=== Price Analysis ===")
        # Remove outliers for better visualization
        price_data = df[['price_min', 'price_max']].dropna()
        if len(price_data) > 0:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            axes[0].hist(price_data['price_min'], bins=30, alpha=0.7, label='Min Price')
            axes[0].hist(price_data['price_max'], bins=30, alpha=0.7, label='Max Price')
            axes[0].set_xlabel('Price (USD)')
            axes[0].set_ylabel('Frequency')
            axes[0].set_title('Price Distribution')
            axes[0].legend()
            
            axes[1].boxplot([price_data['price_min'], price_data['price_max']], 
                           labels=['Min Price', 'Max Price'])
            axes[1].set_ylabel('Price (USD)')
            axes[1].set_title('Price Boxplot')
            
            plt.tight_layout()
            plt.savefig('price_distribution.png')
            plt.show()
    
    # Category distribution
    if 'category' in df.columns:
        print("\n=== Category Distribution ===")
        cat_counts = df['category'].value_counts()
        print(cat_counts)
        
        plt.figure(figsize=(10, 6))
        cat_counts.plot(kind='bar')
        plt.title('Product Distribution by Category')
        plt.xlabel('Category')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('category_distribution.png')
        plt.show()
    
    # Geographic distribution
    if 'supplier_country' in df.columns:
        print("\n=== Geographic Distribution ===")
        geo_counts = df['supplier_country'].value_counts().head(10)
        print(geo_counts)
        
        if len(geo_counts) > 0:
            plt.figure(figsize=(10, 6))
            geo_counts.plot(kind='bar')
            plt.title('Top 10 Supplier Countries')
            plt.xlabel('Country')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('geographic_distribution.png')
            plt.show()

else:
    print("No data loaded from warehouse")

print("\n=== Summary Statistics Complete ===")