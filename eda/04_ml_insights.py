#!/usr/bin/env python3
"""
04_ml_insights.ipynb equivalent as Python script
Machine Learning Insights
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# For LDA topic modeling
try:
    import gensim
    from gensim import corpora
    LDA_AVAILABLE = True
except ImportError:
    LDA_AVAILABLE = False
    print("Gensim not installed. LDA topic modeling will be skipped.")

from warehouse.db import load_products_from_warehouse

# Load data
print("Loading data from warehouse...")
df = load_products_from_warehouse(limit=1000)  # Adjust limit as needed
print(f"Loaded {len(df)} products")

# Convert to DataFrame for analysis
if df:
    df = pd.DataFrame(df)
    
    # Prepare data for ML
    print("\n=== Preparing Data for ML ===")
    
    # Select relevant features and handle missing values
    ml_df = df.copy()
    
    # Fill missing numeric values with median
    numeric_cols = ml_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if ml_df[col].isnull().any():
            ml_df[col].fillna(ml_df[col].median(), inplace=True)
    
    # Fill missing categorical values with mode
    categorical_cols = ml_df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if ml_df[col].isnull().any():
            ml_df[col].fillna(ml_df[col].mode()[0] if not ml_df[col].mode().empty else 'unknown', inplace=True)
    
    print(f"Data prepared for ML: {ml_df.shape}")
    
    # 1. Clustering Suppliers by Profile
    print("\n=== 1. Supplier Clustering (KMeans) ===")
    
    # Select features for supplier clustering
    supplier_features = ['supplier_rating', 'response_rate', 'moq']
    # Add price features if available
    if 'price_min' in ml_df.columns and 'price_max' in ml_df.columns:
        ml_df['avg_price'] = (ml_df['price_min'] + ml_df['price_max']) / 2
        supplier_features.append('avg_price')
    
    # Filter to rows with all required features
    supplier_data = ml_df[supplier_features].dropna()
    
    if len(supplier_data) > 10:
        # Standardize features
        scaler = StandardScaler()
        supplier_scaled = scaler.fit_transform(supplier_data)
        
        # Determine optimal number of clusters (elbow method)
        inertias = []
        K_range = range(2, min(10, len(supplier_data)//2))
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(supplier_scaled)
            inertias.append(kmeans.inertia_)
        
        # Plot elbow curve
        plt.figure(figsize=(10, 6))
        plt.plot(K_range, inertias, 'bo-')
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Inertia')
        plt.title('Elbow Method for Optimal k')
        plt.tight_layout()
        plt.savefig('supplier_clustering_elbow.png')
        plt.show()
        
        # Choose k=4 as default (can be adjusted based on elbow curve)
        k_optimal = 4
        if len(K_range) > 0:
            k_optimal = min(4, len(K_range)) if len(K_range) >= 4 else K_range[-1]
        
        # Perform clustering
        kmeans = KMeans(n_clusters=k_optimal, random_state=42, n_init=10)
        supplier_clusters = kmeans.fit_predict(supplier_scaled)
        
        # Add cluster labels to dataframe
        ml_df.loc[supplier_data.index, 'supplier_cluster'] = supplier_clusters
        
        # Analyze clusters
        print(f"Supplier Clustering Results (k={k_optimal}):")
        cluster_summary = ml_df.groupby('supplier_cluster')[supplier_features].mean()
        print(cluster_summary)
        
        # Visualize clusters (first two dimensions)
        if len(supplier_features) >= 2:
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(supplier_scaled[:, 0], supplier_scaled[:, 1], 
                                c=supplier_clusters, cmap='viridis', alpha=0.6)
            plt.xlabel(f'{supplier_features[0]} (standardized)')
            plt.ylabel(f'{supplier_features[1]} (standardized)')
            plt.title(f'Supplier Clusters (k={k_optimal})')
            plt.colorbar(scatter, label='Cluster')
            plt.tight_layout()
            plt.savefig('supplier_clusters.png')
            plt.show()
    
    # 2. Price Prediction Model (Random Forest)
    print("\n=== 2. Price Prediction (Random Forest) ===")
    
    # Prepare features for price prediction
    price_features = []
    
    # Categorical features to encode
    cat_features = ['category', 'subcategory', 'unit']
    # Add geographical features if available
    if 'supplier_region' in ml_df.columns:
        cat_features.append('supplier_region')
    if 'supplier_country' in ml_df.columns:
        cat_features.append('supplier_country')
    
    # Numerical features
    num_features = ['moq']
    # Add supplier features if available
    if 'supplier_rating' in ml_df.columns:
        num_features.append('supplier_rating')
    if 'response_rate' in ml_df.columns:
        num_features.append('response_rate')
    
    # Encode categorical features
    label_encoders = {}
    X_cat_encoded = pd.DataFrame(index=ml_df.index)
    
    for feature in cat_features:
        if feature in ml_df.columns:
            le = LabelEncoder()
            # Handle missing values
            ml_df[feature] = ml_df[feature].fillna('unknown')
            X_cat_encoded[feature] = le.fit_transform(ml_df[feature])
            label_encoders[feature] = le
    
    # Combine features
    X_num = ml_df[num_features].copy() if all(f in ml_df.columns for f in num_features) else pd.DataFrame(index=ml_df.index)
    X = pd.concat([X_num, X_cat_encoded], axis=1)
    
    # Target variable (average price)
    if 'price_min' in ml_df.columns and 'price_max' in ml_df.columns:
        y = (ml_df['price_min'] + ml_df['price_max']) / 2
        
        # Remove rows with missing target or features
        valid_idx = y.notna() & X.notna().all(axis=1)
        X_valid = X[valid_idx]
        y_valid = y[valid_idx]
        
        if len(X_valid) > 20:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_valid, y_valid, test_size=0.2, random_state=42
            )
            
            # Train Random Forest
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(X_train, y_train)
            
            # Predict and evaluate
            y_pred = rf_model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"Random Forest Price Prediction:")
            print(f"  MSE: {mse:.2f}")
            print(f"  R² Score: {r2:.3f}")
            
            # Feature importance
            feature_names = list(X.columns)
            importances = rf_model.feature_importances_
            feat_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            print("\nTop 10 Important Features:")
            print(feat_importance.head(10))
            
            # Plot feature importance
            plt.figure(figsize=(10, 6))
            plt.barh(range(len(feat_importance.head(10))), 
                    feat_importance.head(10)['importance'])
            plt.yticks(range(len(feat_importance.head(10))), 
                      feat_importance.head(10)['feature'])
            plt.xlabel('Feature Importance')
            plt.title('Top 10 Features for Price Prediction')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig('price_prediction_features.png')
            plt.show()
            
            # Actual vs Predicted plot
            plt.figure(figsize=(8, 6))
            plt.scatter(y_test, y_pred, alpha=0.6)
            plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
            plt.xlabel('Actual Price (USD)')
            plt.ylabel('Predicted Price (USD)')
            plt.title(f'Actual vs Predicted Prices (R² = {r2:.3f})')
            plt.tight_layout()
            plt.savefig('price_prediction_actual_vs_predicted.png')
            plt.show()
        else:
            print("Insufficient data for price prediction model")
    
    # 3. Anomaly Detection on Pricing (Isolation Forest)
    print("\n=== 3. Price Anomaly Detection (Isolation Forest) ===")
    
    # Prepare data for anomaly detection
    anomaly_features = []
    if 'price_min' in ml_df.columns:
        anomaly_features.append('price_min')
    if 'price_max' in ml_df.columns:
        anomaly_features.append('price_max')
    if 'moq' in ml_df.columns:
        anomaly_features.append('moq')
    
    anomaly_data = ml_df[anomaly_features].dropna()
    
    if len(anomaly_data) > 10:
        # Standardize features
        scaler_anomaly = StandardScaler()
        anomaly_scaled = scaler_anomaly.fit_transform(anomaly_data)
        
        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_scores = iso_forest.fit_predict(anomaly_scaled)
        anomaly_probabilities = iso_forest.score_samples(anomaly_scaled)
        
        # Add anomaly labels to dataframe
        ml_df.loc[anomaly_data.index, 'is_anomaly'] = (anomaly_scores == -1)
        ml_df.loc[anomaly_data.index, 'anomaly_score'] = anomaly_probabilities
        
        n_anomalies = (anomaly_scores == -1).sum()
        print(f"Detected {n_anomalies} price anomalies out of {len(anomaly_data)} samples "
              f"({100*n_anomalies/len(anomaly_data):.1f}%)")
        
        # Visualize anomalies (if we have at least 2 features)
        if len(anomaly_features) >= 2:
            plt.figure(figsize=(10, 8))
            colors = ['red' if anomaly == -1 else 'blue' for anomaly in anomaly_scores]
            plt.scatter(anomaly_scaled[:, 0], anomaly_scaled[:, 1], 
                       c=colors, alpha=0.6)
            plt.xlabel(f'{anomaly_features[0]} (standardized)')
            plt.ylabel(f'{anomaly_features[1]} (standardized)')
            plt.title('Price Anomalies Detected by Isolation Forest')
            plt.tight_layout()
            plt.savefig('price_anomalies.png')
            plt.show()
    
    # 4. Keyword Topic Modeling (LDA) - if gensim is available
    if LDA_AVAILABLE and 'description' in ml_df.columns:
        print("\n=== 4. Keyword Topic Modeling (LDA) ===")
        
        # Prepare text data
        descriptions = ml_df['description'].dropna().astype(str)
        
        if len(descriptions) > 10:
            # Tokenize and preprocess
            def preprocess_text(text):
                # Simple tokenization - in practice, you'd want more sophisticated NLP
                tokens = text.lower().split()
                # Remove short words and digits
                tokens = [token for token in tokens if len(token) > 2 and not token.isdigit()]
                return tokens
            
            tokenized_docs = [preprocess_text(doc) for doc in descriptions]
            
            # Remove empty documents
            tokenized_docs = [doc for doc in tokenized_docs if len(doc) > 0]
            
            if len(tokenized_docs) > 5:
                # Create dictionary and corpus
                dictionary = corpora.Dictionary(tokenized_docs)
                # Filter extremes
                dictionary.filter_extremes(no_below=2, no_above=0.5)
                corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]
                
                # Train LDA model
                try:
                    lda_model = gensim.models.LdaModel(
                        corpus=corpus,
                        id2word=dictionary,
                        num_topics=5,
                        random_state=42,
                        passes=10,
                        alpha='auto',
                        per_word_topics=True
                    )
                    
                    print("LDA Topics:")
                    topics = lda_model.print_topics(num_words=5)
                    for topic_id, topic in topics:
                        print(f"Topic {topic_id}: {topic}")
                    
                    # Visualize topic distribution
                    topic_probs = lda_model.get_document_topics(corpus)
                    # Get dominant topic for each document
                    dominant_topics = [max(topic, key=lambda x: x[1])[0] for topic in topic_probs]
                    
                    plt.figure(figsize=(10, 6))
                    plt.hist(dominant_topics, bins=range(len(topics)+1), align='left', rwidth=0.8)
                    plt.xlabel('Topic ID')
                    plt.ylabel('Number of Documents')
                    plt.title('Distribution of Dominant Topics in Product Descriptions')
                    plt.xticks(range(len(topics)))
                    plt.tight_layout()
                    plt.savefig('lda_topics.png')
                    plt.show()
                    
                except Exception as e:
                    print(f"LDA modeling failed: {e}")
            else:
                print("Insufficient text data for LDA after preprocessing")
        else:
            print("Insufficient descriptions for LDA topic modeling")
    elif not LDA_AVAILABLE:
        print("\n=== 4. Keyword Topic Modeling (LDA) ===")
        print("Skipping LDA topic modeling - gensim not installed")
    
    print("\n=== ML Insights Complete ===")

else:
    print("No data loaded from warehouse")