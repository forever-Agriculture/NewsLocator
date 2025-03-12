"""
City location analyzer for news articles using DeepSeek API.

This module analyzes news articles to identify cities mentioned in or related to
the content. It uses the DeepSeek API to process article text and extract city
references with supporting rationale. The analysis is performed in batches to
optimize API usage, with configurable delays between requests.

Dependencies:
    - openai: For DeepSeek API integration
    - tenacity: For retry logic on API errors
    - logging: For error tracking
    - dotenv: For environment variable loading

Usage:
    >>> from src.analyzer import analyze_locations
    >>> articles = [{"title": "London faces flooding", "description": "Heavy rain in UK capital"}]
    >>> results = analyze_locations(articles)
    >>> print(results[0]["cities"])
    ["London"]
"""

import json
import logging
import os
import time
from typing import Dict, List, Any

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("newslocator.analyzer")

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BATCH_SIZE = 3  # Process articles in batches of 3
INTER_BATCH_DELAY = int(os.getenv("INTER_BATCH_DELAY", "2"))  # Use a separate env var with shorter default


class LocationAnalyzer:
    """
    Analyzes news articles to identify mentioned cities using DeepSeek API.
    
    This class handles the processing of news articles to extract city references,
    managing API requests, retries, and response parsing. It uses a structured prompt
    to guide the AI in identifying cities with supporting rationale.
    """
    
    def __init__(self):
        """
        Initialize the LocationAnalyzer with DeepSeek API client.
        
        Sets up the OpenAI client configured for DeepSeek API access and defines
        the prompt template for city identification.
        """
        self.client = OpenAI(
            base_url="https://api.deepseek.com/v1",
            api_key=DEEPSEEK_API_KEY,
            timeout=30.0,
        )
        self.model = "deepseek-chat"
        
        # Prompt template for city identification
        self.prompt_template = """
            You are a geographic analysis expert specializing in identifying cities mentioned in news articles.

            TASK:
            Analyze the following news article and identify which cities are mentioned or directly related to the content.

            ARTICLE:
            Title: {title}
            Description: {description}
            Categories: {categories}

            INSTRUCTIONS:
            1. Identify all cities explicitly mentioned in the article.
            2. Identify cities that are strongly implied or directly related to the content.
            3. If no cities are explicitly mentioned, make an educated guess about which cities might be related based on context clues.
            4. Do NOT include countries, regions, states, or other non-city locations.
            5. Provide a detailed rationale for each city you identify or guess.

            RESPONSE FORMAT:
            Respond in valid JSON format with the following structure:
            {{
            "cities": ["City1", "City2", ...],
            "rationale": "Your explanation for why these cities are mentioned or related to the article"
            }}

            Even if no cities are explicitly mentioned, provide your best guess based on context:
            {{
            "cities": ["GuessedCity1", "GuessedCity2"],
            "rationale": "While no cities are explicitly mentioned, the article likely relates to [GuessedCity1] because... and [GuessedCity2] because..."
            }}

            Only in cases where it's impossible to make any reasonable guess, return:
            {{
            "cities": [],
            "rationale": "No specific cities are mentioned or can be reasonably inferred from this article."
            }}
            """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception)),
    )
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze a single article to identify mentioned cities.
        
        Sends the article content to the DeepSeek API with a structured prompt
        and parses the response to extract cities and rationale.
        
        Args:
            article (dict): Article dictionary with title, description, and categories
            
        Returns:
            dict: The original article with added 'cities' and 'rationale' fields
            
        Raises:
            Exception: If the API request fails after retries
        """
        # Format the prompt with article content
        categories_str = ", ".join(article.get("categories", []))
        prompt = self.prompt_template.format(
            title=article.get("title", ""),
            description=article.get("description", ""),
            categories=categories_str,
        )
        
        try:
            # Call DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            
            # Extract and parse the response
            content = response.choices[0].message.content if response.choices else ""
            
            # Extract JSON from the response - handle code block format
            try:
                # Check if response is in a code block format (```json ... ```)
                if "```json" in content:
                    # Extract content between ```json and ```
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                        result = json.loads(json_content)
                    else:
                        # Fallback to trying to parse the whole content
                        result = json.loads(content)
                else:
                    # Try to find JSON content directly
                    json_match = content.strip()
                    if not json_match.startswith("{"):
                        # Try to find the start of JSON
                        start_idx = content.find("{")
                        if start_idx != -1:
                            json_match = content[start_idx:]
                    
                    result = json.loads(json_match)
                
                # Ensure expected fields exist
                if "cities" not in result:
                    result["cities"] = []
                if "rationale" not in result:
                    result["rationale"] = "No rationale provided"
                    
                # Add analysis results to the article
                article_result = article.copy()
                article_result["cities"] = result["cities"]
                article_result["rationale"] = result["rationale"]
                return article_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response as JSON: {e}")
                logger.error(f"Raw response: {content}")
                
                # Return article with error information
                article_result = article.copy()
                article_result["cities"] = []
                article_result["rationale"] = "Error parsing analysis results"
                article_result["error"] = str(e)
                return article_result
                
        except Exception as e:
            logger.error(f"API request failed: {e}")
            
            # Return article with error information
            article_result = article.copy()
            article_result["cities"] = []
            article_result["rationale"] = f"Error: {str(e)}"
            return article_result

    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Analyze a batch of articles for city mentions.
        
        Processes each article in the batch individually, with a small delay
        between requests to avoid rate limiting.
        
        Args:
            articles (list): List of article dictionaries to analyze
            
        Returns:
            list: The articles with added city analysis results
        """
        results = []
        
        for i, article in enumerate(articles):
            try:
                logger.info(f"Analyzing article: {article.get('title', 'Untitled')[:50]}...")
                result = self.analyze_article(article)
                results.append(result)
                
                # Add a small delay between articles (except for the last one)
                if i < len(articles) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to analyze article: {e}")
                # Add the article with an error flag
                article_copy = article.copy()
                article_copy["cities"] = []
                article_copy["rationale"] = "Analysis failed"
                article_copy["error"] = str(e)
                results.append(article_copy)
                
        return results


def analyze_locations(articles: List[Dict]) -> List[Dict]:
    """
    Analyze a list of articles to identify mentioned cities.
    
    Processes articles in batches to optimize API usage, with configurable
    delays between batches to avoid rate limiting.
    
    Args:
        articles (list): List of article dictionaries to analyze
        
    Returns:
        list: The articles with added city analysis results
    """
    analyzer = LocationAnalyzer()
    results = []
    
    # Process articles in batches
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        logger.info(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} articles)")
        
        batch_results = analyzer.analyze_batch(batch)
        results.extend(batch_results)
        
        # Add a shorter delay between batches (except for the last one)
        if i + BATCH_SIZE < len(articles):
            logger.info(f"Sleeping for {INTER_BATCH_DELAY} seconds before next batch")
            time.sleep(INTER_BATCH_DELAY)
    
    logger.info(f"Analysis complete for {len(results)} articles")
    return results


if __name__ == "__main__":
    # For testing the module directly
    test_articles = [
        {
            "title": "London faces flooding risk as Thames barrier tested",
            "description": "The UK capital prepares for potential flooding as climate change increases risks.",
            "categories": ["uk", "environment"],
        }
    ]
    
    results = analyze_locations(test_articles)
    print(json.dumps(results, indent=2)) 