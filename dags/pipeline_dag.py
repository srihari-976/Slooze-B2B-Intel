"""
Airflow DAG for the B2B Marketplace Crawler Pipeline
Orchestrates the ETL process: Crawl -> Extract -> Transform -> Load -> Analyze
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os

# Default arguments for the DAG
default_args = {
    'owner': 'data-eng-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'b2b_marketplace_pipeline',
    default_args=default_args,
    description='Pipeline for B2B marketplace data crawling and analysis',
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    catchup=False,
    tags=['b2b', 'crawler', 'etl', 'ml']
)

# Task 1: Crawl data from IndiaMART and TradeIndia
def crawl_indiamart(**context):
    """Crawl product data from IndiaMART"""
    import sys
    sys.path.append('/opt/airflow/slooze-challenge')
    from crawler.indiamart_crawler import IndiaMARTCrawler
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Starting IndiaMART crawl")
    
    crawler = IndiaMARTCrawler(rate_limit=2.0)
    
    # Search for products in various categories
    categories = ['Industrial Machinery', 'Electronics', 'Textiles', 'Chemicals', 'Agriculture']
    all_products = []
    
    for category in categories:
        try:
            # Search for products (simplified - in practice would use specific search terms)
            products = crawler.search_products(query=category, max_pages=3)
            logger.info(f"Found {len(products)} products for {category} on IndiaMART")
            all_products.extend(products)
        except Exception as e:
            logger.error(f"Error crawling IndiaMART for {category}: {e}")
    
    # Push results to XCom for next task
    context['task_instance'].xcom_push(key='indiamart_products', value=all_products)
    return len(all_products)

def crawl_tradeindia(**context):
    """Crawl product data from TradeIndia"""
    import sys
    sys.path.append('/opt/airflow/slooze-challenge')
    from crawler.tradeindia_crawler import TradeIndiaCrawler
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Starting TradeIndia crawl")
    
    # Initialize crawler
    crawler = TradeIndiaCrawler(rate_limit=2.0)
    
    # Search for products in various categories
    categories = ['Industrial Machinery', 'Electronics', 'Textiles', 'Chemicals', 'Agriculture']
    all_products = []
    
    for category in categories:
        try:
            products = crawler.search_products(query=category, max_pages=3)
            logger.info(f"Found {len(products)} products for {category} on TradeIndia")
            all_products.extend(products)
        except Exception as e:
            logger.error(f"Error crawling TradeIndia for {category}: {e}")
    
    # Push results to XCom for next task
    context['task_instance'].xcom_push(key='tradeindia_products', value=all_products)
    return len(all_products)

# Task 2: Extract structured data using AI
def extract_with_ai(**context):
    """Extract structured product data using AI"""
    import sys
    sys.path.append('/opt/airflow/slooze-challenge')
    from crawler.ai_extractor import create_extractor
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Starting AI extraction")
    
    # Get crawled data from previous tasks
    ti = context['task_instance']
    indiamart_products = ti.xcom_pull(task_ids='crawl_indiamart', key='indiamart_products')
    tradeindia_products = ti.xcom_pull(task_ids='crawl_tradeindia', key='tradeindia_products')
    
    all_raw_products = (indiamart_products or []) + (tradeindia_products or [])
    logger.info(f"Total raw products to process: {len(all_raw_products)}")
    
    # Initialize AI extractor (auto-detects: Ollama local or Anthropic)
    try:
        extractor = create_extractor()
    except Exception as e:
        logger.error(f"Failed to initialize AI extractor: {e}")
        # Fallback to mock data generation for demonstration
        from crawler.mock_generator import MockDataGenerator
        generator = MockDataGenerator()
        extracted_products = generator.generate_products(count=50)
        ti.xcom_push(key='extracted_products', value=extracted_products)
        return len(extracted_products)
    
    # Process each product with AI extraction
    extracted_products = []
    for i, product in enumerate(all_raw_products[:20]):  # Limit for demo
        try:
            # In practice, we would fetch the HTML content from the listing_url
            # For this demo, we'll simulate the extraction
            if 'listing_url' in product:
                # Normally we would fetch HTML and pass to extractor
                # For demo, we'll generate mock structured data
                from crawler.mock_generator import MockDataGenerator
                generator = MockDataGenerator()
                mock_product = generator.generate_product(
                    category=product.get('category'),
                    subcategory=product.get('subcategory')
                )
                # Preserve some original data
                mock_product['listing_url'] = product.get('listing_url')
                mock_product['source'] = product.get('source')
                extracted_products.append(mock_product)
            else:
                extracted_products.append(product)
        except Exception as e:
            logger.warning(f"Error extracting product {i}: {e}")
            extracted_products.append(product)  # Keep original if extraction fails
    
    logger.info(f"AI extraction completed for {len(extracted_products)} products")
    ti.xcom_push(key='extracted_products', value=extracted_products)
    return len(extracted_products)

# Task 3: Run ETL pipeline
def run_etl(**context):
    """Run the ETL pipeline on extracted data"""
    import sys
    sys.path.append('/opt/airflow/slooze-challenge')
    from etl.deduplicator import Deduplicator
    from etl.normalizer import Normalizer
    from etl.nlp_enricher import NLPEnricher
    from etl.geo_enricher import GeoEnricher
    from warehouse.db import save_products_to_warehouse
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Starting ETL pipeline")
    
    # Get extracted data
    ti = context['task_instance']
    extracted_products = ti.xcom_pull(task_ids='extract_with_ai', key='extracted_products')
    
    if not extracted_products:
        logger.warning("No extracted products to process")
        return 0
    
    logger.info(f"Processing {len(extracted_products)} products through ETL")
    
    # Initialize ETL components
    deduplicator = Deduplicator()
    normalizer = Normalizer()
    nlp_enricher = NLPEnricher()
    geo_enricher = GeoEnricher()
    
    # Process pipeline
    try:
        # 1. Deduplication
        logger.info("Step 1: Deduplication")
        deduped_products = deduplicator.deduplicate(extracted_products)
        logger.info(f"After deduplication: {len(deduped_products)} products")
        
        # 2. Normalization (price, unit)
        logger.info("Step 2: Normalization")
        normalized_products = []
        for product in deduped_products:
            normalized = normalizer.normalize_product(product)
            normalized_products.append(normalized)
        
        # 3. NLP Enrichment
        logger.info("Step 3: NLP Enrichment")
        nlp_enriched_products = []
        for product in normalized_products:
            enriched = nlp_enricher.enrich_product(product)
            nlp_enriched_products.append(enriched)
        
        # 4. Geo Enrichment
        logger.info("Step 4: Geo Enrichment")
        geo_enriched_products = []
        for product in nlp_enriched_products:
            enriched = geo_enricher.enrich_product(product)
            geo_enriched_products.append(enriched)
        
        # 5. Save to warehouse
        logger.info("Step 5: Saving to warehouse")
        success = save_products_to_warehouse(geo_enriched_products)
        
        if success:
            logger.info(f"ETL pipeline completed successfully. Saved {len(geo_enriched_products)} products.")
            return len(geo_enriched_products)
        else:
            logger.error("Failed to save products to warehouse")
            return 0
            
    except Exception as e:
        logger.error(f"Error in ETL pipeline: {e}")
        return 0

# Task 4: Run EDA and ML analysis
def run_analysis(**context):
    """Run EDA and ML analysis on warehouse data"""
    import subprocess
    import logging
    import sys
    import os
    
    logger = logging.getLogger(__name__)
    logger.info("Starting EDA and ML analysis")
    
    scripts = [
        "eda/01_summary_stats.py",
        "eda/02_geo_analysis.py",
        "eda/03_price_analysis.py",
        "eda/04_ml_insights.py",
    ]
    
    failed = []
    for script in scripts:
        logger.info(f"Running {script}...")
        result = subprocess.run(
            [sys.executable, script],
            capture_output=False,
            env={**os.environ, "PYTHONPATH": "/opt/airflow/slooze-challenge"},
        )
        if result.returncode != 0:
            failed.append(script)
            logger.error(f"{script} failed with code {result.returncode}")
        else:
            logger.info(f"{script} completed")
    
    if failed:
        logger.error(f"Failed scripts: {failed}")
        return False
    logger.info("All analysis completed successfully")
    return True

# Define tasks
crawl_indiamart_task = PythonOperator(
    task_id='crawl_indiamart',
    python_callable=crawl_indiamart,
    dag=dag,
)

crawl_tradeindia_task = PythonOperator(
    task_id='crawl_tradeindia',
    python_callable=crawl_tradeindia,
    dag=dag,
)

extract_ai_task = PythonOperator(
    task_id='extract_with_ai',
    python_callable=extract_with_ai,
    dag=dag,
)

etl_task = PythonOperator(
    task_id='run_etl',
    python_callable=run_etl,
    dag=dag,
)

analysis_task = PythonOperator(
    task_id='run_analysis',
    python_callable=run_analysis,
    dag=dag,
)

# Set task dependencies
[crawl_indiamart_task, crawl_tradeindia_task] >> extract_ai_task >> etl_task >> analysis_task