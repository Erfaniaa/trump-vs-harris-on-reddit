# Repo Map

## Overview
Analyzes signals about potential US action against Iran using Reddit sentiment, Polymarket odds and trader behavior, multi-source news, and financial markets (gold/crypto). Produces English and Persian markdown reports and charts.

## Key Entry Points
- `main.py` - CLI entry point and pipeline orchestration.
- `src/core/config.py` - Central configuration and feature flags.
- `src/core/cache_manager.py` - Cache read/write and cache status.

## Data Collection
- `src/data/data_gatherer.py` - Reddit data collection.
- `src/data/polymarket_fetcher.py` - Polymarket API fetch, parsing, and **cross-market smart money analysis** (Iran/Gold/BTC/Russia-Ukraine/China/Stocks trader intelligence).
- `src/data/news_aggregator.py` - Multi-source news aggregation.
- `src/data/market_analyzer.py` - Financial market indicators (gold/crypto).

## Analysis
- `src/analysis/scenario_analyzer.py` - Scenario and sentiment analysis logic.
- `src/analysis/llm_analyzer.py` - LLM-driven analysis.
- `src/analysis/reasoning_framework.py` - Bayesian reasoning framework.
- `src/analysis/user_opinion_summarizer.py` - Summarize opinions.

## Reporting & Visualization
- `src/reporting/report_generator.py` - Markdown report generation (EN/FA). **Very large module; candidate for split into smaller section builders.**
- `src/reporting/geopolitical_section.py` - Geopolitical analysis section builder.
- `src/reporting/chart_generator.py` - Chart creation.
- `src/reporting/visualization_helpers.py` - Chart helpers and layout.
- `src/reporting/investment_advisor.py` - Portfolio suggestions and guidance.
- `src/reporting/polymarket_betting_strategy.py` - Betting strategy outputs.
- `src/reporting/social_media_generator.py` - Social media derivatives.

## Other Files
- `news_aggregator.py`, `polymarket_fetcher.py` - Legacy/alternate top-level scripts.
- `credentials.py` - API keys (local only).
- `requirements.txt` - Python dependencies.
- `cache/` - Runtime data, reports, and generated images (gitignored).

## Module Split Targets (planned)
- `src/reporting/report_generator.py` → split into smaller section modules:
  - `src/reporting/sections/summary.py`
  - `src/reporting/sections/polymarket_section.py`
  - `src/reporting/sections/markets_section.py`
  - `src/reporting/sections/investment_section.py`
  - `src/reporting/sections/appendices.py`
