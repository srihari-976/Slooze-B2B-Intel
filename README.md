# Slooze Challenge: B2B Marketplace Crawler & Analytics Platform

A comprehensive system for crawling B2B marketplaces (IndiaMART, TradeIndia), extracting structured product data using AI, and generating insights through ETL, EDA, and machine learning.

**No API keys required** — the AI extraction layer runs locally via [Ollama](https://ollama.com) + Qwen 2.5 by default.

---

## System Architecture

```
B2B Marketplace Crawler → Raw Data Lake → ETL Pipeline → Data Warehouse → EDA + ML Insights
     └─ AI Extraction (Ollama / Anthropic)
```

## Quick Start

### 1. View the dashboard (zero setup)
Open any file in `dashboard/` in your browser:
```
dashboard/index.html      # Main KPIs & charts
dashboard/geo.html        # Geographic analysis
dashboard/products.html   # Product explorer with DataTable
```

### 2. Run the full pipeline (scrape + ETL + build dashboard)
```bash
cd slooze-challenge
pip install requests beautifulsoup4 pandas pyarrow python-dotenv pydantic
python -m spacy download en_core_web_sm
python crawler/tradeindia_scraper.py
python dashboard/build_html.py
```

### 3. Or use the one-command runner
```bash
python run.py                 # scrape + load + build dashboard
python run.py --no-scrape     # rebuild dashboard from cached data
```

### 4. AI extraction (optional)
```bash
# Install Ollama from https://ollama.com then:
ollama pull qwen2.5:7b
python -c "from crawler.ai_extractor import create_extractor; e = create_extractor(); print(e.extract_product_data('<html><h1>CNC Machine</h1></html>'))"
```

---

## Features

### Part A — Advanced Data Collection
- **Tier 1 – Real HTTP Scraper**: Rotating proxies + user-agents, session management, robots.txt compliance, adaptive rate limiting
- **Tier 2 – AI-Powered Extraction**: Feed raw HTML into an LLM (local Qwen or Anthropic Claude) to extract structured JSON — handles layout changes automatically
- **Tier 3 – Realistic Mock Data Generator**: Faker-based data simulator for offline development and CI testing

### Part B — ETL Pipeline
- Raw JSON → Dedup → Normalize prices (USD) → NLP keyword extraction → Geo-enrichment → Parquet/SQLite warehouse
- Deduplication via fuzzy matching on product name + supplier
- Price normalization (INR/USD/CNY → USD)
- NLP: spaCy for keyword/entity extraction from descriptions
- Geo enrichment: map city → state → region using a lookup table
- Schema validation with pydantic models

### Part C — EDA + ML Layer
- **Analytics**: Price elasticity, supplier density heatmap, MOQ vs price correlation, time-series trends, anomaly detection
- **ML**: Supplier clustering (KMeans), price prediction (Random Forest), keyword topic modeling (LDA)

### Dashboard (HTML, no backend needed)
- **Main Dashboard**: KPI cards, category bar chart, region donut, time series, tier breakdown
- **Geographic Analysis**: Top cities, state heatmap, region-wise category split, state ranking
- **Product Explorer**: Searchable DataTable with filters (category, tier, city, price range, verified), price histogram, MOQ vs price scatter, anomaly highlighting

---

## Setup

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com) (recommended — free, local, no API key) — or an Anthropic API key

### 1. Python Environment

```bash
# Create & activate a virtualenv
python -m venv venv
source venv/bin/activate     # Linux / macOS
venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. AI Backend

#### Option A — Ollama (default, no API key)

```bash
# Install Ollama from https://ollama.com
ollama pull qwen2.5:7b      # ~4 GB, great balance of speed & quality
# or try a larger model:
ollama pull qwen2.5:14b     # ~9 GB, better extraction accuracy
```

The extractor will auto-detect Ollama when `ANTHROPIC_API_KEY` is not set.

#### Option B — Anthropic Claude (optional, requires API key)

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

Set `AI_PROVIDER=anthropic` in `.env` or `settings.yaml` to force Anthropic.

### 4. Environment Variables (all optional)

Create a `.env` file (copy from `.env.example`):

```
# --- AI Provider ---
# Leave empty for auto-detect (ollama if no Anthropic key, else anthropic)
# AI_PROVIDER=ollama
# ANTHROPIC_API_KEY=sk-ant-...

# --- Ollama Settings ---
# OLLAMA_MODEL=qwen2.5:7b
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_TIMEOUT=60
```

---

## Usage

### Run the Full ETL Pipeline

```bash
python -c "
from crawler.mock_generator import MockDataGenerator
from crawler.ai_extractor import create_extractor
from etl.deduplicator import Deduplicator
from etl.normalizer import Normalizer
from etl.nlp_enricher import NLPEnricher
from etl.geo_enricher import GeoEnricher
from warehouse.db import save_products_to_warehouse

# 1. Generate mock data (simulates crawled products)
products = MockDataGenerator().generate_products(200)

# 2. Optional: run AI extraction on raw HTML (simulated here)
#    extractor = create_extractor()
#    products = [extractor.extract_product_data(html, url) for ...]

# 3. ETL pipeline
products = Deduplicator().deduplicate(products)
products = [Normalizer().normalize_product(p) for p in products]
products = [NLPEnricher().enrich_product(p) for p in products]
products = [GeoEnricher().enrich_product(p) for p in products]

# 4. Load to warehouse
save_products_to_warehouse(products)
print(f'Saved {len(products)} products')
"
```

### Run the Dashboard

Just open any HTML file in `dashboard/` in your browser — no server needed:

```bash
# On macOS / Linux
open dashboard/index.html

# On Windows
start dashboard/index.html
```

The three pages share data from a hardcoded `const DATA` block (258 realistic B2B products). All charts use Chart.js v4, the product table uses DataTables, and styling uses Tailwind CSS — all loaded from CDN.

### Crawl Real Sites (requires internet)

```bash
# IndiaMART
python -c "
from crawler.indiamart_crawler import IndiaMARTCrawler
crawler = IndiaMARTCrawler()
products = crawler.search_products('CNC Machine', max_pages=2)
print(f'Found {len(products)} products')
"

# TradeIndia
python -c "
from crawler.tradeindia_crawler import TradeIndiaCrawler
crawler = TradeIndiaCrawler()
products = crawler.search_products('Industrial Machinery', max_pages=2)
print(f'Found {len(products)} products')
"
```

### Activate AI Extraction (Ollama)

```bash
# Make sure Ollama is running in the background, then:
python -c "
from crawler.ai_extractor import create_extractor
extractor = create_extractor()          # auto-detects Ollama
result = extractor.extract_product_data(
    '<html><body><h1>CNC Machine</h1><p>Price: \$5000</p></body></html>',
    url='https://example.com/product/123'
)
print(result)
"
```

To use Anthropic instead:

```bash
ANTHROPIC_API_KEY=sk-ant-... python -c "
from crawler.ai_extractor import create_extractor
extractor = create_extractor(provider='anthropic')
...
"
```

### EDA & ML Analysis

```bash
python eda/01_summary_stats.py
python eda/02_geo_analysis.py
python eda/03_price_analysis.py
python eda/04_ml_insights.py
```

### Airflow Orchestration (optional)

```bash
docker-compose up -d
# Access http://localhost:8080 (admin / admin)
# Trigger the 'b2b_marketplace_pipeline' DAG
```

---

## How AI Extraction Works (No API Key)

The `crawler/ai_extractor.py` module uses a **provider auto-detection** strategy:

1. If `ANTHROPIC_API_KEY` is set → uses **Anthropic Claude** API
2. Otherwise → uses **Ollama** with a local model (default: `qwen2.5:7b`)
3. Explicit override via `AI_PROVIDER=ollama` or `AI_PROVIDER=anthropic`

The extractor sends an HTML page to the LLM with a structured prompt asking for JSON output matching the product schema. This approach is resilient to layout changes — unlike CSS selectors, the LLM understands the semantics of the page.

**Ollama workflow:**
```
HTML page → POST /api/chat (localhost:11434) → qwen2.5 → structured JSON
```

No data leaves your machine when using Ollama.

---

## Folder Structure

```
slooze-challenge/
├── crawler/
│   ├── base_crawler.py        # Abstract base class with rate limiting, robots.txt
│   ├── indiamart_crawler.py   # IndiaMART-specific crawler
│   ├── tradeindia_crawler.py  # TradeIndia-specific crawler
│   ├── ai_extractor.py        # Ollama + Anthropic AI extraction
│   └── mock_generator.py      # Faker-based data simulator (258 products)
├── etl/
│   ├── deduplicator.py        # Fuzzy matching dedup
│   ├── normalizer.py          # Price → USD, unit standardization
│   ├── nlp_enricher.py        # spaCy keyword & entity extraction
│   └── geo_enricher.py        # City → State → Region lookup
├── warehouse/
│   ├── schema.py              # Pydantic v2 models
│   ├── db.py                  # SQLite + Parquet writer/reader
│   └── migrations/
├── eda/
│   ├── 01_summary_stats.py    # Summary statistics & KPIs
│   ├── 02_geo_analysis.py     # Geographical analysis
│   ├── 03_price_analysis.py   # Price analysis & elasticity
│   └── 04_ml_insights.py      # Clustering, prediction, anomaly detection
├── dags/
│   └── pipeline_dag.py        # Apache Airflow DAG
├── dashboard/
│   ├── index.html             # Main dashboard (330 KB, self-contained)
│   ├── geo.html               # Geographic analysis dashboard
│   └── products.html          # Product explorer with DataTable
├── config/
│   └── settings.yaml          # YAML configuration
├── docker-compose.yml         # Airflow stack
└── requirements.txt           # Python dependencies
```

---

## Configuration

### `config/settings.yaml`

| Section | Key | Default | Description |
|---------|-----|---------|-------------|
| `crawler` | `rate_limit` | `2.0` | Seconds between requests |
| `crawler` | `max_retries` | `3` | Retry attempts on failure |
| `ai_extraction` | `provider` | `auto` | `auto` / `anthropic` / `ollama` |
| `ai_extraction` | `ollama_model` | `qwen2.5:7b` | Ollama model to use |
| `ai_extraction` | `ollama_base_url` | `http://localhost:11434` | Ollama server URL |
| `ai_extraction` | `ollama_timeout` | `60` | Request timeout (seconds) |
| `etl.normalization` | `target_currency` | `USD` | Target currency |
| `etl.deduplication` | `name_threshold` | `0.85` | Name similarity threshold |
| `etl.deduplication` | `supplier_threshold` | `0.8` | Supplier similarity threshold |
| `warehouse` | `sqlite.path` | `data/warehouse.db` | SQLite database path |
| `warehouse` | `parquet.path` | `data/warehouse.parquet` | Parquet file path |

---

## Data Model

Each product record (Pydantic `Product` model):

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | `str` | Unique identifier |
| `name` | `str` | Product name |
| `price_min` | `float?` | Minimum price (USD) |
| `price_max` | `float?` | Maximum price (USD) |
| `currency` | `str` | ISO 4217 code (normalized to USD) |
| `moq` | `int?` | Minimum order quantity |
| `unit` | `str?` | Unit of measurement |
| `supplier_name` | `str?` | Supplier company name |
| `supplier_rating` | `float?` | Rating 0–5 |
| `supplier_location` | `str?` | Raw location string |
| `verified_supplier` | `bool?` | Verification status |
| `response_rate` | `float?` | Response rate 0–100% |
| `certifications` | `list[str]` | Certifications list |
| `keywords` | `list[str]` | Extracted keywords |
| `category` | `str?` | Product category |
| `subcategory` | `str?` | Product subcategory |
| `description` | `str?` | Product description |
| `listing_url` | `str?` | Product page URL |
| `scraped_at` | `float` | Unix timestamp |
| `supplier_city` | `str?` | Enriched city |
| `supplier_state` | `str?` | Enriched state |
| `supplier_region` | `str?` | Enriched region (North/South/etc.) |
| `entities` | `list[dict]` | NLP extracted entities |

---

## Extending the System

### Add a New Crawler
1. Create `crawler/newexchange_crawler.py` inheriting `BaseCrawler`
2. Implement `search_products()`, `parse_product_listing()`, `parse_product_detail()`
3. Add to `dags/pipeline_dag.py` if using Airflow

### Add a New ETL Step
1. Create module in `etl/` with an `enrich_product(product)` function
2. Insert it into the pipeline chain in the main script or DAG

### Add a New ML Model
1. Add analysis logic to an existing EDA script or create a new one
2. Add required dependencies to `requirements.txt`

### Customize the Dashboard
1. Edit `dashboard/build_html.py` then regenerate:
   ```bash
   python dashboard/build_html.py
   ```
2. Or directly edit the generated `.html` files

---

## Output

| Artifact | Location | Format |
|----------|----------|--------|
| Raw crawled data | `data/raw/` | JSON |
| Processed warehouse | `data/warehouse.db` | SQLite |
| Processed warehouse | `data/warehouse.parquet` | Parquet |
| Charts & figures | `eda/*.png` | PNG |
| Dashboard | `dashboard/*.html` | HTML (standalone) |
| Logs | `logs/pipeline.log` | Text |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Scraping | `requests`, `BeautifulSoup4`, `fake-useragent` |
| AI Extraction | Ollama + Qwen 2.5 (default) or Anthropic Claude |
| Data Validation | `pydantic` v2 |
| ETL | `pandas`, `numpy`, `spaCy`, `forex-python` |
| Storage | JSON → SQLite + Parquet via `pyarrow` |
| EDA | `matplotlib`, `seaborn`, `plotly`, `wordcloud` |
| ML | `scikit-learn` (KMeans, IsolationForest, RandomForest), `gensim` (LDA) |
| Orchestration | Apache Airflow (optional) |
| Dashboard | Chart.js v4, DataTables, Tailwind CSS, Font Awesome |

---

## License

MIT License — free to use and modify.
