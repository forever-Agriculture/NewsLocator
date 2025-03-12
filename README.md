# NewsLocator

*Identifying geographic focus in news articles*

## Project Overview

NewsLocator is a specialized tool that analyzes news articles to identify which cities they are related to. The application collects recent articles from Fox News RSS feeds, processes them, and uses DeepSeek AI to determine geographic relevance.

## Features

- Efficient RSS parsing with minimal dependencies
- AI-powered location detection
- Detailed rationale for city associations
- Batch processing to optimize API usage
- Configurable news sources

## Setup

### Prerequisites

- Python 3.8 or higher
- DeepSeek API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/NewsLocator.git
cd NewsLocator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your DeepSeek API key:
```
# API Keys
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# Configuration
INTER_SOURCE_DELAY=5
INTER_BATCH_DELAY=2
MAX_ARTICLES_PER_FEED=5
```

## Usage

Run the main script to collect and analyze articles:

```bash
python run_locator.py
```

The application will:
1. Collect the most recent articles from Fox News
2. Save the raw articles to `data/articles_[date].json`
3. Analyze each article to identify mentioned cities
4. Save the analysis results to `output/analysis_[date].json`

## Sample Output

```json
[
  {
    "title": "Manhunt underway for Philly driver who opened fire on teen",
    "description": "A manhunt is underway for a driver accused of shooting...",
    "link": "https://www.foxnews.com/us/manhunt-underway-philly-driver...",
    "categories": ["fox-news/us/philadelphia", "fox-news/crime"],
    "source": "fox_news",
    "cities": ["Philadelphia"],
    "rationale": "The article explicitly mentions 'West Philadelphia' as the location where the road rage incident occurred."
  }
]
```

## Configuration

The application can be configured through environment variables:

- `DEEPSEEK_API_KEY`: Your DeepSeek API key
- `DEEPSEEK_MODEL`: The DeepSeek model to use (default: deepseek-chat)
- `MAX_ARTICLES_PER_FEED`: Number of articles to collect per feed (default: 5)
- `INTER_SOURCE_DELAY`: Delay between feed requests in seconds (default: 5)
- `INTER_BATCH_DELAY`: Delay between analysis batches in seconds (default: 2)

## Project Structure

```
NewsLocator/
├── src/
│   ├── __init__.py
│   ├── collector.py  # RSS feed collection
│   └── analyzer.py   # City analysis with DeepSeek
├── data/             # Collected articles
├── output/           # Analysis results
├── logs/             # Application logs
├── .env              # Configuration
├── requirements.txt
└── run_locator.py    # Main script
```

## License

© 2025 NewsLocator. All rights reserved.
