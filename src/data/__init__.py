"""
Data collection modules - Reddit, Polymarket, News, and Market data.
"""

from .data_gatherer import DataGatherer, CommentData, PostData, GatheringStats
from .polymarket_fetcher import PolymarketFetcher, MarketData
from .news_aggregator import NewsAggregator, NewsArticle, NewsAnalysis
from .market_analyzer import MarketAnalyzer

__all__ = [
    'DataGatherer', 'CommentData', 'PostData', 'GatheringStats',
    'PolymarketFetcher', 'MarketData',
    'NewsAggregator', 'NewsArticle', 'NewsAnalysis',
    'MarketAnalyzer',
]
