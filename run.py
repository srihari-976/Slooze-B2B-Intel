#!/usr/bin/env python3
"""
Slooze B2B Intel — one-command pipeline runner.

Usage:
    python run.py              # scrapes + loads + builds dashboard
    python run.py --no-scrape  # skip scraping, rebuild dashboard from cached data
    python run.py --help       # full options
"""

import os, sys, subprocess, argparse, json
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def run(cmd, **kw):
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, cwd=ROOT, **kw)

def check_deps():
    missing = []
    for mod in ['requests', 'bs4', 'pandas', 'pyarrow', 'pydantic']:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        step("Installing missing dependencies")
        run(f"{sys.executable} -m pip install {' '.join(missing)}")
    # optional extras
    for mod, label in [('spacy', 'spacy'), ('forex_python', 'forex-python')]:
        try:
            __import__(mod)
        except ImportError:
            try:
                run(f"{sys.executable} -m pip install {label}")
            except:
                pass

def ensure_spacy():
    try:
        import spacy
        spacy.load("en_core_web_sm")
    except:
        step("Downloading spaCy model")
        run(f"{sys.executable} -m spacy download en_core_web_sm")

def scrape():
    step("Scraping TradeIndia for real product data")
    result = run(f"{sys.executable} crawler/tradeindia_scraper.py")
    return result.returncode == 0

def build_dashboard():
    step("Building dashboard HTML files")
    result = run(f"{sys.executable} dashboard/build_html.py")
    return result.returncode == 0

def show_summary():
    data_file = ROOT / "data" / "scraped_products.json"
    if data_file.exists():
        with open(data_file) as f:
            products = json.load(f)
        cats = {}
        for p in products:
            c = p.get("category", "Other")
            cats[c] = cats.get(c, 0) + 1
        print(f"\n  Products scraped: {len(products)}")
        for c, n in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"    {c}: {n}")
    print(f"\n  Dashboard: {ROOT/'dashboard/index.html'}")
    print(f"  Open that file in your browser.")

def main():
    parser = argparse.ArgumentParser(description="Slooze B2B Intel pipeline")
    parser.add_argument("--no-scrape", action="store_true", help="Skip scraping, rebuild dashboard from cached data")
    args = parser.parse_args()

    os.makedirs(ROOT / "data", exist_ok=True)

    check_deps()
    ensure_spacy()

    if not args.no_scrape:
        ok = scrape()
        if not ok:
            print("\n  Scrape had issues — check network or site access.")
            print("  Cached data (if any) will still be used for the dashboard.\n")
    else:
        print("  Skipping scrape (--no-scrape)")

    build_dashboard()
    show_summary()

    print(f"\n{'='*60}")
    print(f"  Done. Open dashboard/index.html in your browser.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
