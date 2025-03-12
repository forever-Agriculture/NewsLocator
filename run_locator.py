#!/usr/bin/env python3
# run_locator.py
"""
Main runner script for NewsLocator application.

This script orchestrates the collection of news articles from RSS feeds and their
analysis to identify cities mentioned in or related to the content. It saves both
the collected articles and analysis results to JSON files.

Usage:
    python run_locator.py

Dependencies:
    - collector: For fetching articles from RSS feeds
    - analyzer: For identifying cities in article content
    - logging: For tracking execution
    - os, json, datetime: For file operations and timestamps

Example:
    >>> python run_locator.py
    🚀 Starting NewsLocator process
    📰 Collecting articles from Fox News
    🔍 Analyzing articles for city mentions
    ✅ Process complete! Results saved to output/analysis_2025-03-01.json
"""

import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from src.collector import collect_articles
from src.analyzer import analyze_locations

# Load environment variables
load_dotenv()

# Create necessary directories first
def ensure_directories():
    """
    Create necessary directories for the application if they don't exist.
    
    Creates 'data', 'output', and 'logs' directories to store collected articles,
    analysis results, and log files respectively.
    """
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

# Create directories before setting up logging
ensure_directories()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/locator.log"),
    ],
)
logger = logging.getLogger("newslocator")


def run():
    """
    Run the NewsLocator process.
    
    Collects articles from Fox News RSS feed, analyzes them to identify
    mentioned cities, and saves both the collected articles and analysis results
    to JSON files with timestamps.
    """
    logger.info("Starting NewsLocator process")
    print("🚀 Starting NewsLocator process")
    
    # Get current date for filenames
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Collect articles from RSS feeds
    print("📰 Collecting articles from Fox News")
    articles = collect_articles()
    
    # Save collected articles to JSON
    articles_file = f"data/articles_{current_date}.json"
    with open(articles_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2)
    
    logger.info(f"Collected {len(articles)} articles and saved to {articles_file}")
    
    # Analyze articles for city mentions
    print("🔍 Analyzing articles for city mentions")
    analysis_results = analyze_locations(articles)
    
    # Save analysis results to JSON
    analysis_file = f"output/analysis_{current_date}.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Analysis complete and saved to {analysis_file}")
    print(f"✅ Process complete! Results saved to {analysis_file}")


if __name__ == "__main__":
    run() 