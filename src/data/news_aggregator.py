"""
News Aggregator - Multi-source news collection and analysis for Iran conflict prediction.

Integrates multiple free news APIs to provide comprehensive coverage:
1. NewsAPI (newsapi.org) - 100 requests/day free
2. GNews (gnews.io) - 100 requests/day free
3. GDELT (gdeltproject.org) - Unlimited, no key needed
4. Hacker News (ycombinator) - Unlimited, no key needed
5. World News API (worldnewsapi.com) - 1500 requests/month free
6. Alpha Vantage (alphavantage.co) - 25 requests/day free, has sentiment

API Key Registration Links:
- NewsAPI: https://newsapi.org/register
- GNews: https://gnews.io/register
- World News API: https://worldnewsapi.com/register
- Alpha Vantage: https://www.alphavantage.co/support/#api-key

Created: February 4, 2026
"""

import requests
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter
import json
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    from src.core.config import (
        INCLUDE_PERSIAN_LANGUAGE_SOURCES,
        PERSIAN_RSS_FEEDS,
        INCLUDE_ENGLISH_RSS_SOURCES,
        ENGLISH_RSS_FEEDS,
        MAX_CONCURRENT_WORKERS,
    )
except Exception:
    INCLUDE_PERSIAN_LANGUAGE_SOURCES = False
    PERSIAN_RSS_FEEDS = []
    INCLUDE_ENGLISH_RSS_SOURCES = False
    ENGLISH_RSS_FEEDS = []
    MAX_CONCURRENT_WORKERS = 16

# Import credentials (API keys) - stays at project root
try:
    import credentials
    NEWSAPI_KEY = getattr(credentials, 'NEWSAPI_KEY', '')
    GNEWS_API_KEY = getattr(credentials, 'GNEWS_API_KEY', '')
    WORLDNEWS_API_KEY = getattr(credentials, 'WORLDNEWS_API_KEY', '')
    ALPHAVANTAGE_API_KEY = getattr(credentials, 'ALPHAVANTAGE_API_KEY', '')
except ImportError:
    # Fallback to empty strings if not configured
    NEWSAPI_KEY = ""
    GNEWS_API_KEY = ""
    WORLDNEWS_API_KEY = ""
    ALPHAVANTAGE_API_KEY = ""


@dataclass
class NewsArticle:
    """Represents a single news article."""
    title: str
    description: str
    source: str
    url: str
    published_at: str
    sentiment: float = 0.0  # -1 to 1
    relevance_score: float = 0.0  # 0 to 1
    api_source: str = ""  # Which API provided this
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NewsAnalysis:
    """Aggregated news analysis results."""
    total_articles: int = 0
    pro_strike_articles: int = 0
    anti_strike_articles: int = 0
    neutral_articles: int = 0
    average_sentiment: float = 0.0
    key_themes: List[str] = field(default_factory=list)
    top_sources: List[Tuple[str, int]] = field(default_factory=list)
    timeline: Dict[str, int] = field(default_factory=dict)
    articles: List[NewsArticle] = field(default_factory=list)
    api_sources_used: List[str] = field(default_factory=list)
    fetch_timestamp: str = ""
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['articles'] = [a.to_dict() if hasattr(a, 'to_dict') else a for a in self.articles]
        return result


class NewsAggregator:
    """
    Aggregates news from multiple sources for comprehensive Iran conflict analysis.
    
    Sources:
    - NewsAPI: General news with keyword search
    - GNews: Google News alternative with trending articles
    - GDELT: Geopolitical event database (no key needed)
    - Hacker News: Tech community discussions (no key needed)
    - World News API: Global news with built-in sentiment
    - Alpha Vantage: Financial news sentiment
    """
    
    # Iran/conflict related keywords for searching
    SEARCH_KEYWORDS = [
        "Iran strike",
        "Iran attack",
        "US Iran military",
        "Iran nuclear",
        "Trump Iran",
        "Iran sanctions",
        "IRGC",
        "Iran Israel",
        "Persian Gulf",
        "Iran war",
        "Tehran",
        "Khamenei",
        "Iran protests",
        "Iran regime"
    ]
    
    # Pro-strike indicators
    PRO_STRIKE_KEYWORDS = [
        "strike imminent", "military action", "attack planned", "strike ready",
        "bombing", "air strike", "missile strike", "carrier deployed",
        "B-2 bomber", "F-35", "military buildup", "invasion", "regime change",
        "decapitation strike", "surgical strike", "preemptive", "retaliation"
    ]
    
    # Anti-strike/de-escalation indicators
    ANTI_STRIKE_KEYWORDS = [
        "diplomacy", "negotiations", "talks", "peace", "deal", "agreement",
        "de-escalation", "backchannel", "diplomatic", "ceasefire", "truce",
        "compromise", "dialogue", "mediator", "mediation"
    ]
    
    # Rate limiting settings (requests per minute)
    RATE_LIMITS = {
        "newsapi": 10,
        "gnews": 10,
        "gdelt": 30,  # More generous
        "hackernews": 30,
        "worldnews": 10,
        "alphavantage": 5
    }
    
    def __init__(self):
        """Initialize the news aggregator."""
        self.last_request_time = {}
        self.request_counts = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "IranConflictAnalyzer/1.0 (Research Project)"
        })
    
    def _rate_limit(self, api_name: str):
        """Implement rate limiting for API calls."""
        now = time.time()
        min_interval = 60.0 / self.RATE_LIMITS.get(api_name, 10)
        
        if api_name in self.last_request_time:
            elapsed = now - self.last_request_time[api_name]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        
        self.last_request_time[api_name] = time.time()
    
    def _calculate_sentiment(self, text: str) -> float:
        """
        Calculate sentiment score for text based on keyword analysis.
        Returns float between -1 (anti-strike) and 1 (pro-strike).
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        pro_count = sum(1 for kw in self.PRO_STRIKE_KEYWORDS if kw.lower() in text_lower)
        anti_count = sum(1 for kw in self.ANTI_STRIKE_KEYWORDS if kw.lower() in text_lower)
        
        total = pro_count + anti_count
        if total == 0:
            return 0.0
        
        # Normalize to -1 to 1 range
        sentiment = (pro_count - anti_count) / total
        return round(sentiment, 2)

    def fetch_persian_rss(self, max_items_per_feed: int = 30) -> List[NewsArticle]:
        """
        Fetch Persian-language news from public RSS feeds (no API key).
        This is optional and controlled by config.INCLUDE_PERSIAN_LANGUAGE_SOURCES.
        """
        if not INCLUDE_PERSIAN_LANGUAGE_SOURCES or not PERSIAN_RSS_FEEDS:
            return []

        articles: List[NewsArticle] = []

        # Very lightweight Persian sentiment cues for "strike vs diplomacy" framing.
        pro = ["حمله", "بمباران", "موشک", "جنگ", "درگیری", "حمله آمریکا", "حمله اسرائیل"]
        anti = ["مذاکره", "توافق", "دیپلماسی", "کاهش تنش", "آتش‌بس", "گفت‌وگو", "میانجی"]

        for feed in PERSIAN_RSS_FEEDS:
            name = feed.get("name", "Persian RSS")
            url = feed.get("url", "")
            if not url:
                continue
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()

                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                # Atom fallback
                if not items:
                    items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

                for item in items[:max_items_per_feed]:
                    title = (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()

                    # RSS: <link>text</link> ; Atom: <link href="..."/>
                    link = (item.findtext("link") or "").strip()
                    if not link:
                        link_el = item.find("{http://www.w3.org/2005/Atom}link")
                        if link_el is not None:
                            link = (link_el.attrib.get("href") or "").strip()

                    pub = (
                        item.findtext("pubDate")
                        or item.findtext("{http://www.w3.org/2005/Atom}updated")
                        or item.findtext("{http://www.w3.org/2005/Atom}published")
                        or ""
                    ).strip()

                    if not title or not link:
                        continue

                    s = 0.0
                    if any(k in title for k in pro):
                        s += 0.4
                    if any(k in title for k in anti):
                        s -= 0.4

                    articles.append(NewsArticle(
                        title=title,
                        description="",
                        source=name,
                        url=link,
                        published_at=pub,
                        sentiment=s,
                        relevance_score=self._calculate_relevance(title),
                        api_source="RSS-FA",
                    ))
            except Exception:
                continue

        return articles

    def fetch_english_rss(self, max_items_per_feed: int = 40) -> List[NewsArticle]:
        """
        Fetch English-language news from public RSS feeds (no API key).
        This is optional and controlled by config.INCLUDE_ENGLISH_RSS_SOURCES.
        """
        if not INCLUDE_ENGLISH_RSS_SOURCES or not ENGLISH_RSS_FEEDS:
            return []

        articles: List[NewsArticle] = []

        for feed in ENGLISH_RSS_FEEDS:
            name = feed.get("name", "English RSS")
            url = feed.get("url", "")
            if not url:
                continue
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()

                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                if not items:
                    # Atom fallback
                    items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

                for item in items[:max_items_per_feed]:
                    title = (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                    desc = (item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()

                    link = (item.findtext("link") or "").strip()
                    if not link:
                        link_el = item.find("{http://www.w3.org/2005/Atom}link")
                        if link_el is not None:
                            link = (link_el.attrib.get("href") or "").strip()

                    pub = (
                        item.findtext("pubDate")
                        or item.findtext("{http://www.w3.org/2005/Atom}updated")
                        or item.findtext("{http://www.w3.org/2005/Atom}published")
                        or ""
                    ).strip()

                    if not title or not link:
                        continue

                    full_text = f"{title} {desc}".strip()
                    articles.append(NewsArticle(
                        title=title,
                        description=(desc[:500] if desc else ""),
                        source=name,
                        url=link,
                        published_at=pub,
                        sentiment=self._calculate_sentiment(full_text),
                        relevance_score=self._calculate_relevance(full_text),
                        api_source="RSS-EN",
                    ))
            except Exception:
                continue

        return articles
    
    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score for Iran conflict analysis."""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Core Iran keywords
        iran_keywords = ["iran", "tehran", "persian", "irgc", "khamenei", "araghchi"]
        conflict_keywords = ["strike", "attack", "military", "war", "nuclear", "sanctions"]
        
        iran_score = sum(1 for kw in iran_keywords if kw in text_lower)
        conflict_score = sum(1 for kw in conflict_keywords if kw in text_lower)
        
        # Relevance is high if both Iran and conflict keywords present
        relevance = min(1.0, (iran_score * 0.3 + conflict_score * 0.2))
        return round(relevance, 2)
    
    # =========================================================================
    # NewsAPI Integration (https://newsapi.org)
    # =========================================================================
    
    def fetch_newsapi(self, query: str = "Iran", days_back: int = 7) -> List[NewsArticle]:
        """
        Fetch articles from NewsAPI.
        
        Free tier: 100 requests/day, 100 articles/request
        Register at: https://newsapi.org/register
        """
        if not NEWSAPI_KEY:
            print("   ⚠️ NewsAPI key not configured. Skipping.")
            return []
        
        self._rate_limit("newsapi")
        
        articles = []
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": 100,
            "apiKey": NEWSAPI_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("articles", []):
                    title = item.get("title", "")
                    description = item.get("description", "") or ""
                    full_text = f"{title} {description}"
                    
                    article = NewsArticle(
                        title=title,
                        description=description[:500] if description else "",
                        source=item.get("source", {}).get("name", "Unknown"),
                        url=item.get("url", ""),
                        published_at=item.get("publishedAt", ""),
                        sentiment=self._calculate_sentiment(full_text),
                        relevance_score=self._calculate_relevance(full_text),
                        api_source="NewsAPI"
                    )
                    articles.append(article)
                
                print(f"   ✓ NewsAPI: {len(articles)} articles fetched")
            else:
                print(f"   ⚠️ NewsAPI error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ NewsAPI exception: {e}")
        
        return articles
    
    # =========================================================================
    # GNews API Integration (https://gnews.io)
    # =========================================================================
    
    def fetch_gnews(self, query: str = "Iran", max_articles: int = 100) -> List[NewsArticle]:
        """
        Fetch articles from GNews API.
        
        Free tier: 100 requests/day, 10 articles/request
        Register at: https://gnews.io/register
        """
        if not GNEWS_API_KEY:
            print("   ⚠️ GNews API key not configured. Skipping.")
            return []
        
        self._rate_limit("gnews")
        
        articles = []
        
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "max": min(max_articles, 10),  # Free tier limit
            "token": GNEWS_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("articles", []):
                    title = item.get("title", "")
                    description = item.get("description", "") or ""
                    full_text = f"{title} {description}"
                    
                    article = NewsArticle(
                        title=title,
                        description=description[:500] if description else "",
                        source=item.get("source", {}).get("name", "Unknown"),
                        url=item.get("url", ""),
                        published_at=item.get("publishedAt", ""),
                        sentiment=self._calculate_sentiment(full_text),
                        relevance_score=self._calculate_relevance(full_text),
                        api_source="GNews"
                    )
                    articles.append(article)
                
                print(f"   ✓ GNews: {len(articles)} articles fetched")
            else:
                print(f"   ⚠️ GNews error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ GNews exception: {e}")
        
        return articles
    
    # =========================================================================
    # GDELT API Integration (https://gdeltproject.org) - NO API KEY NEEDED
    # =========================================================================
    
    def fetch_gdelt(self, query: str = "Iran", mode: str = "artlist") -> List[NewsArticle]:
        """
        Fetch articles from GDELT Project.
        
        FREE - No API key needed!
        Largest open database of human society events.
        """
        self._rate_limit("gdelt")
        
        articles = []
        
        # GDELT DOC 2.0 API
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": f"{query} sourcelang:eng",
            "mode": mode,
            "maxrecords": 75,
            "format": "json",
            "sort": "DateDesc"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("articles", []):
                    title = item.get("title", "")
                    
                    article = NewsArticle(
                        title=title,
                        description="",  # GDELT doesn't provide descriptions
                        source=item.get("domain", "Unknown"),
                        url=item.get("url", ""),
                        published_at=item.get("seendate", ""),
                        sentiment=self._calculate_sentiment(title),
                        relevance_score=self._calculate_relevance(title),
                        api_source="GDELT"
                    )
                    articles.append(article)
                
                print(f"   ✓ GDELT: {len(articles)} articles fetched")
            else:
                print(f"   ⚠️ GDELT error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ GDELT exception: {e}")
        
        return articles
    
    # =========================================================================
    # Hacker News API Integration - NO API KEY NEEDED
    # =========================================================================
    
    def fetch_hackernews(self, max_stories: int = 100) -> List[NewsArticle]:
        """
        Fetch Iran-related discussions from Hacker News.
        
        FREE - No API key needed!
        Tech community perspective on geopolitical events.
        """
        articles = []
        iran_keywords = ["iran", "persian", "tehran", "nuclear", "sanction", "middle east", "gulf"]
        
        try:
            # Get top and new stories
            for endpoint in ["topstories", "newstories"]:
                url = f"https://hacker-news.firebaseio.com/v0/{endpoint}.json"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    story_ids = response.json()[:max_stories]
                    
                    # Fetch stories in batches with minimal delay
                    checked = 0
                    for story_id in story_ids:
                        if checked >= 50:  # Limit checks per endpoint
                            break
                        
                        try:
                            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                            item_response = self.session.get(item_url, timeout=3)
                            checked += 1
                            
                            if item_response.status_code == 200:
                                item = item_response.json()
                                if item and item.get("title"):
                                    title = item.get("title", "").lower()
                                    
                                    # Check if Iran-related
                                    if any(kw in title for kw in iran_keywords):
                                        article = NewsArticle(
                                            title=item.get("title", ""),
                                            description=f"HN Score: {item.get('score', 0)}, Comments: {item.get('descendants', 0)}",
                                            source="Hacker News",
                                            url=item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                            published_at=datetime.fromtimestamp(item.get("time", 0)).isoformat(),
                                            sentiment=self._calculate_sentiment(item.get("title", "")),
                                            relevance_score=self._calculate_relevance(item.get("title", "")),
                                            api_source="HackerNews"
                                        )
                                        articles.append(article)
                        except:
                            continue
            
            print(f"   ✓ Hacker News: {len(articles)} relevant discussions found")
            
        except Exception as e:
            print(f"   ⚠️ Hacker News exception: {e}")
        
        return articles
    
    # =========================================================================
    # World News API Integration (https://worldnewsapi.com)
    # =========================================================================
    
    def fetch_worldnews(self, query: str = "Iran", 
                        min_sentiment: float = -1.0, 
                        max_sentiment: float = 1.0) -> List[NewsArticle]:
        """
        Fetch articles from World News API with built-in sentiment.
        
        Free tier: 1500 requests/month
        Register at: https://worldnewsapi.com/register
        """
        if not WORLDNEWS_API_KEY:
            print("   ⚠️ World News API key not configured. Skipping.")
            return []
        
        self._rate_limit("worldnews")
        
        articles = []
        
        url = "https://api.worldnewsapi.com/search-news"
        params = {
            "text": query,
            "language": "en",
            "min-sentiment": min_sentiment,
            "max-sentiment": max_sentiment,
            "number": 100,
            "api-key": WORLDNEWS_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("news", []):
                    title = item.get("title", "")
                    text = item.get("text", "") or ""
                    
                    # World News API provides sentiment directly
                    api_sentiment = item.get("sentiment", 0.0)
                    
                    article = NewsArticle(
                        title=title,
                        description=text[:500] if text else "",
                        source=item.get("source_country", "Unknown"),
                        url=item.get("url", ""),
                        published_at=item.get("publish_date", ""),
                        sentiment=api_sentiment,  # Use API's sentiment
                        relevance_score=self._calculate_relevance(f"{title} {text}"),
                        api_source="WorldNewsAPI"
                    )
                    articles.append(article)
                
                print(f"   ✓ World News API: {len(articles)} articles fetched")
            else:
                print(f"   ⚠️ World News API error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ World News API exception: {e}")
        
        return articles
    
    # =========================================================================
    # Iranian News Sources via World News API
    # =========================================================================
    
    def fetch_iranian_sources(self) -> List[NewsArticle]:
        """
        Fetch news specifically from Iranian sources via World News API.
        
        World News API monitors 70+ Iranian news sources including:
        - IRNA (Islamic Republic News Agency)
        - Fars News
        - Tasnim News
        - Mehr News
        - Press TV
        - ISNA
        
        Note: These are ENGLISH versions of Iranian state media.
        They provide the Iranian government's perspective.
        
        Free tier: 1500 requests/month
        Register at: https://worldnewsapi.com/register
        """
        if not WORLDNEWS_API_KEY:
            print("   ⚠️ World News API key not configured. Skipping Iranian sources.")
            return []
        
        self._rate_limit("worldnews")
        
        articles = []
        
        # Fetch news from Iran (country code: ir)
        url = "https://api.worldnewsapi.com/search-news"
        params = {
            "text": "Iran OR nuclear OR IRGC OR sanctions OR protests",
            "source-countries": "ir",  # Iran country code
            "language": "en",  # English language articles from Iranian sources
            "number": 50,
            "api-key": WORLDNEWS_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("news", []):
                    title = item.get("title", "")
                    text = item.get("text", "") or ""
                    source_name = item.get("author", "") or item.get("source_country", "Iranian Source")
                    
                    # Mark as Iranian government source for transparency
                    source_label = f"🇮🇷 {source_name} (Iranian State Media)"
                    
                    api_sentiment = item.get("sentiment", 0.0)
                    
                    article = NewsArticle(
                        title=title,
                        description=text[:500] if text else "",
                        source=source_label,
                        url=item.get("url", ""),
                        published_at=item.get("publish_date", ""),
                        sentiment=api_sentiment,
                        relevance_score=self._calculate_relevance(f"{title} {text}"),
                        api_source="WorldNewsAPI-Iran"
                    )
                    articles.append(article)
                
                print(f"   ✓ Iranian Sources: {len(articles)} articles fetched")
            else:
                print(f"   ⚠️ Iranian Sources error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Iranian Sources exception: {e}")
        
        return articles
    
    def fetch_persian_gulf_news(self) -> List[NewsArticle]:
        """
        Fetch news from Persian Gulf region countries via World News API.
        
        Includes: Saudi Arabia, UAE, Qatar, Bahrain, Kuwait, Oman
        Provides regional perspective on Iran tensions.
        """
        if not WORLDNEWS_API_KEY:
            print("   ⚠️ World News API key not configured. Skipping Gulf sources.")
            return []
        
        self._rate_limit("worldnews")
        
        articles = []
        
        # Gulf countries
        gulf_countries = "sa,ae,qa,bh,kw,om"  # Country codes
        
        url = "https://api.worldnewsapi.com/search-news"
        params = {
            "text": "Iran OR Tehran OR IRGC OR nuclear OR Hormuz",
            "source-countries": gulf_countries,
            "language": "en",
            "number": 50,
            "api-key": WORLDNEWS_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("news", []):
                    title = item.get("title", "")
                    text = item.get("text", "") or ""
                    country = item.get("source_country", "Gulf")
                    
                    # Map country codes to names
                    country_names = {
                        "sa": "🇸🇦 Saudi Arabia",
                        "ae": "🇦🇪 UAE",
                        "qa": "🇶🇦 Qatar",
                        "bh": "🇧🇭 Bahrain",
                        "kw": "🇰🇼 Kuwait",
                        "om": "🇴🇲 Oman"
                    }
                    source_label = country_names.get(country.lower(), f"🌍 {country}") + " Media"
                    
                    api_sentiment = item.get("sentiment", 0.0)
                    
                    article = NewsArticle(
                        title=title,
                        description=text[:500] if text else "",
                        source=source_label,
                        url=item.get("url", ""),
                        published_at=item.get("publish_date", ""),
                        sentiment=api_sentiment,
                        relevance_score=self._calculate_relevance(f"{title} {text}"),
                        api_source="WorldNewsAPI-Gulf"
                    )
                    articles.append(article)
                
                print(f"   ✓ Gulf Region Sources: {len(articles)} articles fetched")
            else:
                print(f"   ⚠️ Gulf Sources error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Gulf Sources exception: {e}")
        
        return articles
    
    # =========================================================================
    # Alpha Vantage News Sentiment Integration (https://alphavantage.co)
    # =========================================================================
    
    def fetch_alphavantage_sentiment(self, tickers: str = "XLE,USO,GLD") -> List[NewsArticle]:
        """
        Fetch financial news with sentiment from Alpha Vantage.
        
        Free tier: 25 requests/day
        Register at: https://www.alphavantage.co/support/#api-key
        
        Useful for: Oil (USO), Gold (GLD), Energy (XLE) sentiment
        """
        if not ALPHAVANTAGE_API_KEY:
            print("   ⚠️ Alpha Vantage API key not configured. Skipping.")
            return []
        
        self._rate_limit("alphavantage")
        
        articles = []
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": tickers,
            "topics": "energy_transportation,finance",
            "apikey": ALPHAVANTAGE_API_KEY
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("feed", []):
                    title = item.get("title", "")
                    summary = item.get("summary", "") or ""
                    
                    # Alpha Vantage provides detailed sentiment
                    sentiment_score = float(item.get("overall_sentiment_score", 0))
                    
                    # Filter for Iran-related content
                    full_text = f"{title} {summary}".lower()
                    if any(kw in full_text for kw in ["iran", "oil", "gold", "middle east", "gulf"]):
                        article = NewsArticle(
                            title=title,
                            description=summary[:500] if summary else "",
                            source=item.get("source", "Unknown"),
                            url=item.get("url", ""),
                            published_at=item.get("time_published", ""),
                            sentiment=sentiment_score,
                            relevance_score=self._calculate_relevance(full_text),
                            api_source="AlphaVantage"
                        )
                        articles.append(article)
                
                print(f"   ✓ Alpha Vantage: {len(articles)} financial news articles")
            else:
                print(f"   ⚠️ Alpha Vantage error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Alpha Vantage exception: {e}")
        
        return articles
    
    # =========================================================================
    # Main Aggregation Methods
    # =========================================================================
    
    def fetch_all_sources(self, query: str = "Iran strike OR Iran attack OR Iran nuclear") -> NewsAnalysis:
        """
        Fetch news from all available sources and aggregate results.
        Uses parallel execution for 5-8x speedup.
        
        Returns comprehensive NewsAnalysis with articles from multiple sources.
        """
        print("\n📰 Fetching news from multiple sources (parallel)...")
        
        all_articles = []
        sources_used = []
        _lock = threading.Lock()
        
        def _fetch_task(name: str, fetch_fn, source_name: str, *args, **kwargs):
            """Helper to run a fetch and collect results thread-safely."""
            try:
                articles = fetch_fn(*args, **kwargs)
                with _lock:
                    if articles:
                        all_articles.extend(articles)
                        sources_used.append(source_name)
                        print(f"   ✓ {name}: {len(articles)} articles")
                    else:
                        print(f"   - {name}: 0 articles")
                return len(articles) if articles else 0
            except Exception as e:
                print(f"   ✗ {name} failed: {e}")
                return 0
        
        # Define all fetch tasks
        tasks = [
            ("GDELT Project", self.fetch_gdelt, "GDELT", "Iran"),
            ("Hacker News", self.fetch_hackernews, "HackerNews"),
            ("NewsAPI", self.fetch_newsapi, "NewsAPI", "Iran military OR Iran nuclear OR Iran attack"),
            ("GNews", self.fetch_gnews, "GNews", "Iran"),
            ("World News API", self.fetch_worldnews, "WorldNewsAPI", "Iran military attack strike"),
            ("Iranian State Media", self.fetch_iranian_sources, "IranianMedia"),
            ("Gulf Region Media", self.fetch_persian_gulf_news, "GulfMedia"),
            ("Alpha Vantage", self.fetch_alphavantage_sentiment, "AlphaVantage"),
        ]
        
        # Add optional RSS feeds
        if INCLUDE_ENGLISH_RSS_SOURCES:
            tasks.append(("English RSS", self.fetch_english_rss, "RSS-EN"))
        if INCLUDE_PERSIAN_LANGUAGE_SOURCES:
            tasks.append(("Persian RSS", self.fetch_persian_rss, "RSS-FA"))
        
        # Execute all tasks in parallel
        with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_WORKERS, len(tasks))) as executor:
            futures = []
            for task in tasks:
                name, fetch_fn, source_name = task[0], task[1], task[2]
                args = task[3:] if len(task) > 3 else ()
                futures.append(executor.submit(_fetch_task, name, fetch_fn, source_name, *args))
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"   ✗ Task error: {e}")
        
        # Analyze aggregated results
        analysis = self._analyze_articles(all_articles, sources_used)
        
        print(f"\n✅ Total: {len(all_articles)} articles from {len(sources_used)} sources")
        
        return analysis
    
    def _analyze_articles(self, articles: List[NewsArticle], sources_used: List[str]) -> NewsAnalysis:
        """Analyze aggregated articles and generate insights."""
        
        if not articles:
            return NewsAnalysis(
                fetch_timestamp=datetime.now().isoformat(),
                api_sources_used=sources_used
            )
        
        # Calculate sentiment distribution
        pro_strike = sum(1 for a in articles if a.sentiment > 0.2)
        anti_strike = sum(1 for a in articles if a.sentiment < -0.2)
        neutral = len(articles) - pro_strike - anti_strike
        
        # Average sentiment
        avg_sentiment = sum(a.sentiment for a in articles) / len(articles)
        
        # Count sources
        source_counter = Counter(a.source for a in articles)
        top_sources = source_counter.most_common(10)
        
        # Extract key themes
        all_titles = " ".join(a.title.lower() for a in articles)
        themes = []
        theme_keywords = [
            ("Nuclear Program", ["nuclear", "enrichment", "uranium"]),
            ("Military Action", ["strike", "attack", "military", "bombing"]),
            ("Diplomacy", ["talks", "negotiations", "diplomacy", "deal"]),
            ("Sanctions", ["sanctions", "pressure", "economic"]),
            ("Protests", ["protests", "uprising", "revolution"]),
            ("Israel Relations", ["israel", "netanyahu", "idf"]),
            ("Oil/Energy", ["oil", "energy", "opec", "crude"]),
            ("Regional Tensions", ["gulf", "hezbollah", "yemen", "houthi"])
        ]
        
        for theme_name, keywords in theme_keywords:
            if any(kw in all_titles for kw in keywords):
                themes.append(theme_name)
        
        # Timeline analysis (articles per day)
        timeline = {}
        for article in articles:
            if article.published_at:
                try:
                    date = article.published_at[:10]  # YYYY-MM-DD
                    timeline[date] = timeline.get(date, 0) + 1
                except:
                    pass
        
        # Sort articles by relevance
        sorted_articles = sorted(articles, key=lambda x: x.relevance_score, reverse=True)
        
        return NewsAnalysis(
            total_articles=len(articles),
            pro_strike_articles=pro_strike,
            anti_strike_articles=anti_strike,
            neutral_articles=neutral,
            average_sentiment=round(avg_sentiment, 3),
            key_themes=themes[:5],
            top_sources=top_sources,
            timeline=dict(sorted(timeline.items(), reverse=True)[:7]),
            articles=sorted_articles[:50],  # Keep top 50 most relevant
            api_sources_used=sources_used,
            fetch_timestamp=datetime.now().isoformat()
        )
    
    def get_strike_probability_from_news(self) -> Dict:
        """
        Calculate strike probability based on news sentiment analysis.
        
        Returns dict with probability estimates and supporting data.
        """
        analysis = self.fetch_all_sources()
        
        if analysis.total_articles == 0:
            return {
                "probability": 0.25,  # Default baseline
                "confidence": "low",
                "reasoning": "Insufficient news data",
                "articles_analyzed": 0
            }
        
        # Base probability adjusted by sentiment
        # Average sentiment ranges from -1 (very anti-strike) to 1 (very pro-strike)
        # Map to probability range: 0.15 to 0.55
        base_prob = 0.25
        sentiment_adjustment = analysis.average_sentiment * 0.15
        
        # Adjust by article volume (more articles = more attention = higher probability)
        volume_adjustment = min(0.05, analysis.total_articles / 1000)
        
        # Adjust by pro-strike ratio
        if analysis.total_articles > 0:
            pro_ratio = analysis.pro_strike_articles / analysis.total_articles
            ratio_adjustment = (pro_ratio - 0.5) * 0.1
        else:
            ratio_adjustment = 0
        
        final_prob = base_prob + sentiment_adjustment + volume_adjustment + ratio_adjustment
        final_prob = max(0.05, min(0.75, final_prob))  # Clamp to reasonable range
        
        # Determine confidence level
        if analysis.total_articles >= 100 and len(analysis.api_sources_used) >= 3:
            confidence = "high"
        elif analysis.total_articles >= 30 and len(analysis.api_sources_used) >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "probability": round(final_prob, 2),
            "confidence": confidence,
            "average_sentiment": analysis.average_sentiment,
            "pro_strike_pct": round(100 * analysis.pro_strike_articles / max(1, analysis.total_articles), 1),
            "anti_strike_pct": round(100 * analysis.anti_strike_articles / max(1, analysis.total_articles), 1),
            "articles_analyzed": analysis.total_articles,
            "sources_used": analysis.api_sources_used,
            "key_themes": analysis.key_themes,
            "top_sources": analysis.top_sources[:5],
            "top_articles": [
                {
                    "title": a.title,
                    "source": a.source,
                    "sentiment": a.sentiment,
                    "url": a.url,
                    "published_at": a.published_at,
                    "api_source": a.api_source,
                }
                for a in analysis.articles[:10]
            ]
        }
    
    def get_summary_for_report(self) -> Dict:
        """
        Get a summary suitable for including in the final report.
        
        Returns formatted data for report_generator.py integration.
        """
        prob_data = self.get_strike_probability_from_news()
        
        return {
            "news_analysis": {
                "total_articles": prob_data["articles_analyzed"],
                "sources": prob_data["sources_used"],
                "sentiment": {
                    "average": prob_data["average_sentiment"],
                    "pro_strike_pct": prob_data["pro_strike_pct"],
                    "anti_strike_pct": prob_data["anti_strike_pct"],
                    "neutral_pct": round(100 - prob_data["pro_strike_pct"] - prob_data["anti_strike_pct"], 1)
                },
                "key_themes": prob_data["key_themes"],
                "top_sources": prob_data["top_sources"],
                "top_headlines": prob_data["top_articles"]
            },
            "probability_estimate": {
                "value": prob_data["probability"],
                "confidence": prob_data["confidence"],
                "methodology": "Multi-source sentiment analysis"
            }
        }


# =========================================================================
# Standalone test
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("News Aggregator Test")
    print("=" * 60)
    
    aggregator = NewsAggregator()
    
    # Test fetching
    result = aggregator.get_strike_probability_from_news()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Strike Probability: {result['probability']*100:.1f}%")
    print(f"Confidence: {result['confidence']}")
    print(f"Articles Analyzed: {result['articles_analyzed']}")
    print(f"Sources Used: {', '.join(result['sources_used'])}")
    print(f"Average Sentiment: {result['average_sentiment']:.3f}")
    print(f"Pro-Strike: {result['pro_strike_pct']:.1f}%")
    print(f"Anti-Strike: {result['anti_strike_pct']:.1f}%")
    print(f"\nKey Themes: {', '.join(result['key_themes'])}")
    print(f"\nTop Headlines:")
    for i, article in enumerate(result['top_articles'][:5], 1):
        print(f"  {i}. [{article['sentiment']:+.2f}] {article['title'][:70]}...")
