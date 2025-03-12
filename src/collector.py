"""
News article collector for NewsLocator application.

This module handles the collection of news articles from RSS feeds,
specifically from Fox News. It fetches, parses, and normalizes the
article data for further processing.

Dependencies:
    - feedparser: For RSS feed parsing
    - tenacity: For retry logic on network errors
    - logging: For error tracking
    - dotenv: For environment variable loading

Usage:
    >>> from src.collector import collect_articles
    >>> articles = collect_articles()
    >>> print(f"Collected {len(articles)} articles")
"""

import logging
import os
import time
from typing import Dict, List, Any

import feedparser
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("newslocator.collector")

# Configuration
MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", "5"))
INTER_SOURCE_DELAY = int(os.getenv("INTER_SOURCE_DELAY", "5"))

# Fox News RSS feed URL
FOX_NEWS_RSS_URL = "https://moxie.foxnews.com/google-publisher/us.xml"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception)),
)
def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """
    Fetch and parse an RSS feed with retry logic.
    
    Args:
        url (str): The URL of the RSS feed to fetch
        
    Returns:
        feedparser.FeedParserDict: The parsed feed
        
    Raises:
        Exception: If the feed cannot be fetched after retries
    """
    logger.info(f"Fetching feed from {url}")
    feed = feedparser.parse(url)
    
    if feed.get("bozo_exception"):
        logger.error(f"Error parsing feed: {feed.bozo_exception}")
        raise Exception(f"Failed to parse feed: {feed.bozo_exception}")
    
    return feed


def parse_fox_news_feed(feed: feedparser.FeedParserDict) -> List[Dict[str, Any]]:
    """
    Parse Fox News RSS feed into a list of article dictionaries.
    
    Args:
        feed (feedparser.FeedParserDict): The parsed Fox News RSS feed
        
    Returns:
        list: List of article dictionaries with normalized data
    """
    articles = []
    
    for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
        # Extract categories if available
        categories = []
        if hasattr(entry, "tags"):
            categories = [tag.term for tag in entry.tags if hasattr(tag, "term")]
        
        # Extract content from the entry
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary
        
        # Create normalized article dictionary
        article = {
            "title": entry.get("title", ""),
            "published": entry.get("published", ""),
            "description": entry.get("description", ""),
            "content": content,
            "link": entry.get("link", ""),
            "categories": categories,
            "source": "fox_news",
        }
        
        articles.append(article)
    
    return articles


def collect_articles() -> List[Dict[str, Any]]:
    """
    Collect articles from Fox News RSS feed.
    
    Returns:
        list: List of article dictionaries with normalized data
    """
    all_articles = []
    
    try:
        # Fetch and parse Fox News feed
        feed = fetch_feed(FOX_NEWS_RSS_URL)
        articles = parse_fox_news_feed(feed)
        
        logger.info(f"Collected {len(articles)} articles from Fox News")
        all_articles.extend(articles)
        
    except Exception as e:
        logger.error(f"Error collecting articles from Fox News: {e}")
    
    return all_articles


if __name__ == "__main__":
    # For testing the module directly
    logging.basicConfig(level=logging.INFO)
    articles = collect_articles()
    print(f"Collected {len(articles)} articles")
    for article in articles:
        print(f"- {article['title']}") 