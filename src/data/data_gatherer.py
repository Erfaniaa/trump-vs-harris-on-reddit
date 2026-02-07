"""
Data Gatherer - Collects Reddit comments with detailed metadata and caching support.

Enhanced with optional concurrent fetching for improved performance.
"""

import praw
import prawcore
import time
import random
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class CommentData:
    """Structured data for a single comment."""
    body: str
    author: str
    subreddit: str
    post_title: str
    post_id: str
    comment_id: str
    score: int
    created_utc: float
    is_top_level: bool
    
    @property
    def created_date(self) -> str:
        """Human-readable date string."""
        return datetime.fromtimestamp(self.created_utc).strftime("%Y-%m-%d %H:%M")
    
    @property
    def days_ago(self) -> int:
        """Number of days since comment was posted."""
        return (datetime.now() - datetime.fromtimestamp(self.created_utc)).days
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['created_date'] = self.created_date
        d['days_ago'] = self.days_ago
        return d


@dataclass
class PostData:
    """Structured data for a post."""
    title: str
    post_id: str
    subreddit: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: float
    url: str
    
    @property
    def created_date(self) -> str:
        """Human-readable date string."""
        return datetime.fromtimestamp(self.created_utc).strftime("%Y-%m-%d %H:%M")
    
    @property
    def days_ago(self) -> int:
        """Number of days since post was created."""
        return (datetime.now() - datetime.fromtimestamp(self.created_utc)).days
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['created_date'] = self.created_date
        d['days_ago'] = self.days_ago
        return d


@dataclass
class GatheringStats:
    """Statistics about the data gathering process."""
    total_subreddits_processed: int = 0
    total_posts_processed: int = 0
    total_comments_collected: int = 0
    total_unique_authors: int = 0
    failed_subreddits: list = field(default_factory=list)
    subreddit_stats: dict = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class DataGatherer:
    """
    Collects Reddit comments with detailed metadata.
    Supports filtering, statistics tracking, and structured data output.
    """

    # Bots and auto-moderators to ignore
    IGNORED_AUTHORS = {
        "AutoModerator", "RemindMeBot", "WikiTextBot", "imguralbumbot",
        "sneakpeekbot", "TotesMessenger", "CommonMisspellingBot",
        "HelperBot_", "sub_doesnt_exist_bot", "RepostSleuthBot",
        "Bot", "bot", "AutoBot"
    }

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        subreddit_names_list: list[str],
        maximum_posts_per_subreddit: int,
        top_posts_time_filter: str,
        min_comment_length: int = 50,
        max_comment_length: int = 10000,
        context_keywords: Optional[list[str]] = None,
        # Performance tuning
        max_comments_per_post: int = 400,
        max_comments_per_subreddit: int = 12000,
        include_recent_comment_feed: bool = True,
        recent_comments_per_subreddit: int = 1500,
        submission_comment_sort: str = "top",
        replace_more_limit: int = 2,
        # Concurrent fetching options
        use_concurrent: bool = False,
        max_workers: int = 3,
    ):
        """
        Initialize the data gatherer.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            subreddit_names_list: List of subreddit names to scrape
            maximum_posts_per_subreddit: Max posts to process per subreddit
            top_posts_time_filter: Time filter for top posts
            min_comment_length: Minimum comment length to include
            max_comment_length: Maximum comment length to include
            context_keywords: If provided, only include comments containing these keywords
        """
        self.subreddit_names_list = subreddit_names_list
        self.maximum_posts_per_subreddit = maximum_posts_per_subreddit
        self.top_posts_time_filter = top_posts_time_filter
        self.min_comment_length = min_comment_length
        self.max_comment_length = max_comment_length
        self.context_keywords = [kw.lower() for kw in (context_keywords or [])]

        # Performance tuning (all optional, safe defaults)
        self.max_comments_per_post = int(max_comments_per_post or 0)
        self.max_comments_per_subreddit = int(max_comments_per_subreddit or 0)
        self.include_recent_comment_feed = bool(include_recent_comment_feed)
        self.recent_comments_per_subreddit = int(recent_comments_per_subreddit or 0)
        self.submission_comment_sort = str(submission_comment_sort or "top")
        self.replace_more_limit = int(replace_more_limit or 0)
        
        # Concurrent fetching options
        # Reddit API rate limits are handled by PRAW with exponential backoff,
        # so we can safely use higher concurrency for I/O-bound operations.
        self.use_concurrent = bool(use_concurrent)
        self.max_workers = max(1, min(int(max_workers or 16), 16))  # Support up to 16 workers
        
        # Store credentials for creating per-thread clients
        self._client_id = client_id
        self._client_secret = client_secret
        
        self.reddit_client = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="IranConflictAnalyzer/2.0 (Research Project)",
            # Prevent indefinite hangs on network stalls:
            # PRAW passes this through to the underlying requests session.
            requestor_kwargs={"timeout": 20},
        )
        
        # Data storage
        self.comments_by_author: dict[str, list[CommentData]] = defaultdict(list)
        self.all_comments: list[CommentData] = []
        self.all_posts: list[PostData] = []
        self.stats = GatheringStats()
        self._seen_comment_ids: set[str] = set()
        self._seen_post_ids: set[str] = set()
        
        # Thread safety locks for concurrent mode
        self._data_lock = threading.Lock()
        self._progress_lock = threading.Lock()
    
    def _create_reddit_client(self) -> praw.Reddit:
        """Create a new Reddit client instance (for thread safety in concurrent mode)."""
        return praw.Reddit(
            client_id=self._client_id,
            client_secret=self._client_secret,
            user_agent=f"IranConflictAnalyzer/2.0-{threading.current_thread().name}",
            requestor_kwargs={"timeout": 20},
        )

    def _iter_comment_tree_limited(self, submission, limit: int):
        """
        Iterate a submission's comment tree without building a giant list.
        This is much faster (and uses less memory) than submission.comments.list().
        """
        if limit <= 0:
            return
        q = deque()
        try:
            for c in submission.comments:
                q.append(c)
        except Exception:
            return

        yielded = 0
        while q and yielded < limit:
            c = q.popleft()
            # Skip MoreComments placeholders
            try:
                from praw.models import MoreComments
                if isinstance(c, MoreComments):
                    continue
            except Exception:
                pass
            yield c
            yielded += 1
            try:
                # replies is a CommentForest (iterable). This should not trigger extra calls if replace_more ran.
                for r in getattr(c, "replies", []) or []:
                    q.append(r)
            except Exception:
                continue

    def _is_valid_author(self, author) -> bool:
        """Check if author is valid (not deleted, not a bot)."""
        if author is None:
            return False
        if author.name in self.IGNORED_AUTHORS:
            return False
        if "bot" in author.name.lower():
            return False
        return True

    def _is_valid_comment(self, comment_body: str) -> bool:
        """Check if comment meets length requirements."""
        length = len(comment_body)
        return self.min_comment_length <= length <= self.max_comment_length

    def _contains_context_keyword(self, text: str) -> bool:
        """Check if text contains any context keyword."""
        if not self.context_keywords:
            return True  # No filter if no keywords specified
        
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.context_keywords)

    def _process_subreddit(self, subreddit_name: str, reddit_client: Optional[praw.Reddit] = None) -> dict:
        """
        Process a single subreddit and return stats.
        
        Args:
            subreddit_name: Name of the subreddit to process
            reddit_client: Optional Reddit client (for thread-safe concurrent mode)
        """
        # Use provided client or default (for sequential mode)
        client = reddit_client or self.reddit_client
        
        subreddit_stats = {
            "posts_processed": 0,
            "comments_collected": 0,
            "unique_authors": set(),
            "error": None
        }
        
        # Thread-local storage for comments/posts before merging
        local_comments: List[CommentData] = []
        local_posts: List[PostData] = []
        local_comment_ids: set = set()
        local_post_ids: set = set()
        
        # Retry loop to handle transient 429s gracefully.
        for attempt in range(3):
            try:
                subreddit = client.subreddit(subreddit_name)
                top_posts = subreddit.top(time_filter=self.top_posts_time_filter, limit=self.maximum_posts_per_subreddit)
                
                collected_in_sub = 0
                for post in top_posts:
                    if self.max_comments_per_subreddit and collected_in_sub >= self.max_comments_per_subreddit:
                        break

                    # Store post data
                    post_data = PostData(
                        title=post.title,
                        post_id=post.id,
                        subreddit=subreddit_name,
                        score=post.score,
                        upvote_ratio=post.upvote_ratio,
                        num_comments=post.num_comments,
                        created_utc=post.created_utc,
                        url=post.url
                    )
                    # Deduplicate posts
                    if post.id not in self._seen_post_ids:
                        self._seen_post_ids.add(post.id)
                        self.all_posts.append(post_data)
                    
                    # Process comments (this can trigger additional API calls)
                    try:
                        post.comment_sort = self.submission_comment_sort
                    except Exception:
                        pass

                    # Avoid fetching the entire tree. Small replace_more_limit keeps it fast.
                    try:
                        post.comments.replace_more(limit=max(0, self.replace_more_limit))
                    except Exception:
                        pass

                    per_post_cap = self.max_comments_per_post or 0
                    if per_post_cap <= 0:
                        per_post_cap = 400

                    for comment in self._iter_comment_tree_limited(post, limit=per_post_cap):
                        if self.max_comments_per_subreddit and collected_in_sub >= self.max_comments_per_subreddit:
                            break
                        if not self._is_valid_author(comment.author):
                            continue
                        
                        if not self._is_valid_comment(comment.body):
                            continue

                        # Deduplicate by comment id (global)
                        if getattr(comment, "id", None) in self._seen_comment_ids:
                            continue
                        
                        # Check context keywords
                        if not self._contains_context_keyword(comment.body):
                            continue
                        
                        # Create comment data
                        comment_data = CommentData(
                            body=comment.body,
                            author=comment.author.name,
                            subreddit=subreddit_name,
                            post_title=post.title,
                            post_id=post.id,
                            comment_id=comment.id,
                            score=comment.score,
                            created_utc=comment.created_utc,
                            is_top_level=comment.parent_id == f"t3_{post.id}"
                        )
                        
                        self.all_comments.append(comment_data)
                        self.comments_by_author[comment.author.name].append(comment_data)
                        self._seen_comment_ids.add(comment.id)
                        
                        subreddit_stats["comments_collected"] += 1
                        subreddit_stats["unique_authors"].add(comment.author.name)
                        collected_in_sub += 1
                    
                    subreddit_stats["posts_processed"] += 1
                    
                    # Progress update
                    self.stats.total_posts_processed += 1
                    if self.stats.total_posts_processed % 10 == 0:
                        print(f"  Progress: {self.stats.total_posts_processed} posts, "
                              f"{len(self.all_comments)} comments collected")

                    # Light pacing to reduce 429s on large runs.
                    # This is intentionally small; TooManyRequests handling remains the main backoff mechanism.
                    time.sleep(0.05)
                
                # Success: break retry loop
                break
            except prawcore.exceptions.TooManyRequests as e:
                # Respect the server-provided retry-after when available.
                retry_after = None
                try:
                    retry_after = int(getattr(e, "retry_after", None) or 0)
                except Exception:
                    retry_after = None
                if not retry_after:
                    # Exponential backoff with jitter as fallback.
                    retry_after = int((2 ** attempt) * 15 + random.randint(0, 10))
                print(f"  ⏳ Rate limited on r/{subreddit_name} (HTTP 429). Sleeping {retry_after}s then retrying...")
                time.sleep(retry_after)
                continue
            except Exception as e:
                subreddit_stats["error"] = str(e)
                self.stats.failed_subreddits.append({
                    "name": subreddit_name,
                    "error": str(e)
                })
                print(f"  ⚠️  Error processing r/{subreddit_name}: {e}")
                break

        # Also fetch recent comments feed (cheap, captures fresh updates)
        if self.include_recent_comment_feed and self.recent_comments_per_subreddit > 0:
            try:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                for comment in subreddit.comments(limit=self.recent_comments_per_subreddit):
                    if self.max_comments_per_subreddit and subreddit_stats["comments_collected"] >= self.max_comments_per_subreddit:
                        break
                    if not self._is_valid_author(comment.author):
                        continue
                    if not self._is_valid_comment(comment.body):
                        continue
                    if getattr(comment, "id", None) in self._seen_comment_ids:
                        continue
                    if not self._contains_context_keyword(comment.body):
                        continue

                    # Best-effort context (submission fetch may be cached by PRAW; keep guarded)
                    post_title = ""
                    post_id = ""
                    try:
                        post_id = str(getattr(comment, "link_id", "")).replace("t3_", "")
                    except Exception:
                        post_id = ""
                    try:
                        # Accessing submission may trigger an extra API call; avoid hard dependency
                        post_title = getattr(getattr(comment, "submission", None), "title", "") or ""
                    except Exception:
                        post_title = ""

                    comment_data = CommentData(
                        body=comment.body,
                        author=comment.author.name,
                        subreddit=subreddit_name,
                        post_title=post_title,
                        post_id=post_id,
                        comment_id=comment.id,
                        score=getattr(comment, "score", 0),
                        created_utc=getattr(comment, "created_utc", 0.0),
                        is_top_level=str(getattr(comment, "parent_id", "")).startswith("t3_"),
                    )
                    self.all_comments.append(comment_data)
                    self.comments_by_author[comment.author.name].append(comment_data)
                    self._seen_comment_ids.add(comment.id)
                    subreddit_stats["comments_collected"] += 1
                    subreddit_stats["unique_authors"].add(comment.author.name)
            except Exception:
                # Recent feed is best-effort; ignore failures.
                pass
        
        # Convert set to count for JSON serialization
        subreddit_stats["unique_authors"] = len(subreddit_stats["unique_authors"])
        
        return subreddit_stats

    def gather_data(self, progress_callback=None) -> dict:
        """
        Gather comments from all configured subreddits.
        
        Uses concurrent fetching if self.use_concurrent is True.
        
        Args:
            progress_callback: Optional callback function(subreddit_name, stats)
        
        Returns:
            Dictionary with all gathered data and statistics
        """
        if self.use_concurrent:
            return self._gather_data_concurrent(progress_callback)
        else:
            return self._gather_data_sequential(progress_callback)
    
    def _gather_data_sequential(self, progress_callback=None) -> dict:
        """Sequential (original) data gathering method."""
        self.stats.started_at = datetime.now().isoformat()
        print(f"\n📥 Starting SEQUENTIAL data collection from {len(self.subreddit_names_list)} subreddits...")
        print(f"   Settings: {self.maximum_posts_per_subreddit} posts/subreddit, "
              f"time filter: {self.top_posts_time_filter}")
        
        consecutive_network_errors = 0
        fatal_network_error = None

        for i, subreddit_name in enumerate(self.subreddit_names_list, 1):
            print(f"\n[{i}/{len(self.subreddit_names_list)}] Processing r/{subreddit_name}...")
            
            subreddit_stats = self._process_subreddit(subreddit_name)
            self.stats.subreddit_stats[subreddit_name] = subreddit_stats
            self.stats.total_subreddits_processed += 1

            # Detect recurring DNS/network failures and abort early.
            err = str(subreddit_stats.get("error") or "")
            if "NameResolutionError" in err or "Temporary failure in name resolution" in err or "Failed to resolve" in err:
                consecutive_network_errors += 1
                fatal_network_error = err
            else:
                consecutive_network_errors = 0

            if consecutive_network_errors >= 5:
                print("\n🛑 Detected repeated network/DNS errors to Reddit API. Aborting data gathering early.")
                break
            
            if progress_callback:
                progress_callback(subreddit_name, subreddit_stats)
        
        # Finalize stats
        self.stats.total_comments_collected = len(self.all_comments)
        self.stats.total_unique_authors = len(self.comments_by_author)
        self.stats.completed_at = datetime.now().isoformat()
        
        print(f"\n✅ Data collection complete!")
        print(f"   📊 {self.stats.total_subreddits_processed} subreddits processed")
        print(f"   📝 {self.stats.total_posts_processed} posts processed")
        print(f"   💬 {self.stats.total_comments_collected} comments collected")
        print(f"   👥 {self.stats.total_unique_authors} unique authors")
        
        if self.stats.failed_subreddits:
            print(f"   ⚠️  {len(self.stats.failed_subreddits)} subreddits failed")
        
        results = self.get_results()
        if fatal_network_error:
            results["fatal_error"] = {
                "type": "network_dns",
                "message": fatal_network_error,
                "consecutive_failures": consecutive_network_errors,
            }
        return results
    
    def _gather_data_concurrent(self, progress_callback=None) -> dict:
        """
        Concurrent data gathering using ThreadPoolExecutor.
        
        Each worker thread gets its own PRAW client instance to avoid
        thread-safety issues. Results are merged after all workers complete.
        
        This can significantly speed up data collection when Reddit API
        rate limits are not a bottleneck.
        """
        self.stats.started_at = datetime.now().isoformat()
        print(f"\n📥 Starting CONCURRENT data collection from {len(self.subreddit_names_list)} subreddits...")
        print(f"   Settings: {self.maximum_posts_per_subreddit} posts/subreddit, "
              f"time filter: {self.top_posts_time_filter}, workers: {self.max_workers}")
        
        # Thread-local results storage
        all_results: Dict[str, Any] = {}
        completed_count = [0]  # Use list for closure mutation
        
        def process_subreddit_worker(subreddit_name: str) -> Dict[str, Any]:
            """Worker function that runs in a separate thread."""
            # Create thread-local PRAW client
            thread_client = self._create_reddit_client()
            
            # Create thread-local storage
            local_comments: List[CommentData] = []
            local_posts: List[PostData] = []
            local_comments_by_author: Dict[str, List[CommentData]] = defaultdict(list)
            seen_comment_ids: set = set()
            seen_post_ids: set = set()
            
            subreddit_stats = {
                "posts_processed": 0,
                "comments_collected": 0,
                "unique_authors": set(),
                "error": None
            }
            
            # Retry loop
            for attempt in range(3):
                try:
                    subreddit = thread_client.subreddit(subreddit_name)
                    top_posts = subreddit.top(
                        time_filter=self.top_posts_time_filter,
                        limit=self.maximum_posts_per_subreddit
                    )
                    
                    collected_in_sub = 0
                    for post in top_posts:
                        if self.max_comments_per_subreddit and collected_in_sub >= self.max_comments_per_subreddit:
                            break
                        
                        # Store post data
                        if post.id not in seen_post_ids:
                            seen_post_ids.add(post.id)
                            local_posts.append(PostData(
                                title=post.title,
                                post_id=post.id,
                                subreddit=subreddit_name,
                                score=post.score,
                                upvote_ratio=post.upvote_ratio,
                                num_comments=post.num_comments,
                                created_utc=post.created_utc,
                                url=post.url
                            ))
                        
                        # Process comments
                        try:
                            post.comment_sort = self.submission_comment_sort
                            post.comments.replace_more(limit=max(0, self.replace_more_limit))
                        except Exception:
                            pass
                        
                        per_post_cap = self.max_comments_per_post or 400
                        
                        for comment in self._iter_comment_tree_limited(post, limit=per_post_cap):
                            if self.max_comments_per_subreddit and collected_in_sub >= self.max_comments_per_subreddit:
                                break
                            if not self._is_valid_author(comment.author):
                                continue
                            if not self._is_valid_comment(comment.body):
                                continue
                            if getattr(comment, "id", None) in seen_comment_ids:
                                continue
                            if not self._contains_context_keyword(comment.body):
                                continue
                            
                            comment_data = CommentData(
                                body=comment.body,
                                author=comment.author.name,
                                subreddit=subreddit_name,
                                post_title=post.title,
                                post_id=post.id,
                                comment_id=comment.id,
                                score=comment.score,
                                created_utc=comment.created_utc,
                                is_top_level=comment.parent_id == f"t3_{post.id}"
                            )
                            
                            local_comments.append(comment_data)
                            local_comments_by_author[comment.author.name].append(comment_data)
                            seen_comment_ids.add(comment.id)
                            
                            subreddit_stats["comments_collected"] += 1
                            subreddit_stats["unique_authors"].add(comment.author.name)
                            collected_in_sub += 1
                        
                        subreddit_stats["posts_processed"] += 1
                        time.sleep(0.05)  # Light pacing
                    
                    break  # Success
                    
                except prawcore.exceptions.TooManyRequests as e:
                    retry_after = None
                    try:
                        retry_after = int(getattr(e, "retry_after", None) or 0)
                    except Exception:
                        retry_after = None
                    if not retry_after:
                        retry_after = int((2 ** attempt) * 15 + random.randint(0, 10))
                    
                    with self._progress_lock:
                        print(f"  ⏳ Rate limited on r/{subreddit_name} (429). Sleeping {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                    
                except Exception as e:
                    subreddit_stats["error"] = str(e)
                    break
            
            # Recent comments feed
            if self.include_recent_comment_feed and self.recent_comments_per_subreddit > 0:
                try:
                    for comment in thread_client.subreddit(subreddit_name).comments(
                        limit=self.recent_comments_per_subreddit
                    ):
                        if self.max_comments_per_subreddit and subreddit_stats["comments_collected"] >= self.max_comments_per_subreddit:
                            break
                        if not self._is_valid_author(comment.author):
                            continue
                        if not self._is_valid_comment(comment.body):
                            continue
                        if getattr(comment, "id", None) in seen_comment_ids:
                            continue
                        if not self._contains_context_keyword(comment.body):
                            continue
                        
                        post_id = str(getattr(comment, "link_id", "")).replace("t3_", "")
                        post_title = ""
                        try:
                            post_title = getattr(getattr(comment, "submission", None), "title", "") or ""
                        except Exception:
                            pass
                        
                        comment_data = CommentData(
                            body=comment.body,
                            author=comment.author.name,
                            subreddit=subreddit_name,
                            post_title=post_title,
                            post_id=post_id,
                            comment_id=comment.id,
                            score=getattr(comment, "score", 0),
                            created_utc=getattr(comment, "created_utc", 0.0),
                            is_top_level=str(getattr(comment, "parent_id", "")).startswith("t3_"),
                        )
                        local_comments.append(comment_data)
                        local_comments_by_author[comment.author.name].append(comment_data)
                        seen_comment_ids.add(comment.id)
                        subreddit_stats["comments_collected"] += 1
                        subreddit_stats["unique_authors"].add(comment.author.name)
                except Exception:
                    pass
            
            subreddit_stats["unique_authors"] = len(subreddit_stats["unique_authors"])
            
            # Progress update
            with self._progress_lock:
                completed_count[0] += 1
                print(f"  [{completed_count[0]}/{len(self.subreddit_names_list)}] Completed r/{subreddit_name}: "
                      f"{subreddit_stats['comments_collected']} comments")
            
            return {
                "subreddit": subreddit_name,
                "stats": subreddit_stats,
                "comments": local_comments,
                "posts": local_posts,
                "comments_by_author": dict(local_comments_by_author),
            }
        
        # Run workers in thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_subreddit_worker, sub): sub
                for sub in self.subreddit_names_list
            }
            
            for future in as_completed(futures):
                subreddit_name = futures[future]
                try:
                    result = future.result()
                    all_results[result["subreddit"]] = result
                except Exception as e:
                    print(f"  ⚠️ Worker error for r/{subreddit_name}: {e}")
                    all_results[subreddit_name] = {
                        "subreddit": subreddit_name,
                        "stats": {"error": str(e), "posts_processed": 0, "comments_collected": 0, "unique_authors": 0},
                        "comments": [],
                        "posts": [],
                        "comments_by_author": {},
                    }
                
                if progress_callback:
                    progress_callback(subreddit_name, all_results[subreddit_name].get("stats", {}))
        
        # Merge results
        print("\n🔄 Merging results from all workers...")
        for sub_name, result in all_results.items():
            self.stats.subreddit_stats[sub_name] = result["stats"]
            self.stats.total_subreddits_processed += 1
            
            if result["stats"].get("error"):
                self.stats.failed_subreddits.append({
                    "name": sub_name,
                    "error": result["stats"]["error"]
                })
            
            # Merge comments (with deduplication)
            for comment in result.get("comments", []):
                if comment.comment_id not in self._seen_comment_ids:
                    self._seen_comment_ids.add(comment.comment_id)
                    self.all_comments.append(comment)
                    self.comments_by_author[comment.author].append(comment)
            
            # Merge posts (with deduplication)
            for post in result.get("posts", []):
                if post.post_id not in self._seen_post_ids:
                    self._seen_post_ids.add(post.post_id)
                    self.all_posts.append(post)
            
            self.stats.total_posts_processed += result["stats"].get("posts_processed", 0)
        
        # Finalize stats
        self.stats.total_comments_collected = len(self.all_comments)
        self.stats.total_unique_authors = len(self.comments_by_author)
        self.stats.completed_at = datetime.now().isoformat()
        
        print(f"\n✅ Concurrent data collection complete!")
        print(f"   📊 {self.stats.total_subreddits_processed} subreddits processed")
        print(f"   📝 {self.stats.total_posts_processed} posts processed")
        print(f"   💬 {self.stats.total_comments_collected} comments collected")
        print(f"   👥 {self.stats.total_unique_authors} unique authors")
        
        if self.stats.failed_subreddits:
            print(f"   ⚠️  {len(self.stats.failed_subreddits)} subreddits failed")
        
        return self.get_results()

    def get_results(self) -> dict:
        """Get all gathered data in a structured format."""
        return {
            "comments_by_author": {
                author: [c.to_dict() for c in comments]
                for author, comments in self.comments_by_author.items()
            },
            "all_comments": [c.to_dict() for c in self.all_comments],
            "all_posts": [p.to_dict() for p in self.all_posts],
            "statistics": self.stats.to_dict(),
            "config": {
                "subreddits": self.subreddit_names_list,
                "max_posts_per_subreddit": self.maximum_posts_per_subreddit,
                "time_filter": self.top_posts_time_filter,
                "min_comment_length": self.min_comment_length,
                "max_comment_length": self.max_comment_length,
                "context_keywords": self.context_keywords
            }
        }

    def get_comments_list_by_author(self, subreddit_name: str = "all") -> dict[str, list[str]]:
        """
        Legacy method for backward compatibility.
        Returns simple dict of author -> list of comment bodies.
        """
        if not self.comments_by_author:
            self.gather_data()
        
        return {
            author: [c.body for c in comments]
            for author, comments in self.comments_by_author.items()
        }

    def get_comment_texts(self) -> list[str]:
        """Get all comment texts as a simple list."""
        return [c.body for c in self.all_comments]

    def get_high_score_comments(self, min_score: int = 10) -> list[CommentData]:
        """Get comments with score above threshold."""
        return [c for c in self.all_comments if c.score >= min_score]

    def get_subreddit_breakdown(self) -> dict[str, int]:
        """Get comment count breakdown by subreddit."""
        breakdown = defaultdict(int)
        for comment in self.all_comments:
            breakdown[comment.subreddit] += 1
        return dict(breakdown)

