#!/usr/bin/env python3
"""
US-Iran Conflict Prediction Analyzer
=====================================

Analyzes Reddit sentiment to predict likelihood of US military action against Iran.
Compares results with Polymarket prediction market odds.
Uses Claude Opus 4.6 for deep reasoning and date predictions.

Usage:
    python main.py                    # Full analysis (gather + analyze + report)
    python main.py --skip-gather      # Skip data gathering, use cached data
    python main.py --skip-analyze     # Skip analysis, use cached results
    python main.py --quick            # Quick mode (less data, faster)
    python main.py --no-llm           # Skip Claude AI analysis
    python main.py --skip-charts      # Skip chart generation
    python main.py --skip-social      # Skip social media outputs
    python main.py --cache-status     # Show cache status
    python main.py --clear-cache      # Clear all cached data
    python main.py --polymarket-only  # Only show Polymarket odds
"""

# =============================================================================
# PATH SETUP - Must be done BEFORE any local imports
# =============================================================================
import sys
import warnings
from pathlib import Path

# Add project root to path for src package imports
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Fix mpl_toolkits namespace package conflict (user site vs system)
# Note: We prioritize user site but DON'T remove system dist-packages entirely
# because some packages (like 'distro' needed by anthropic) are only there.
_user_site = '/home/erfan/.local/lib/python3.10/site-packages'
if _user_site in sys.path:
    sys.path.remove(_user_site)
sys.path.insert(0, _user_site)
warnings.filterwarnings('ignore', message='.*Unable to import Axes3D.*')

# =============================================================================
# STANDARD LIBRARY IMPORTS
# =============================================================================
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# =============================================================================
# CREDENTIALS (stays at project root)
# =============================================================================
from credentials import CLIENT_ID, CLIENT_SECRET, ANTHROPIC_API_KEY

# =============================================================================
# PROJECT IMPORTS - Using new package structure
# =============================================================================
# Core modules
from src.core.config import (
    SUBREDDIT_NAMES_LIST, CONTEXT_KEYWORDS, TOP_POSTS_TIME_FILTER,
    MAXIMUM_POSTS_PER_SUBREDDIT, MINIMUM_COMMENT_LENGTH, MAXIMUM_COMMENT_LENGTH,
    USE_GPU, CACHE_DIRECTORY, AUTO_CACHE, INCLUDE_RAW_COMMENTS, MAX_SAMPLE_COMMENTS,
    MAX_COMMENTS_PER_POST, MAX_COMMENTS_PER_SUBREDDIT, INCLUDE_RECENT_COMMENT_FEED,
    RECENT_COMMENTS_PER_SUBREDDIT, SUBMISSION_COMMENT_SORT, REPLACE_MORE_LIMIT,
    MAX_CONCURRENT_WORKERS, USE_CONCURRENT_REDDIT_GATHERING,
)
from src.core.cache_manager import CacheManager

# Data collection modules
from src.data.data_gatherer import DataGatherer
from src.data.polymarket_fetcher import PolymarketFetcher
try:
    from src.data.news_aggregator import NewsAggregator
    NEWS_AGGREGATOR_AVAILABLE = True
except ImportError:
    NEWS_AGGREGATOR_AVAILABLE = False

# Analysis modules
from src.analysis.scenario_analyzer import ScenarioAnalyzer
from src.analysis.llm_analyzer import LLMAnalyzer
from src.analysis.reasoning_framework import ReasoningFramework

# Reporting modules
from src.reporting.report_generator import ReportGenerator
from src.reporting.investment_advisor import InvestmentAdvisor
from src.reporting.polymarket_betting_strategy import PolymarketBettingStrategy

try:
    from src.reporting.social_media_generator import generate_social_media_content
    _SOCIAL_MEDIA_AVAILABLE = True
except ImportError:
    generate_social_media_content = None  # type: ignore[assignment]
    _SOCIAL_MEDIA_AVAILABLE = False

try:
    from src.analysis.user_opinion_summarizer import summarize_user_opinions
    _OPINION_SUMMARY_AVAILABLE = True
except Exception:
    summarize_user_opinions = None  # type: ignore[assignment]
    _OPINION_SUMMARY_AVAILABLE = False


def print_banner():
    """Print application banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           US-IRAN CONFLICT PREDICTION ANALYZER                    ║
║                                                                   ║
║   Analyzing Reddit sentiment on potential US military action     ║
║   against Iran and comparing with Polymarket prediction odds.    ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def show_cache_status(cache: CacheManager):
    """Display current cache status."""
    status = cache.get_cache_status()
    
    print("\n📦 Cache Status")
    print("=" * 50)
    print(f"Cache directory: {status['cache_dir']}")
    print()
    
    for cache_type in ['comments', 'classification', 'analysis', 'polymarket']:
        info = status[cache_type]
        exists = "✅" if info['exists'] else "❌"
        print(f"{cache_type.capitalize():15} {exists}", end="")
        if info['exists'] and info['info']:
            cached_at = info['info'].get('cached_at', 'unknown')
            print(f" (cached: {cached_at[:10]})", end="")
            if 'stats' in info['info']:
                stats = info['info']['stats']
                print(f" - {stats.get('comments', 'N/A')} comments, {stats.get('authors', 'N/A')} authors", end="")
        print()
    
    if status['reports']:
        print(f"\n📄 Saved Reports: {len(status['reports'])}")
        for report in status['reports'][:5]:
            print(f"   • {report}")


def gather_data(cache: CacheManager, quick_mode: bool = False) -> dict:
    """Gather data from Reddit."""
    print("\n" + "=" * 60)
    print("STEP 1: DATA GATHERING")
    print("=" * 60)
    
    # Adjust settings for quick mode
    subreddits = SUBREDDIT_NAMES_LIST[:5] if quick_mode else SUBREDDIT_NAMES_LIST
    max_posts = 50 if quick_mode else MAXIMUM_POSTS_PER_SUBREDDIT
    
    print(f"📋 Configuration:")
    print(f"   Subreddits: {len(subreddits)}")
    print(f"   Max posts per subreddit: {max_posts}")
    print(f"   Time filter: {TOP_POSTS_TIME_FILTER}")
    print(f"   Context keywords: {len(CONTEXT_KEYWORDS)}")
    
    gatherer = DataGatherer(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        subreddit_names_list=subreddits,
        maximum_posts_per_subreddit=max_posts,
        top_posts_time_filter=TOP_POSTS_TIME_FILTER,
        min_comment_length=MINIMUM_COMMENT_LENGTH,
        max_comment_length=MAXIMUM_COMMENT_LENGTH,
        context_keywords=CONTEXT_KEYWORDS,
        max_comments_per_post=MAX_COMMENTS_PER_POST,
        max_comments_per_subreddit=MAX_COMMENTS_PER_SUBREDDIT,
        include_recent_comment_feed=INCLUDE_RECENT_COMMENT_FEED,
        recent_comments_per_subreddit=RECENT_COMMENTS_PER_SUBREDDIT,
        submission_comment_sort=SUBMISSION_COMMENT_SORT,
        replace_more_limit=REPLACE_MORE_LIMIT,
        # Enable concurrent fetching for faster Reddit data collection
        use_concurrent=USE_CONCURRENT_REDDIT_GATHERING,
        max_workers=MAX_CONCURRENT_WORKERS,
    )
    
    results = gatherer.gather_data()

    # If Reddit API is unreachable (e.g., DNS/network failure), fall back to cached data
    # so the rest of the pipeline can still complete and produce the two reports.
    try:
        fatal = results.get("fatal_error") if isinstance(results, dict) else None
        total_comments = int((results.get("statistics") or {}).get("total_comments_collected", 0)) if isinstance(results, dict) else 0
        if (fatal and fatal.get("type") == "network_dns") or total_comments == 0:
            if cache.has_comments_cache():
                print("\n⚠️ Reddit gathering failed/unavailable. Falling back to cached Reddit data...")
                cached = cache.load_comments()
                if isinstance(cached, dict):
                    return cached
    except Exception:
        pass
    
    # Cache results
    if AUTO_CACHE:
        print("\n💾 Caching gathered data...")
        cache.save_comments(
            comments_by_author=results['comments_by_author'],
            all_comments=results.get("all_comments", []),
            all_posts=results.get("all_posts", []),
            statistics=results.get("statistics", {}),
            config=results.get("config", {}),
            subreddits=subreddits,
            time_filter=TOP_POSTS_TIME_FILTER,
            max_posts=max_posts
        )
        print("   ✅ Data cached successfully")
    
    return results


def analyze_data(cache: CacheManager, comments_data: dict, quick_mode: bool = False) -> tuple:
    """Analyze gathered data."""
    print("\n" + "=" * 60)
    print("STEP 2: SENTIMENT ANALYSIS")
    print("=" * 60)
    
    # Prepare comments for analysis
    all_comments = comments_data.get('all_comments', [])
    
    if not all_comments:
        # Try to reconstruct from comments_by_author
        comments_by_author = comments_data.get('comments_by_author', {})
        for author, author_comments in comments_by_author.items():
            if isinstance(author_comments, list):
                for comment in author_comments:
                    if isinstance(comment, dict):
                        all_comments.append(comment)
                    else:
                        # Legacy format: just strings
                        all_comments.append({
                            'body': comment,
                            'author': author,
                            'subreddit': 'unknown',
                            'comment_id': ''
                        })
    
    print(f"📊 Analyzing {len(all_comments)} comments...")
    
    # Initialize analyzer with fast_mode for speed (2x faster)
    use_zero_shot = not quick_mode  # Skip zero-shot in quick mode
    analyzer = ScenarioAnalyzer(use_zero_shot=use_zero_shot, use_gpu=USE_GPU, fast_mode=True)
    
    # Run analysis
    results = analyzer.analyze_comments(all_comments)
    reasoning = analyzer.generate_reasoning(results)
    
    # Cache results
    if AUTO_CACHE:
        print("\n💾 Caching analysis results...")
        cache.save_classification(results.to_dict())
        cache.save_analysis({
            'results': results.to_dict(),
            'reasoning': reasoning
        })
        print("   ✅ Analysis cached successfully")
    
    return results, reasoning


def fetch_polymarket(cache: CacheManager, skip_comments: bool = False) -> dict:
    """Fetch Polymarket odds and comments."""
    print("\n" + "=" * 60)
    print("STEP 3: POLYMARKET COMPARISON")
    print("=" * 60)
    
    fetcher = PolymarketFetcher()
    data = fetcher.get_current_odds()
    
    print(fetcher.format_odds_summary())
    print("\n")
    print(fetcher.format_timeline_summary())
    print("\n")
    
    # Fetch Polymarket comments (can take a while with many markets)
    market_comments = []
    
    if skip_comments:
        # Load from cache
        print("   ⏩ Skipping Polymarket comments fetch, loading from cache...")
        cached_comments = cache.load_polymarket_comments_merged()
        if cached_comments:
            market_comments = cached_comments
            print(f"   ✅ Loaded {len(market_comments):,} comments from cache")
        else:
            print("   ⚠️ No cached Polymarket comments found")
    else:
        try:
            print("   Fetching Polymarket comments...")
            market_comments = fetcher.get_market_comments()
            print(fetcher.format_comments_summary(market_comments))
            
            # Save to append-only cache (deduplicates automatically)
            if AUTO_CACHE and market_comments:
                merge_stats = cache.save_polymarket_comments_merged(
                    comments=market_comments,
                    market_info={"fetched_at": datetime.now().isoformat()}
                )
                print(f"   💾 Saved to cache: {merge_stats['new_added']} new, {merge_stats['duplicates']} duplicates, {merge_stats['total']} total")
        except Exception as e:
            print(f"   ⚠️ Comment fetch failed: {e}")
            # Try loading from cache as fallback
            cached_comments = cache.load_polymarket_comments_merged()
            if cached_comments:
                market_comments = cached_comments
                print(f"   ↩️ Fallback: loaded {len(market_comments):,} comments from cache")

    # Get comments summary for report (stance + top liked)
    comments_summary = fetcher.get_comments_summary(market_comments)
    data["comments_summary"] = comments_summary
    data["market_comments_count"] = len(market_comments)

    # Also persist a timestamped snapshot for historical tracking
    try:
        snap_path = cache.save_polymarket_comments_snapshot(market_comments) if AUTO_CACHE and market_comments else ""
        if snap_path:
            data["market_comments_snapshot_path"] = snap_path
    except Exception:
        pass

    # Non-LLM user-opinion summary (themes + representative quotes)
    if _OPINION_SUMMARY_AVAILABLE and summarize_user_opinions and market_comments:
        try:
            data["user_opinion_summary"] = data.get("user_opinion_summary", {})
            data["user_opinion_summary"]["polymarket"] = summarize_user_opinions(
                comments=market_comments,
                source_label="Polymarket",
                top_n_themes=8,
                max_quotes_per_theme=3,
                max_total_quotes=20,
            )
        except Exception:
            pass

    # Add Polymarket near-term term structure tables for reports/charts
    try:
        data["us_strike_term_structure"] = fetcher.get_us_strike_term_structure(include_past=False)
        data["us_strike_near_term"] = fetcher.get_us_strike_near_term_tables(max_days_daily=21)
    except Exception:
        # Never fail the pipeline due to extra convenience fields
        pass

    # High win-rate traders (estimated from closed positions) + positions on project markets
    try:
        print("   Fetching high win-rate trader data...")
        trader_insights = fetcher.get_high_win_rate_traders_on_project_markets(data)
        data["high_win_rate_traders"] = trader_insights
        # For existing chart/report hooks
        if isinstance(trader_insights, dict):
            if isinstance(trader_insights.get("traders_for_chart"), list) and trader_insights.get("traders_for_chart"):
                data["top_traders"] = trader_insights["traders_for_chart"]
            if isinstance(trader_insights.get("smart_money"), dict) and trader_insights.get("smart_money"):
                data["smart_money"] = trader_insights["smart_money"]
        print("   ✓ Trader analysis complete")
    except Exception as e:
        print(f"   ⚠️ High win-rate trader analysis failed: {e}")

    # Cross-market smart money analysis (Iran + Gold + Bitcoin + Russia/Ukraine + China + Stocks)
    try:
        print("\n   🌍 Cross-market smart money analysis...")
        cross_market = fetcher.get_smart_money_cross_market_analysis(polymarket_odds_data=data)
        data["cross_market_smart_money"] = cross_market
        n_traders = cross_market.get("total_traders_qualified", 0)
        n_positions = cross_market.get("total_positions_tracked", 0)
        print(f"   ✓ Cross-market analysis: {n_traders} traders, {n_positions} positions tracked")
        # Quick summary
        cats = cross_market.get("categories", {})
        for cat_name in ["iran", "gold", "bitcoin", "russia_ukraine", "us_stocks"]:
            cd = cats.get(cat_name, {})
            if cd.get("num_positions", 0) > 0:
                print(f"      {cat_name}: YES {cd.get('yes_pct',50):.0f}% / NO {cd.get('no_pct',50):.0f}%  "
                      f"({cd.get('num_positions',0)} positions)")
    except Exception as e:
        print(f"   ⚠️ Cross-market smart money analysis failed: {e}")
    
    # Cache results
    if AUTO_CACHE:
        cache.save_polymarket(data)
    
    return data, fetcher


def fetch_multi_source_news(cache: CacheManager, skip_fetch: bool = False) -> dict:
    """Fetch and analyze news from multiple sources."""
    print("\n" + "=" * 60)
    print("STEP 3.25: MULTI-SOURCE NEWS ANALYSIS")
    print("=" * 60)
    
    if not NEWS_AGGREGATOR_AVAILABLE:
        print("   ⚠️ News aggregator not available")
        return {}
    
    # Check if we should load from cache
    if skip_fetch:
        print("   ⏩ Skipping news fetch, loading from cache...")
        cached_news = cache.load_news()
        if cached_news and cached_news.get("articles"):
            articles = cached_news.get("articles", [])
            print(f"   ✅ Loaded {len(articles):,} articles from cache")
            
            # Reconstruct the summary from cached data
            return {
                "news_analysis": cached_news.get("analysis", {}),
                "probability_estimate": cached_news.get("probability_estimate", {}),
                "all_articles": articles,
                "from_cache": True
            }
        else:
            print("   ⚠️ No cached news found, fetching fresh data...")
    
    try:
        aggregator = NewsAggregator()
        
        print("\n📰 Fetching news from multiple APIs...")
        print("   (GDELT, Hacker News, NewsAPI, GNews, WorldNews, Alpha Vantage)")
        
        # Fetch all articles first (for caching)
        analysis = aggregator.fetch_all_sources()
        
        # Convert articles to dict format for caching
        all_articles = []
        if hasattr(analysis, 'articles') and analysis.articles:
            for art in analysis.articles:
                if hasattr(art, 'to_dict'):
                    all_articles.append(art.to_dict())
                elif isinstance(art, dict):
                    all_articles.append(art)
        
        # Save to append-only cache
        if AUTO_CACHE and all_articles:
            cache_key = cache.save_news(
                articles=all_articles,
                analysis={
                    "total_articles": analysis.total_articles,
                    "pro_strike_articles": analysis.pro_strike_articles,
                    "anti_strike_articles": analysis.anti_strike_articles,
                    "neutral_articles": analysis.neutral_articles,
                    "average_sentiment": analysis.average_sentiment,
                    "key_themes": analysis.key_themes,
                    "top_sources": analysis.top_sources,
                    "api_sources_used": analysis.api_sources_used,
                },
                source_info={"sources": analysis.api_sources_used}
            )
            # Get updated stats
            cached_news = cache.load_news()
            if cached_news:
                total_cached = cached_news.get("total_articles", len(all_articles))
                last_stats = cached_news.get("last_merge_stats", {})
                print(f"   💾 Saved to cache: {last_stats.get('new_added', 0)} new articles, {total_cached:,} total in database")
        
        # Get summary for report
        news_data = aggregator.get_summary_for_report()
        news_data["all_articles"] = all_articles
        
        # Print summary
        na = news_data.get("news_analysis", {})
        prob = news_data.get("probability_estimate", {})
        
        print(f"\n📊 **News Analysis Summary:**")
        print(f"   Total Articles: {na.get('total_articles', 0):,}")
        print(f"   Sources Used: {', '.join(na.get('sources', []))}")
        
        sentiment = na.get("sentiment", {})
        print(f"\n   Sentiment Breakdown:")
        print(f"      Pro-Strike:  {sentiment.get('pro_strike_pct', 0):.1f}%")
        print(f"      Anti-Strike: {sentiment.get('anti_strike_pct', 0):.1f}%")
        print(f"      Neutral:     {sentiment.get('neutral_pct', 0):.1f}%")
        
        print(f"\n   Key Themes: {', '.join(na.get('key_themes', []))}")
        print(f"\n   News-Based Strike Probability: {prob.get('value', 0.25)*100:.0f}%")
        print(f"   Confidence: {prob.get('confidence', 'low')}")
        
        # Show top headlines
        headlines = na.get("top_headlines", [])
        if headlines:
            print(f"\n   📰 Top Headlines:")
            for i, h in enumerate(headlines[:3], 1):
                sentiment_str = "🔴" if h.get("sentiment", 0) > 0.2 else "🟢" if h.get("sentiment", 0) < -0.2 else "🟡"
                print(f"      {i}. {sentiment_str} {h.get('title', 'N/A')[:60]}...")
        
        return news_data
        
    except Exception as e:
        print(f"   ⚠️ News aggregation failed: {e}")
        # Try loading from cache as fallback
        cached_news = cache.load_news()
        if cached_news and cached_news.get("articles"):
            print(f"   ↩️ Fallback: loaded {len(cached_news['articles']):,} articles from cache")
            return {
                "news_analysis": cached_news.get("analysis", {}),
                "all_articles": cached_news.get("articles", []),
                "from_cache": True
            }
        return {}


def analyze_financial_markets() -> dict:
    """Analyze gold and crypto markets for conflict correlation."""
    print("\n" + "=" * 60)
    print("STEP 3.5: FINANCIAL MARKET ANALYSIS")
    print("=" * 60)
    
    try:
        from src.data.market_analyzer import MarketAnalyzer
        
        analyzer = MarketAnalyzer()
        analysis = analyzer.analyze_markets()
        
        print(f"\n💰 **Gold Market (Primary Conflict Indicator)**")
        print(f"   Current Price: ${analysis.gold.current_price:,.2f}/oz")
        gold_change = analysis.gold.price_change_percent
        if isinstance(gold_change, (int, float)):
            print(f"   24h Change: +{gold_change:.2f}%")
        else:
            print(f"   24h Change: +{gold_change}%")
        
        yoy_change = analysis.gold.year_change_percent
        if isinstance(yoy_change, (int, float)):
            print(f"   YoY Change: {yoy_change:+.1f}%")
        else:
            print(f"   YoY Change: {yoy_change}%")
        
        print(f"   Risk Level: {analysis.risk_indicator.upper()}")
        
        print(f"\n₿ **Bitcoin Market (Secondary Indicator)**")
        btc_price = analysis.bitcoin.current_price
        if isinstance(btc_price, (int, float)):
            print(f"   Current Price: ${btc_price:,.0f}")
        else:
            print(f"   Current Price: ${btc_price}")
        
        btc_change = analysis.bitcoin.price_change_percent
        if isinstance(btc_change, (int, float)):
            print(f"   24h Change: {btc_change:+.1f}%")
        else:
            print(f"   24h Change: {btc_change}%")
        print(f"   Behavior: Risk asset (not safe haven)")
        
        print(f"\n📊 **Gold-Based Attack Probability:**")
        probs = analyzer.get_attack_probability_from_gold()
        for timeline, prob in probs.items():
            if isinstance(prob, (int, float)):
                timeline_str = timeline.replace('_', ' ').title()
                print(f"   {timeline_str}: {prob:.1f}%")
        
        print(f"\n🔗 **Correlation Score:** {analysis.correlation_score}/100")
        print(f"\n📈 **Market Signal:**")
        print(f"   {analysis.prediction_signal}")
        
        return {
            'gold': {
                'price': analysis.gold.current_price,
                'change_24h': analysis.gold.price_change_percent,
                'change_yoy': analysis.gold.year_change_percent,
                'risk_level': analysis.risk_indicator
            },
            'bitcoin': {
                'price': analysis.bitcoin.current_price,
                'change_24h': analysis.bitcoin.price_change_percent
            },
            'correlation_score': analysis.correlation_score,
            'prediction_signal': analysis.prediction_signal,
            'gold_based_probabilities': probs,
            'full_analysis': analyzer.format_market_summary()
        }
    except ImportError:
        print("   ⚠️ Market analyzer not available")
        return {}
    except Exception as e:
        print(f"   ⚠️ Market analysis failed: {e}")
        return {}


def run_llm_analysis(
    cache: CacheManager,
    results: dict,
    polymarket_data: dict,
    gathering_stats: dict,
    reasoning: dict | None = None,
) -> dict:
    """Run deep analysis with Claude Opus 4.6."""
    print("\n" + "=" * 60)
    print("STEP 4: AI DEEP ANALYSIS (Claude Opus 4.6)")
    print("=" * 60)
    
    llm = LLMAnalyzer(api_key=ANTHROPIC_API_KEY)
    
    # Convert results to dict if needed
    results_dict = results.to_dict() if hasattr(results, 'to_dict') else results
    
    # Run comprehensive analysis
    llm_result = llm.analyze(
        analysis_results=results_dict,
        polymarket_data=polymarket_data,
        gathering_stats=gathering_stats
    )
    
    if llm_result:
        # Cache LLM results
        if AUTO_CACHE:
            cache.save_analysis({
                'results': results_dict,
                'reasoning': reasoning or {},
                'llm_analysis': llm_result.to_dict()
            })
        
        # Print key findings
        print("\n🎯 KEY FINDINGS FROM AI ANALYSIS:")
        for i, finding in enumerate(llm_result.key_findings[:5], 1):
            print(f"   {i}. {finding}")
        
        print(f"\n📅 LIKELY ATTACK DATES:")
        for date_pred in llm_result.likely_dates[:4]:
            print(f"   • {date_pred.get('date_range', 'N/A')}: {date_pred.get('probability', 'N/A')}")
            print(f"     {date_pred.get('reasoning', '')[:80]}...")
        
        print(f"\n💡 FINAL VERDICT:")
        print(f"   {llm_result.final_verdict}")
        
        return llm_result
    
    return None


def generate_report(
    cache: CacheManager,
    results,
    reasoning: dict,
    polymarket_data: dict,
    gathering_stats: dict = None,
    llm_analysis = None,
    news_analysis: dict = None,
    skip_charts: bool = False,
    skip_social: bool = False
) -> str:
    """Generate and save analysis report."""
    print("\n" + "=" * 60)
    print("STEP 5: REPORT GENERATION")
    print("=" * 60)
    
    generator = ReportGenerator()
    
    # Convert results to dict if needed
    results_dict = results.to_dict() if hasattr(results, 'to_dict') else results
    
    # Get polymarket comments summary
    polymarket_comments = polymarket_data.get('comments_summary', None)
    
    # Convert llm_analysis to dict if needed
    llm_analysis_dict = None
    if llm_analysis:
        llm_analysis_dict = llm_analysis.to_dict() if hasattr(llm_analysis, 'to_dict') else llm_analysis
    
    # Keep output directory clean: only keep the final reports and social media files.
    try:
        reports_dir = Path(CACHE_DIRECTORY) / "reports"
        if reports_dir.exists():
            # Files to keep
            keep_files = {
                "report_EN.md", "report_FA.md",
                "twitter_thread_FA.md", "twitter_thread_EN.md",
                "linkedin_post_FA.md", "linkedin_post_EN.md"
            }
            for p in reports_dir.glob("*.md"):
                if p.name in keep_files:
                    continue
                if p.name.startswith(("report_", "investment_advice_", "betting_strategy_", "reasoning_analysis_")):
                    p.unlink()
    except Exception:
        pass

    # Generate separate English and Persian reports with charts (ONLY outputs)
    print("\n📊 Generating English and Persian reports with charts...")
    try:
        bilingual_reports = generator.generate_both_reports(
            analysis_results=results_dict,
            reasoning=reasoning,
            polymarket_data=polymarket_data,
            polymarket_comments=polymarket_comments,
            llm_analysis=llm_analysis_dict,
            gathering_stats=gathering_stats,
            include_sample_comments=INCLUDE_RAW_COMMENTS,
            news_analysis=news_analysis,
            skip_charts=skip_charts
        )
        
        # Save English report (fixed filename, overwrite)
        en_filename = "report_EN.md"
        en_filepath = f"{CACHE_DIRECTORY}/reports/{en_filename}"
        with open(en_filepath, 'w', encoding='utf-8') as f:
            f.write(bilingual_reports['english'])
        print(f"  🇺🇸 English report: cache/reports/{en_filename} (overwritten)")
        
        # Save Persian report (fixed filename, overwrite)
        fa_filename = "report_FA.md"
        fa_filepath = f"{CACHE_DIRECTORY}/reports/{fa_filename}"
        with open(fa_filepath, 'w', encoding='utf-8') as f:
            f.write(bilingual_reports['persian'])
        print(f"  🇮🇷 Persian report: cache/reports/{fa_filename} (overwritten)")
        
        # Report charts generated
        charts = bilingual_reports.get('charts', {})
        if charts:
            print(f"  📊 Generated {len(charts)} charts in cache/charts/")
        
    except Exception as e:
        print(f"  ⚠️ Bilingual report generation failed: {e}")
        return ""
    
    # Generate social media content (Twitter threads + LinkedIn posts)
    if _SOCIAL_MEDIA_AVAILABLE and generate_social_media_content and not skip_social:
        print("\n📱 Generating social media content...")
        try:
            social_media_data = {
                'analysis_results': results_dict,
                'polymarket_data': polymarket_data,
                'reasoning': reasoning,
                'llm_analysis': llm_analysis_dict,
            }
            
            social_files = generate_social_media_content(
                analysis_results=results_dict,
                polymarket_data=polymarket_data,
                reasoning=reasoning,
                llm_analysis=llm_analysis_dict,
                output_dir=f"{CACHE_DIRECTORY}/reports"
            )
            
            print(f"  🐦 Twitter thread (FA): cache/reports/twitter_thread_FA.md")
            print(f"  🐦 Twitter thread (EN): cache/reports/twitter_thread_EN.md")
            print(f"  💼 LinkedIn post (FA): cache/reports/linkedin_post_FA.md")
            print(f"  💼 LinkedIn post (EN): cache/reports/linkedin_post_EN.md")
        except Exception as e:
            print(f"  ⚠️ Social media generation failed: {e}")
    
    # Return English report text for any caller usage
    return bilingual_reports.get("english", "")


def print_results_summary(results, reasoning: dict, polymarket_data: dict, fetcher: PolymarketFetcher, llm_analysis=None):
    """Print a summary of results to console."""
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    total_authors = results.total_authors_analyzed if hasattr(results, 'total_authors_analyzed') else results.get('total_authors_analyzed', 0)
    predict_attack = results.predict_attack if hasattr(results, 'predict_attack') else results.get('predict_attack', 0)
    predict_no_attack = results.predict_no_attack if hasattr(results, 'predict_no_attack') else results.get('predict_no_attack', 0)
    neutral = results.neutral if hasattr(results, 'neutral') else results.get('neutral', 0)
    
    total_opinionated = predict_attack + predict_no_attack
    
    print(f"\n📅 Current Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"👥 Users Analyzed: {total_authors}")
    
    if total_opinionated > 0:
        attack_pct = 100 * predict_attack / total_opinionated
        no_attack_pct = 100 * predict_no_attack / total_opinionated
        
        print(f"\n🗳️  PREDICTIONS:")
        print(f"   🔴 Attack will happen:   {predict_attack:4} users ({attack_pct:.1f}%)")
        print(f"   🟢 No attack:            {predict_no_attack:4} users ({no_attack_pct:.1f}%)")
        print(f"   ⚪ Neutral/Unclear:      {neutral:4} users")
        
        # Visual bar
        bar_length = 40
        attack_bar = int(attack_pct * bar_length / 100)
        print(f"\n   [{'█' * attack_bar}{'░' * (bar_length - attack_bar)}]")
        print(f"    Attack {attack_pct:.1f}%{' ' * 20}No Attack {no_attack_pct:.1f}%")
        
        # Polymarket comparison
        if fetcher is not None:
            print(f"\n📈 POLYMARKET COMPARISON:")
            comparison = fetcher.compare_with_reddit(attack_pct)
            print(f"   Reddit Attack Prediction: {attack_pct:.1f}%")
            print(f"   Polymarket Average:       {comparison['polymarket_average']:.1f}%")
            print(f"   Difference:               {comparison['difference_total']:+.1f}%")
            print(f"\n   {comparison['interpretation']}")
        else:
            print(f"\n📈 POLYMARKET COMPARISON: ⚠️ Polymarket data unavailable")
        
        # LLM Analysis Summary
        if llm_analysis:
            print(f"\n🧠 AI ANALYSIS (Claude):")
            print(f"   {llm_analysis.executive_summary}")
            
            print(f"\n📅 PREDICTED ATTACK TIMELINE:")
            for date_pred in llm_analysis.likely_dates[:5]:
                print(f"   • {date_pred.get('date_range')}: {date_pred.get('probability')}")
            
            # Extended predictions
            if llm_analysis.extended_predictions:
                print(f"\n🔮 EXTENDED PREDICTIONS:")
                ext = llm_analysis.extended_predictions
                # Safety: do not print or forecast individual-harm / assassination outcomes
                if ext.get("safety_note"):
                    print(f"   • Safety note: {ext.get('safety_note')}")
                print(f"   • Regime Change (time horizon): {ext.get('regime_change_probability_2026', ext.get('regime_change_probability', 'N/A'))}")
                print(f"   • War Duration (if occurs): {ext.get('war_duration_if_occurs', 'N/A')}")
                print(f"   • Negotiation Success: {ext.get('negotiation_success_probability', 'N/A')}")
                print(f"   • Future Government (most likely): {ext.get('future_government_most_likely', 'N/A')}")
                print(f"   • Iran Most Resembles: {ext.get('iran_most_resembles', 'N/A')}")
            
            # Timeline breakdown
            if llm_analysis.timeline_breakdown:
                print(f"\n⏰ TIMELINE BREAKDOWN:")
                for timeframe, prob in llm_analysis.timeline_breakdown.items():
                    timeframe_display = timeframe.replace("_", " ").title()
                    print(f"   • {timeframe_display}: {prob}")
        
        # Final verdict
        print("\n" + "-" * 60)
        if llm_analysis and llm_analysis.final_verdict:
            print(f"🎯 AI VERDICT: {llm_analysis.final_verdict}")
        elif attack_pct > 55:
            print("🎯 VERDICT: Reddit sentiment suggests ATTACK IS LIKELY")
        elif no_attack_pct > 55:
            print("🎯 VERDICT: Reddit sentiment suggests ATTACK IS UNLIKELY")
        else:
            print("🎯 VERDICT: Reddit sentiment is DIVIDED - no clear consensus")
    else:
        print("⚠️  No users expressed clear predictions")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="US-Iran Conflict Prediction Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Full analysis with AI reasoning
  python main.py --skip-gather      # Use cached Reddit data
  python main.py --skip-analyze     # Use cached analysis results  
  python main.py --quick            # Quick mode (less data, no AI)
  python main.py --no-llm           # Skip Claude AI analysis
  python main.py --cache-status     # Show what's cached
  python main.py --clear-cache      # Clear all cached data
  python main.py --polymarket-only  # Just show Polymarket odds
        """
    )
    
    parser.add_argument('--skip-gather', action='store_true',
                       help='Skip data gathering, use cached comments')
    parser.add_argument('--skip-analyze', action='store_true', 
                       help='Skip analysis, use cached results')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Quick mode: fewer subreddits, no zero-shot, no AI')
    parser.add_argument('--no-llm', action='store_true',
                       help='Skip Claude AI deep analysis')
    parser.add_argument('--cache-status', action='store_true',
                       help='Show cache status and exit')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear all cached data')
    parser.add_argument('--polymarket-only', action='store_true',
                       help='Only fetch and display Polymarket odds')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip report generation')
    parser.add_argument('--export', action='store_true',
                       help='Export all data to JSON')
    parser.add_argument('--skip-news', action='store_true',
                       help='Skip news fetching, use cached news data')
    parser.add_argument('--skip-polymarket-comments', action='store_true',
                       help='Skip Polymarket comments fetching, use cached comments')
    parser.add_argument('--skip-markets', action='store_true',
                       help='Skip financial market analysis')
    parser.add_argument('--skip-external', action='store_true',
                       help='Skip all external data fetching (news, Polymarket comments, markets)')
    parser.add_argument('--skip-charts', action='store_true',
                       help='Skip chart generation (reports will be text-only)')
    parser.add_argument('--skip-social', action='store_true',
                       help='Skip social media outputs (Twitter/LinkedIn)')
    
    args = parser.parse_args()
    
    # Initialize cache manager
    cache = CacheManager(CACHE_DIRECTORY)
    
    # Handle special commands
    if args.cache_status:
        print_banner()
        show_cache_status(cache)
        return
    
    if args.clear_cache:
        print("🗑️  Clearing all cached data...")
        cache.clear_cache()
        print("   ✅ Cache cleared")
        return
    
    if args.polymarket_only:
        print_banner()
        fetcher = PolymarketFetcher()
        print(fetcher.format_odds_summary())
        return
    
    # Start main analysis
    print_banner()
    start_time = datetime.now()
    
    # Step 1: Data Gathering
    if args.skip_gather:
        print("\n⏩ Skipping data gathering, loading from cache...")
        cached_comments = cache.load_comments()
        if cached_comments:
            comments_data = cached_comments
            gathering_stats = cached_comments.get('statistics', {})
            print(f"   ✅ Loaded {cached_comments.get('total_comments', 'N/A')} comments from cache")
        else:
            print("   ❌ No cached data found! Running full gather...")
            comments_data = gather_data(cache, args.quick)
            gathering_stats = comments_data.get('statistics', {})
    else:
        comments_data = gather_data(cache, args.quick)
        gathering_stats = comments_data.get('statistics', {})
    
    # Step 2: Analysis
    if args.skip_analyze:
        print("\n⏩ Skipping analysis, loading from cache...")
        cached_analysis = cache.load_analysis()
        if cached_analysis:
            results = cached_analysis.get('results', {})
            reasoning = cached_analysis.get('reasoning', {})
            print(f"   ✅ Loaded analysis from cache")
        else:
            print("   ❌ No cached analysis found! Running full analysis...")
            results, reasoning = analyze_data(cache, comments_data, args.quick)
    else:
        results, reasoning = analyze_data(cache, comments_data, args.quick)
    
    # Steps 3, 3.25, 3.5: Parallel fetching (Polymarket, News, Markets)
    # These are independent operations - run them in parallel for 2-3x speedup
    print("\n🚀 Fetching external data sources in parallel...")
    
    # Determine skip flags
    skip_news = args.skip_news or args.skip_external
    skip_polymarket_comments = args.skip_polymarket_comments or args.skip_external
    skip_markets = args.skip_markets or args.skip_external
    
    if skip_news or skip_polymarket_comments or skip_markets:
        skipped = []
        if skip_news:
            skipped.append("news")
        if skip_polymarket_comments:
            skipped.append("Polymarket comments")
        if skip_markets:
            skipped.append("markets")
        print(f"   ⏩ Skipping: {', '.join(skipped)} (using cached data)")
    
    polymarket_data = None
    fetcher = None
    news_analysis = {}
    market_data = {}
    
    def _fetch_polymarket_wrapper():
        return fetch_polymarket(cache, skip_comments=skip_polymarket_comments)
    
    def _fetch_news_wrapper():
        return fetch_multi_source_news(cache, skip_fetch=skip_news)
    
    def _fetch_markets_wrapper():
        if skip_markets:
            print("\n   ⏩ Skipping market analysis (using cached data not available)")
            return {}
        return analyze_financial_markets()
    
    with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_WORKERS, 4)) as executor:
        future_polymarket = executor.submit(_fetch_polymarket_wrapper)
        future_news = executor.submit(_fetch_news_wrapper)
        future_markets = executor.submit(_fetch_markets_wrapper)
        
        # Collect results
        try:
            polymarket_data, fetcher = future_polymarket.result()
        except Exception as e:
            print(f"   ⚠️ Polymarket fetch error: {e}")
            polymarket_data = {}
            fetcher = None
        
        try:
            news_analysis = future_news.result()
        except Exception as e:
            print(f"   ⚠️ News fetch error: {e}")
            news_analysis = {}
        
        try:
            market_data = future_markets.result()
        except Exception as e:
            print(f"   ⚠️ Market analysis error: {e}")
            market_data = {}
    
    # Inject market analysis into polymarket_data; use a fresh dict if
    # Polymarket fetch failed so gold/BTC data isn't silently dropped.
    if not polymarket_data:
        polymarket_data = {}
    polymarket_data['market_analysis'] = market_data
    
    # Step 4: AI Deep Analysis (Claude Opus 4.6)
    llm_analysis = None
    if not args.no_llm and not args.quick:
        llm_analysis = run_llm_analysis(cache, results, polymarket_data, gathering_stats, reasoning=reasoning)
    elif args.quick:
        print("\n⏩ Skipping AI analysis (quick mode)")
    else:
        print("\n⏩ Skipping AI analysis (--no-llm flag)")
    
    # Step 5: Report
    if not args.no_report:
        report = generate_report(
            cache,
            results,
            reasoning,
            polymarket_data,
            gathering_stats,
            llm_analysis,
            news_analysis,
            skip_charts=args.skip_charts,
            skip_social=args.skip_social
        )
    
    # Note: Investment/betting/reasoning sections are embedded in the two final reports.
    
    # Step 6: Export (if requested)
    if args.export:
        print("\n📤 Exporting all data to JSON...")
        export_path = cache.export_to_json()
        print(f"   ✅ Exported to {export_path}")
    
    # Print summary
    print_results_summary(results, reasoning, polymarket_data, fetcher, llm_analysis)
    
    # Timing
    duration = (datetime.now() - start_time).total_seconds()
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print(f"📄 Reports saved in cache/reports/:")
    print(f"   • report_EN.md, report_FA.md (full reports)")
    print(f"   • twitter_thread_FA.md, twitter_thread_EN.md (Twitter threads)")
    print(f"   • linkedin_post_FA.md, linkedin_post_EN.md (LinkedIn posts)")


if __name__ == "__main__":
    main()
