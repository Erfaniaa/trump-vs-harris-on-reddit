# US-Iran Conflict Prediction Analyzer

Analyze Reddit sentiment, Polymarket odds, and multi-source news to predict the likelihood of US military action against Iran.

## Features

- **Reddit Sentiment Analysis**: Gathers and analyzes comments from political subreddits
- **Polymarket Integration**: Fetches real-time prediction market odds and trader opinions
- **Multi-Source News**: Aggregates news from 10+ APIs (GDELT, NewsAPI, GNews, etc.)
- **Financial Market Analysis**: Tracks gold and crypto prices as conflict indicators
- **LLM Deep Analysis**: Uses Claude AI for sophisticated reasoning and predictions
- **Comprehensive Reports**: Generates detailed English and Persian reports with charts

## Project Structure

```
├── main.py                 # Entry point
├── credentials.py          # API keys (not in git)
├── requirements.txt        # Dependencies
├── src/
│   ├── core/               # Core infrastructure
│   │   ├── config.py       # Configuration settings
│   │   └── cache_manager.py # Data caching
│   ├── data/               # Data collection modules
│   │   ├── data_gatherer.py      # Reddit data collection
│   │   ├── polymarket_fetcher.py # Polymarket API
│   │   ├── news_aggregator.py    # Multi-source news
│   │   └── market_analyzer.py    # Financial markets
│   ├── analysis/           # Analysis modules
│   │   ├── scenario_analyzer.py      # Sentiment analysis
│   │   ├── llm_analyzer.py           # Claude AI analysis
│   │   ├── reasoning_framework.py    # Bayesian reasoning
│   │   └── user_opinion_summarizer.py
│   └── reporting/          # Report generation
│       ├── report_generator.py       # Markdown reports
│       ├── chart_generator.py        # Visualizations
│       ├── visualization_helpers.py
│       ├── investment_advisor.py
│       └── polymarket_betting_strategy.py
└── cache/                  # Runtime data (gitignored)
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/iran-conflict-prediction.git
   cd iran-conflict-prediction
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Create `credentials.py` with your API keys:
   ```python
   # Reddit API (required)
   CLIENT_ID = "your_reddit_client_id"
   CLIENT_SECRET = "your_reddit_client_secret"
   
   # Anthropic API (for LLM analysis)
   ANTHROPIC_API_KEY = "your_anthropic_key"
   
   # News APIs (optional, enhances analysis)
   NEWSAPI_KEY = ""
   GNEWS_API_KEY = ""
   WORLDNEWS_API_KEY = ""
   ALPHAVANTAGE_API_KEY = ""
   ```

4. (Optional) Edit `src/core/config.py` to customize settings.

## Usage

```bash
# Full analysis (gather + analyze + report)
python3 main.py

# Use cached data (skip gathering)
python3 main.py --skip-gather

# Use cached analysis (skip processing)
python3 main.py --skip-analyze

# Quick mode (less data, faster)
python3 main.py --quick

# Skip LLM analysis
python3 main.py --no-llm

# Show cache status
python3 main.py --cache-status

# Clear all cached data
python3 main.py --clear-cache

# Only show Polymarket odds
python3 main.py --polymarket-only
```

## Output

Reports are generated in `cache/reports/`:
- `report_EN.md` - English report with analysis and charts
- `report_FA.md` - Persian report with RTL support

## API Requirements

- **Reddit API**: Required for comment gathering ([Get credentials](https://www.reddit.com/prefs/apps))
- **Anthropic API**: Required for LLM analysis ([Get API key](https://console.anthropic.com/))
- **News APIs**: Optional, but recommended for comprehensive analysis

## License

MIT License - see [LICENSE](LICENSE) file.
