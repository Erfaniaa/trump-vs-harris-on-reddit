"""
Cache Manager - Handles offline storage of data and analysis results.
Supports pickle for fast Python object caching and JSON for human-readable exports.
"""

import os
import pickle
import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date and datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class CacheManager:
    """Manages caching of Reddit data and analysis results."""
    
    CACHE_DIR = "cache"
    
    # Cache file names
    COMMENTS_CACHE = "comments_data.pkl"
    CLASSIFICATION_CACHE = "classification_results.pkl"
    ANALYSIS_CACHE = "analysis_results.pkl"
    POLYMARKET_CACHE = "polymarket_odds.json"
    POLYMARKET_COMMENTS_DIR = "polymarket_comments"
    NEWS_CACHE = "news_data.pkl"
    REPORT_CACHE = "reports"
    METADATA_FILE = "cache_metadata.json"
    DUPLICATE_LOG = "duplicate_detection.log"
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize cache manager with optional custom cache directory."""
        self.cache_dir = Path(cache_dir or self.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / self.REPORT_CACHE).mkdir(exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self):
        """Load or initialize cache metadata."""
        metadata_path = self.cache_dir / self.METADATA_FILE
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "last_updated": None,
                "cache_versions": {}
            }
            self._save_metadata()
    
    def _save_metadata(self):
        """Save cache metadata."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        with open(self.cache_dir / self.METADATA_FILE, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_cache_path(self, filename: str) -> Path:
        """Get full path for a cache file."""
        return self.cache_dir / filename
    
    def _compute_hash(self, data: Any) -> str:
        """Compute hash of data for change detection."""
        return hashlib.md5(str(data).encode()).hexdigest()[:12]
    
    # ==================== Comments Data ====================
    
    @staticmethod
    def _normalize_id(value: Any) -> str:
        """Normalize IDs to stable strings."""
        try:
            s = str(value or "").strip()
        except Exception:
            return ""
        return s

    @staticmethod
    def _merge_unique_by_id(existing: list, incoming: list, id_key: str) -> list:
        """
        Merge two lists of dicts by a unique id key.
        - Keeps a single record per id (no duplicates)
        - If the same id appears in incoming, it updates/replaces the stored record
        - Preserves insertion order: existing order first, new ids appended
        """
        out = []
        index: dict[str, int] = {}

        def add_or_update(item: Any) -> None:
            if not isinstance(item, dict):
                return
            _id = CacheManager._normalize_id(item.get(id_key))
            if not _id:
                return
            if _id in index:
                out[index[_id]] = item
            else:
                index[_id] = len(out)
                out.append(item)

        for it in existing or []:
            add_or_update(it)
        for it in incoming or []:
            add_or_update(it)
        return out

    def save_comments(
        self,
        comments_by_author: dict,
        subreddits: list,
        time_filter: str,
        max_posts: int,
        all_comments: Optional[list] = None,
        all_posts: Optional[list] = None,
        statistics: Optional[dict] = None,
        config: Optional[dict] = None,
    ) -> str:
        """
        Save collected Reddit comments to cache.
        
        This is append-only at the data level: previously cached posts/comments are never removed.
        New runs only add new items (deduped by comment_id/post_id) and update existing items if edited.
        
        Returns cache key for reference.
        """
        cache_key = f"comments_{time_filter}_{max_posts}_{self._compute_hash(subreddits)}"

        # If caller didn't provide flat lists, reconstruct them from per-author lists.
        # This also migrates legacy caches that only stored comments_by_author.
        if not all_comments:
            reconstructed = []
            for author, items in (comments_by_author or {}).items():
                if not isinstance(items, list):
                    continue
                for it in items:
                    if isinstance(it, dict):
                        reconstructed.append(it)
            all_comments = reconstructed

        if not all_posts:
            # Best-effort minimal post reconstruction from comment metadata.
            # If the full post objects are provided by DataGatherer, those are preferred.
            post_index: dict[str, dict] = {}
            for c in all_comments or []:
                if not isinstance(c, dict):
                    continue
                pid = self._normalize_id(c.get("post_id"))
                if not pid:
                    continue
                post_index[pid] = {
                    "post_id": pid,
                    "title": c.get("post_title") or "",
                    "subreddit": c.get("subreddit") or "",
                    # Minimal fields; full PostData is only available when DataGatherer provides all_posts.
                    "created_utc": c.get("created_utc") or 0,
                    "created_date": c.get("created_date") or "",
                    "url": "",
                    "score": 0,
                    "upvote_ratio": 0,
                    "num_comments": 0,
                    "days_ago": c.get("days_ago") or 0,
                }
            all_posts = list(post_index.values())

        existing = self.load_comments() if self.has_comments_cache() else None
        existing_comments_by_author = (existing or {}).get("comments_by_author", {}) if isinstance(existing, dict) else {}
        existing_all_comments = (existing or {}).get("all_comments", []) if isinstance(existing, dict) else []
        existing_all_posts = (existing or {}).get("all_posts", []) if isinstance(existing, dict) else []

        # Merge the flat lists first (global dedupe keys)
        merged_all_posts = self._merge_unique_by_id(existing_all_posts, all_posts or [], id_key="post_id")
        merged_all_comments = self._merge_unique_by_id(existing_all_comments, all_comments or [], id_key="comment_id")

        # Build a quick lookup for comment_id -> comment dict
        comment_index: dict[str, dict] = {}
        for c in merged_all_comments:
            if isinstance(c, dict):
                cid = self._normalize_id(c.get("comment_id"))
                if cid:
                    comment_index[cid] = c

        # Merge per-author lists, deduping by comment_id and updating records from global index
        merged_by_author: dict = {}
        all_authors = set(existing_comments_by_author.keys()) | set((comments_by_author or {}).keys())
        for author in all_authors:
            existing_list = existing_comments_by_author.get(author, []) if isinstance(existing_comments_by_author, dict) else []
            incoming_list = (comments_by_author or {}).get(author, [])

            # Normalize legacy string lists into dict-like structure when possible
            normalized_existing = []
            for it in existing_list or []:
                if isinstance(it, dict):
                    normalized_existing.append(it)
            normalized_incoming = []
            for it in incoming_list or []:
                if isinstance(it, dict):
                    normalized_incoming.append(it)

            merged = self._merge_unique_by_id(normalized_existing, normalized_incoming, id_key="comment_id")

            # Ensure the per-author comment dict matches the latest global version (e.g., edits)
            fixed = []
            seen = set()
            for it in merged:
                if not isinstance(it, dict):
                    continue
                cid = self._normalize_id(it.get("comment_id"))
                if not cid or cid in seen:
                    continue
                seen.add(cid)
                fixed.append(comment_index.get(cid, it))
            merged_by_author[author] = fixed

        # Merge subreddit list/config history
        merged_subreddits = sorted(set((existing or {}).get("subreddits", []) if isinstance(existing, dict) else []) | set(subreddits or []))

        first_cached_at = (existing or {}).get("first_cached_at") if isinstance(existing, dict) else None
        if not first_cached_at:
            first_cached_at = (existing or {}).get("cached_at") if isinstance(existing, dict) else None
        if not first_cached_at:
            first_cached_at = datetime.now().isoformat()

        cache_data = {
            "comments_by_author": merged_by_author,
            "all_comments": merged_all_comments,
            "all_posts": merged_all_posts,
            "subreddits": merged_subreddits,
            "time_filter": time_filter,
            "max_posts_per_subreddit": max_posts,
            "statistics": statistics or (existing or {}).get("statistics", {}) if isinstance(existing, dict) else {},
            "config": config or (existing or {}).get("config", {}) if isinstance(existing, dict) else {},
            "total_authors": len(merged_by_author),
            "total_comments": len(merged_all_comments),
            "total_posts": len(merged_all_posts),
            "first_cached_at": first_cached_at,
            "cached_at": datetime.now().isoformat(),
            "note": "Append-only merge cache. Items deduped by comment_id/post_id; existing items may be updated if edited.",
        }
        
        with open(self._get_cache_path(self.COMMENTS_CACHE), 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        self.metadata["cache_versions"]["comments"] = {
            "key": cache_key,
            "cached_at": cache_data["cached_at"],
            "stats": {
                "authors": cache_data["total_authors"],
                "comments": cache_data["total_comments"],
                "posts": cache_data.get("total_posts", 0),
                "subreddits": len(merged_subreddits)
            }
        }
        self._save_metadata()
        
        return cache_key
    
    def load_comments(self) -> Optional[dict]:
        """Load cached comments data. Returns None if not found."""
        cache_path = self._get_cache_path(self.COMMENTS_CACHE)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    
    def has_comments_cache(self) -> bool:
        """Check if comments cache exists."""
        return self._get_cache_path(self.COMMENTS_CACHE).exists()
    
    # ==================== Classification Results ====================
    
    def save_classification(self, results: dict) -> None:
        """Save classification results to cache."""
        cache_data = {
            "results": results,
            "cached_at": datetime.now().isoformat()
        }
        
        with open(self._get_cache_path(self.CLASSIFICATION_CACHE), 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        self.metadata["cache_versions"]["classification"] = {
            "cached_at": cache_data["cached_at"],
            "total_analyzed": results.get("total_users_analyzed", 0)
        }
        self._save_metadata()
    
    def load_classification(self) -> Optional[dict]:
        """Load cached classification results."""
        cache_path = self._get_cache_path(self.CLASSIFICATION_CACHE)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
            return data.get("results")
    
    def has_classification_cache(self) -> bool:
        """Check if classification cache exists."""
        return self._get_cache_path(self.CLASSIFICATION_CACHE).exists()
    
    # ==================== Analysis Results ====================
    
    def save_analysis(self, analysis: dict) -> None:
        """Save deep analysis results to cache."""
        cache_data = {
            "analysis": analysis,
            "cached_at": datetime.now().isoformat()
        }
        
        with open(self._get_cache_path(self.ANALYSIS_CACHE), 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        self.metadata["cache_versions"]["analysis"] = {
            "cached_at": cache_data["cached_at"]
        }
        self._save_metadata()
    
    def load_analysis(self) -> Optional[dict]:
        """Load cached analysis results."""
        cache_path = self._get_cache_path(self.ANALYSIS_CACHE)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
            return data.get("analysis")
    
    def has_analysis_cache(self) -> bool:
        """Check if analysis cache exists."""
        return self._get_cache_path(self.ANALYSIS_CACHE).exists()
    
    # ==================== Polymarket Data ====================
    
    def save_polymarket(self, odds_data: dict) -> None:
        """Save Polymarket odds to cache (JSON for readability)."""
        odds_data["cached_at"] = datetime.now().isoformat()
        
        with open(self._get_cache_path(self.POLYMARKET_CACHE), 'w') as f:
            json.dump(odds_data, f, indent=2, cls=DateTimeEncoder)
        
        self.metadata["cache_versions"]["polymarket"] = {
            "cached_at": odds_data["cached_at"]
        }
        self._save_metadata()

    def save_polymarket_comments_snapshot(self, comments: list) -> str:
        """
        Save a timestamped snapshot of Polymarket comments (append-only).

        Returns the relative path (under cache/) to the saved JSON file.
        """
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = self.cache_dir / self.POLYMARKET_COMMENTS_DIR
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = f"comments_{ts}.json"
            path = out_dir / filename
            with open(path, "w", encoding="utf-8") as f:
                json.dump(comments or [], f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            return str(path.relative_to(self.cache_dir.parent)) if self.cache_dir.parent in path.parents else str(path)
        except Exception:
            return ""
    
    def load_polymarket(self) -> Optional[dict]:
        """Load cached Polymarket odds."""
        cache_path = self._get_cache_path(self.POLYMARKET_CACHE)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r') as f:
            return json.load(f)
    
    def has_polymarket_cache(self) -> bool:
        """Check if Polymarket cache exists."""
        return self._get_cache_path(self.POLYMARKET_CACHE).exists()
    
    # ==================== News Data ====================
    
    def _log_duplicate(self, item_type: str, item_id: str, source: str = ""):
        """Log duplicate detection for debugging."""
        try:
            log_path = self._get_cache_path(self.DUPLICATE_LOG)
            with open(log_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] DUPLICATE {item_type}: {item_id} (source: {source})\n")
        except Exception:
            pass  # Logging should not break main flow
    
    def save_news(
        self,
        articles: list,
        analysis: Optional[dict] = None,
        source_info: Optional[dict] = None,
    ) -> str:
        """
        Save news articles to cache with append-only merge logic.
        
        Articles are deduped by URL (primary) and title+source (fallback).
        Existing articles are never removed - new ones are appended.
        
        Returns cache key for reference.
        """
        cache_key = f"news_{datetime.now().strftime('%Y%m%d')}"
        
        # Load existing if any
        existing = self.load_news() if self.has_news_cache() else None
        existing_articles = (existing or {}).get("articles", []) if isinstance(existing, dict) else []
        
        # Build index of existing articles by URL and title+source
        url_index: dict[str, int] = {}
        title_source_index: dict[str, int] = {}
        
        for idx, art in enumerate(existing_articles):
            if not isinstance(art, dict):
                continue
            url = self._normalize_id(art.get("url"))
            if url:
                url_index[url] = idx
            # Fallback: title + source
            title = self._normalize_id(art.get("title", ""))
            source = self._normalize_id(art.get("source", ""))
            if title and source:
                title_source_index[f"{title}::{source}"] = idx
        
        # Merge incoming articles
        merged_articles = list(existing_articles)
        duplicates_found = 0
        new_added = 0
        
        for art in (articles or []):
            if not isinstance(art, dict):
                continue
            
            url = self._normalize_id(art.get("url"))
            title = self._normalize_id(art.get("title", ""))
            source = self._normalize_id(art.get("source", ""))
            
            # Check for duplicates
            is_duplicate = False
            
            if url and url in url_index:
                is_duplicate = True
                # Update existing record
                merged_articles[url_index[url]] = art
                self._log_duplicate("news_article", url, source)
                duplicates_found += 1
            elif title and source:
                key = f"{title}::{source}"
                if key in title_source_index:
                    is_duplicate = True
                    merged_articles[title_source_index[key]] = art
                    self._log_duplicate("news_article", key, source)
                    duplicates_found += 1
            
            if not is_duplicate:
                # New article - add to list and update indices
                idx = len(merged_articles)
                merged_articles.append(art)
                if url:
                    url_index[url] = idx
                if title and source:
                    title_source_index[f"{title}::{source}"] = idx
                new_added += 1
        
        # Merge analysis data
        existing_analysis = (existing or {}).get("analysis", {}) if isinstance(existing, dict) else {}
        merged_analysis = {**existing_analysis, **(analysis or {})}
        
        # Merge source info
        existing_sources = (existing or {}).get("sources_used", []) if isinstance(existing, dict) else []
        new_sources = (source_info or {}).get("sources", []) if isinstance(source_info, dict) else []
        merged_sources = sorted(set(existing_sources) | set(new_sources))
        
        first_cached_at = (existing or {}).get("first_cached_at") if isinstance(existing, dict) else None
        if not first_cached_at:
            first_cached_at = datetime.now().isoformat()
        
        cache_data = {
            "articles": merged_articles,
            "analysis": merged_analysis,
            "sources_used": merged_sources,
            "total_articles": len(merged_articles),
            "first_cached_at": first_cached_at,
            "cached_at": datetime.now().isoformat(),
            "last_merge_stats": {
                "duplicates_found": duplicates_found,
                "new_added": new_added,
                "timestamp": datetime.now().isoformat()
            },
            "note": "Append-only news cache. Articles deduped by URL or title+source."
        }
        
        with open(self._get_cache_path(self.NEWS_CACHE), 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        self.metadata["cache_versions"]["news"] = {
            "key": cache_key,
            "cached_at": cache_data["cached_at"],
            "stats": {
                "total_articles": len(merged_articles),
                "sources": len(merged_sources),
                "duplicates_last_run": duplicates_found,
                "new_last_run": new_added
            }
        }
        self._save_metadata()
        
        return cache_key
    
    def load_news(self) -> Optional[dict]:
        """Load cached news data. Returns None if not found."""
        cache_path = self._get_cache_path(self.NEWS_CACHE)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    
    def has_news_cache(self) -> bool:
        """Check if news cache exists."""
        return self._get_cache_path(self.NEWS_CACHE).exists()
    
    # ==================== Polymarket Comments Append ====================
    
    def save_polymarket_comments_merged(
        self,
        comments: list,
        market_info: Optional[dict] = None,
    ) -> dict:
        """
        Save Polymarket comments with append-only merge logic.
        
        Comments are deduped by comment_id or (author + text hash).
        Returns merge statistics.
        """
        cache_path = self._get_cache_path(self.POLYMARKET_COMMENTS_DIR) / "merged_comments.pkl"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing if any
        existing_comments = []
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    existing_data = pickle.load(f)
                    existing_comments = existing_data.get("comments", []) if isinstance(existing_data, dict) else []
            except Exception:
                existing_comments = []
        
        # Build index
        comment_index: dict[str, int] = {}
        text_hash_index: dict[str, int] = {}
        
        for idx, c in enumerate(existing_comments):
            if not isinstance(c, dict):
                continue
            cid = self._normalize_id(c.get("comment_id") or c.get("id"))
            if cid:
                comment_index[cid] = idx
            # Fallback: author + text hash
            author = c.get("author", "")
            text = c.get("text", "")
            if author and text:
                text_hash = hashlib.md5(f"{author}::{text[:100]}".encode()).hexdigest()[:16]
                text_hash_index[text_hash] = idx
        
        # Merge
        merged = list(existing_comments)
        duplicates = 0
        new_added = 0
        
        for c in (comments or []):
            if not isinstance(c, dict):
                continue
            
            cid = self._normalize_id(c.get("comment_id") or c.get("id"))
            author = c.get("author", "")
            text = c.get("text", "")
            
            is_dup = False
            
            if cid and cid in comment_index:
                merged[comment_index[cid]] = c
                is_dup = True
                duplicates += 1
                self._log_duplicate("polymarket_comment", cid, author)
            elif author and text:
                text_hash = hashlib.md5(f"{author}::{text[:100]}".encode()).hexdigest()[:16]
                if text_hash in text_hash_index:
                    merged[text_hash_index[text_hash]] = c
                    is_dup = True
                    duplicates += 1
                    self._log_duplicate("polymarket_comment", text_hash, author)
            
            if not is_dup:
                idx = len(merged)
                merged.append(c)
                if cid:
                    comment_index[cid] = idx
                if author and text:
                    text_hash = hashlib.md5(f"{author}::{text[:100]}".encode()).hexdigest()[:16]
                    text_hash_index[text_hash] = idx
                new_added += 1
        
        cache_data = {
            "comments": merged,
            "market_info": market_info or {},
            "total_comments": len(merged),
            "cached_at": datetime.now().isoformat(),
            "last_merge_stats": {
                "duplicates_found": duplicates,
                "new_added": new_added,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        return {
            "total": len(merged),
            "duplicates": duplicates,
            "new_added": new_added
        }
    
    def load_polymarket_comments_merged(self) -> list:
        """Load merged Polymarket comments."""
        cache_path = self._get_cache_path(self.POLYMARKET_COMMENTS_DIR) / "merged_comments.pkl"
        if not cache_path.exists():
            return []
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                return data.get("comments", []) if isinstance(data, dict) else []
        except Exception:
            return []
    
    # ==================== Reports ====================
    
    def save_report(self, report_content: str, report_type: str = "full") -> str:
        """
        Save analysis report to cache.
        
        Returns the filename of the saved report.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report_type}_{timestamp}.md"
        report_path = self.cache_dir / self.REPORT_CACHE / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return filename
    
    def list_reports(self) -> list:
        """List all saved reports."""
        reports_dir = self.cache_dir / self.REPORT_CACHE
        return sorted([f.name for f in reports_dir.glob("*.md")], reverse=True)
    
    def load_report(self, filename: str) -> Optional[str]:
        """Load a specific report by filename."""
        report_path = self.cache_dir / self.REPORT_CACHE / filename
        if not report_path.exists():
            return None
        
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # ==================== Cache Management ====================
    
    def get_cache_status(self) -> dict:
        """Get status of all caches."""
        return {
            "cache_dir": str(self.cache_dir),
            "comments": {
                "exists": self.has_comments_cache(),
                "info": self.metadata.get("cache_versions", {}).get("comments")
            },
            "classification": {
                "exists": self.has_classification_cache(),
                "info": self.metadata.get("cache_versions", {}).get("classification")
            },
            "analysis": {
                "exists": self.has_analysis_cache(),
                "info": self.metadata.get("cache_versions", {}).get("analysis")
            },
            "polymarket": {
                "exists": self.has_polymarket_cache(),
                "info": self.metadata.get("cache_versions", {}).get("polymarket")
            },
            "reports": self.list_reports()
        }
    
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        Clear cache files.
        
        Args:
            cache_type: Specific cache to clear ('comments', 'classification', 
                       'analysis', 'polymarket', 'reports') or None for all.
        """
        cache_files = {
            "comments": self.COMMENTS_CACHE,
            "classification": self.CLASSIFICATION_CACHE,
            "analysis": self.ANALYSIS_CACHE,
            "polymarket": self.POLYMARKET_CACHE
        }
        
        if cache_type is None:
            # Clear all
            for filename in cache_files.values():
                path = self._get_cache_path(filename)
                if path.exists():
                    path.unlink()
            
            # Clear reports
            for report in (self.cache_dir / self.REPORT_CACHE).glob("*.md"):
                report.unlink()
            
            self.metadata["cache_versions"] = {}
            self._save_metadata()
            
        elif cache_type == "reports":
            for report in (self.cache_dir / self.REPORT_CACHE).glob("*.md"):
                report.unlink()
                
        elif cache_type in cache_files:
            path = self._get_cache_path(cache_files[cache_type])
            if path.exists():
                path.unlink()
            
            if cache_type in self.metadata.get("cache_versions", {}):
                del self.metadata["cache_versions"][cache_type]
                self._save_metadata()
    
    def export_to_json(self, output_file: str = "full_export.json") -> str:
        """Export all cached data to a single JSON file for external use."""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metadata": self.metadata
        }
        
        # Load all caches
        if self.has_comments_cache():
            comments_data = self.load_comments()
            # Convert comments to JSON-serializable format
            export_data["comments"] = {
                "subreddits": comments_data.get("subreddits"),
                "time_filter": comments_data.get("time_filter"),
                "total_authors": comments_data.get("total_authors"),
                "total_comments": comments_data.get("total_comments"),
                "cached_at": comments_data.get("cached_at"),
                # Sample of comments (full export would be too large)
                "sample_authors": list(comments_data.get("comments_by_author", {}).keys())[:100]
            }
        
        if self.has_classification_cache():
            export_data["classification"] = self.load_classification()
        
        if self.has_analysis_cache():
            export_data["analysis"] = self.load_analysis()
        
        if self.has_polymarket_cache():
            export_data["polymarket"] = self.load_polymarket()
        
        output_path = self.cache_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        
        return str(output_path)
