#!/usr/bin/env python3
"""
03_price_analysis.ipynb equivalent as Python script
Price Analysis and Elasticity
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from warehouse.db import load_products_from_warehouse

# Load data
print("Loading data from warehouse...")
df = load_products_from_warehouse(limit=1000)  # Adjust limit as needed
print(f"Loaded {len(df)} products")

# Convert to DataFrame for analysis
if df:
    df = pd.DataFrame(df)
    
    # Price analysis
    print("\n=== Price Analysis ===")
    
    # Clean price data
    price_df = df[['price_min', 'price_max', 'category', 'supplier_rating', 'moq']].dropna()
    print(f"Price data available for {len(price_df)} products")
    
    if len(price_df) > 0:
        # Calculate average price
        price_df['avg_price'] = (price_df['price_min'] + price_df['price_max']) / 2
        
        # Price distribution by category
        print("\n--- Price Distribution by Category ---")
        if 'category' in price_df.columns:
            plt.figure(figsize=(14, 8))
            sns.boxplot(data=price_df, x='category', y='avg_price')
            plt.title('Price Distribution by Category')
            plt.xlabel('Category')
            plt.ylabel('Average Price (USD)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('price_by_category.png')
            plt.show()
            
            # Price statistics by category
            print("Price Statistics by Category:")
            category_stats = price_df.groupby('category')['avg_price'].agg(['mean', 'median', 'std', 'count'])
            print(category_stats)
        
        # Price vs MOQ correlation
        print("\n--- Price vs MOQ Analysis ---")
        if 'moq' in price_df.columns:
            # Remove extreme outliers for better visualization
            q_low = price_df['moq'].quantile(0.01)
            q_high = price_df['moq'].quantile(0.99)
            moq_filtered = price_df[(price_df['moq'] >= q_low) & (price_df['moq'] <= q_high)]
            
            if len(moq_filtered) > 10:
                correlation = moq_filtered['avg_price'].corr(moq_filtered['moq'])
                print(f"Correlation between price and MOQ: {correlation:.3f}")
                
                plt.figure(figsize=(10, 6))
                plt.scatter(moq_filtered['moq'], moq_filtered['avg_price'], alpha=0.6)
                plt.xlabel('Minimum Order Quantity')
                plt.ylabel('Average Price (USD)')
                plt.title(f'Price vs MOQ (Correlation: {correlation:.3f})')
                
                # Add trend line
                z = np.polyfit(moq_filtered['moq'], moq_filtered['avg_price'], 1)
                p = np.poly1d(z)
                plt.plot(moq_filtered['moq'], p(moq_filtered['moq']), "r--", alpha=0.8)
                plt.tight_layout()
                plt.savefig('price_vs_moq.png')
                plt.show()
        
        # Price vs Supplier Rating
        print("\n--- Price vs Supplier Rating ---")
        if 'supplier_rating' in price_df.columns:
            rating_filtered = price_df.dropna(subset=['supplier_rating'])
            if len(rating_filtered) > 10:
                correlation = rating_filtered['avg_price'].corr(rating_filtered['supplier_rating'])
                print(f"Correlation between price and supplier rating: {correlation:.3f}")
                
                plt.figure(figsize=(10, 6))
                plt.scatter(rating_filtered['supplier_rating'], rating_filtered['avg_price'], alpha=0.6)
                plt.xlabel('Supplier Rating')
                plt.ylabel('Average Price (USD)')
                plt.title(f'Price vs Supplier Rating (Correlation: {correlation:.3f})')
                
                # Add trend line
                z = np.polyfit(rating_filtered['supplier_rating'], rating_filtered['avg_price'], 1)
                p = np.poly1d(z)
                plt.plot(rating_filtered['supplier_rating'], p(rating_filtered['supplier_rating']), "r--", alpha=0.8)
                plt.tight_layout()
                plt.savefig('price_vs_rating.png')
                plt.show()
        
        # Price elasticity analysis (simplified)
        print("\n--- Price Elasticity Analysis ---")
        # Group by category and calculate basic elasticity measures
        if 'category' in price_df.columns and len(price_df['category'].unique()) > 1:
            elasticity_results = []
            for category in price_df['category'].unique():
                cat_data = price_df[price_df['category'] == category]
                if len(cat_data) > 10:  # Need sufficient data
                    # Simple elasticity: % change in quantity / % change in price
                    # Using MOQ as proxy for quantity, price as price
                    if 'moq' in cat_data.columns and 'avg_price' in cat_data.columns:
                        # Calculate log-log regression for elasticity
                        try:
                            log_price = np.log(cat_data['avg_price'])
                            log_moq = np.log(cat_data['moq'])
                            slope, intercept, r_value, p_value, std_err = stats.linregress(log_price, log_moq)
                            elasticity_results.append({
                                'category': category,
                                'elasticity': slope,
                                'r_squared': r_value**2,
                                'p_value': p_value,
                                'sample_size': len(cat_data)
                            })
                        except:
                            pass
            
            if elasticity_results:
                elasticity_df = pd.DataFrame(elasticity_results)
                print("Price Elasticity Results:")
                print(elasticity_df)
                
                # Plot elasticity
                plt.figure(figsize=(12, 6))
                bars = plt.bar(elasticity_df['category'], elasticity_df['elasticity'])
                plt.xlabel('Category')
                plt.ylabel('Price Elasticity')
                plt.title('Price Elasticity by Category')
                plt.xticks(rotation=45)
                
                # Color bars by elasticity value
                for i, bar in enumerate(bars):
                    if elasticity_df['elasticity'].iloc[i] < 0:
                        bar.set_color('red')  # Negative elasticity (expected)
                    else:
                        bar.set_color('blue')  # Positive elasticity (unexpected)
                
                plt.tight_layout()
                plt.savefig('price_elasticity.png')
                plt.show()
    
    # Price ranges analysis
    print("\n--- Price Range Analysis ---")
    if 'price_min' in df.columns and 'price_max' in df.columns:
        # Calculate price spread
        df['price_spread'] = df['price_max'] - df['price_min']
        df['price_spread_pct'] = (df['price_spread'] / df['price_min']) * 100
        
        # Remove extreme outliers
        spread_df = df[['price_spread', 'price_spread_pct', 'category']].dropna()
        q_high = spread_df['price_spread_pct'].quantile(0.95)
        spread_filtered = spread_df[spread_df['price_spread_pct'] <= q_high]
        
        if len(spread_filtered) > 0:
            print(f"Average price spread: {spread_filtered['price_spread'].mean():.2f} USD")
            print(f"Average price spread percentage: {spread_filtered['price_spread_pct'].mean():.2f}%")
            
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=spread_filtered, x='category', y='price_spread_pct')
            plt.title('Price Spread Percentage by Category')
            plt.xlabel('Category')
            plt.ylabel('Price Spread (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('price_spread.png')
            plt.show()

else:
    print("No data loaded from warehouse")

print("\n=== Price Analysis Complete ===")