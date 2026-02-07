"""
User Opinion Summarizer
----------------------

This module produces a **non-LLM** summary of what users are saying, by:
- extracting frequent keywords / bigrams
- grouping them into coarse "themes" via keyword dictionaries
- selecting representative quotes (verbatim) with minimal heuristics

It is intentionally simple, transparent, and deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict


_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^\w\s\u0600-\u06FF]+", re.UNICODE)  # keep Persian letters too
_WS_RE = re.compile(r"\s+")


EN_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "so", "to", "of", "in", "on", "for",
    "with", "as", "at", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "it", "this", "that", "these", "those", "i", "you", "we", "they", "he", "she", "them", "his",
    "her", "their", "our", "my", "your", "me", "us", "do", "does", "did", "not", "no", "yes",
    "will", "would", "can", "could", "should", "may", "might", "just", "very", "really",
}

FA_STOP = {
    "و", "یا", "اما", "اگر", "پس", "که", "را", "به", "از", "برای", "با", "در", "روی", "تا", "این",
    "اون", "آن", "هم", "من", "تو", "شما", "ما", "او", "ایشون", "ایشان", "ها", "های", "کرد", "کنه",
    "میشه", "می‌شود", "نمی", "نه", "بله", "بود", "هست", "نیست",
}

CORE_IRAN_KEYWORDS = [
    "iran", "iranian", "tehran", "islamic republic", "irgc", "revolutionary guard",
    "khamenei", "supreme leader", "natanz", "fordow", "arak", "persian gulf",
    "hormuz", "iranian regime", "jcpoa", "nuclear", "uranium", "iran-us", "us-iran",
]


THEMES: Dict[str, List[str]] = {
    # Conflict / military
    "military_action": ["strike", "attack", "bomb", "war", "invasion", "missile", "drone", "airstrike", "carrier", "centcom"],
    "diplomacy_talks": ["diplomacy", "talks", "deal", "agreement", "negotiation", "jcpoa", "oman", "vienna", "istanbul"],
    "nuclear_program": ["nuclear", "enrichment", "uranium", "centrifuge", "natanz", "fordow", "arak"],
    "sanctions_economy": ["sanction", "oil", "energy", "inflation", "currency", "rial", "economy", "market"],
    "protests_internal": ["protest", "uprising", "revolution", "woman", "hijab", "mahsa", "wlf", "crackdown"],
    "israel_region": ["israel", "idf", "hezbollah", "houthi", "yemen", "gulf", "hormuz", "saudi", "uae", "qatar", "oman", "turkey", "iraq"],
    "great_powers": ["china", "russia", "ukraine", "putin", "xi", "zelensky"],

    # Persian theme keywords (lightweight; matches are done on normalized lower text)
    "نظامی/درگیری": ["حمله", "جنگ", "موشک", "پهپاد", "بمباران", "ناو", "درگیری"],
    "مذاکره/دیپلماسی": ["مذاکره", "توافق", "دیپلماسی", "گفتگو", "گفت‌وگو", "میانجی", "عمان"],
    "هسته‌ای": ["هسته", "غنی", "اورانیوم", "فردو", "نطنز"],
    "اقتصاد/تحریم": ["تحریم", "نفت", "انرژی", "تورم", "ارز", "ریال", "اقتصاد", "بازار", "طلا", "بیتکوین", "بیت‌کوین"],
    "اعتراضات/داخل": ["اعتراض", "زن", "زندگی", "آزادی", "حجاب", "مهسا", "سرکوب"],
}


def _normalize(text: str) -> str:
    if not text:
        return ""
    t = _URL_RE.sub(" ", text)
    t = t.lower()
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def _tokenize(text: str) -> List[str]:
    t = _normalize(text)
    if not t:
        return []
    toks = [w for w in t.split(" ") if len(w) >= 3]
    # stopword removal (both lists)
    toks = [w for w in toks if (w not in EN_STOP and w not in FA_STOP)]
    return toks


def _is_relevant_to_iran(text: str) -> bool:
    norm = _normalize(text)
    if not norm:
        return False
    return any(kw in norm for kw in CORE_IRAN_KEYWORDS)


def _has_theme_keyword(text: str) -> bool:
    norm = _normalize(text)
    if not norm:
        return False
    for kws in THEMES.values():
        if any(kw in norm for kw in kws):
            return True
    return False


def _bigrams(tokens: List[str]) -> List[str]:
    if len(tokens) < 2:
        return []
    return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]


@dataclass
class ThemeSummary:
    theme: str
    count: int
    sample_quotes: List[Dict[str, Any]]

    def to_dict(self) -> dict:
        return asdict(self)


def summarize_user_opinions(
    comments: List[Dict[str, Any]],
    *,
    source_label: str,
    top_n_themes: int = 8,
    max_quotes_per_theme: int = 3,
    max_total_quotes: int = 20,
) -> Dict[str, Any]:
    """
    Build a deterministic, non-LLM summary for a comment corpus.

    Expected comment fields (best-effort):
      - text/body: str
      - author: str
      - subreddit: str (reddit)
      - likes: int (polymarket)
      - score: int (reddit, optional)
      - timestamp/created_utc/etc (optional)
    """
    # Extract raw texts
    rows: List[Dict[str, Any]] = []
    for c in comments or []:
        txt = c.get("text")
        if not isinstance(txt, str) or not txt.strip():
            txt = c.get("body")
        if not isinstance(txt, str) or not txt.strip():
            continue
        if source_label.lower() == "reddit":
            if not _is_relevant_to_iran(txt):
                continue
            if not _has_theme_keyword(txt):
                continue
        rows.append({
            "text": txt.strip(),
            "author": c.get("author", "unknown"),
            "subreddit": c.get("subreddit", ""),
            "likes": int(c.get("likes") or 0),
            "score": int(c.get("score") or 0) if str(c.get("score", "")).lstrip("-").isdigit() else 0,
            "timestamp": c.get("timestamp") or c.get("created_utc") or c.get("created") or "",
            "source": source_label,
        })

    # Token stats
    unigram = Counter()
    bigram = Counter()
    theme_hits = Counter()
    theme_to_quote_candidates: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for r in rows:
        toks = _tokenize(r["text"])
        unigram.update(toks)
        bigram.update(_bigrams(toks))

        norm = _normalize(r["text"])
        for theme, kws in THEMES.items():
            if any(kw in norm for kw in kws):
                theme_hits[theme] += 1
                theme_to_quote_candidates[theme].append(r)

    # Representative quotes heuristic: prefer (likes/score), then longer, then earlier
    def quote_rank(q: Dict[str, Any]) -> Tuple[int, int, int]:
        return (int(q.get("likes") or 0) + int(q.get("score") or 0), len(q.get("text") or ""), 1)

    # Build theme summaries
    theme_summaries: List[ThemeSummary] = []
    for theme, cnt in theme_hits.most_common(top_n_themes):
        cands = theme_to_quote_candidates.get(theme, [])
        cands_sorted = sorted(cands, key=quote_rank, reverse=True)
        # Deduplicate identical texts
        seen_text = set()
        quotes: List[Dict[str, Any]] = []
        for q in cands_sorted:
            t = q.get("text", "")
            key = t[:240]
            if key in seen_text:
                continue
            seen_text.add(key)
            quotes.append({
                "text": t,
                "author": q.get("author", "unknown"),
                "subreddit": q.get("subreddit", ""),
                "likes": q.get("likes", 0),
                "score": q.get("score", 0),
                "timestamp": q.get("timestamp", ""),
            })
            if len(quotes) >= max_quotes_per_theme:
                break

        theme_summaries.append(ThemeSummary(theme=theme, count=int(cnt), sample_quotes=quotes))

    # Global top quotes (most reacted)
    global_sorted = sorted(rows, key=quote_rank, reverse=True)
    global_quotes: List[Dict[str, Any]] = []
    seen_global = set()
    for q in global_sorted:
        t = q.get("text", "")
        key = t[:240]
        if key in seen_global:
            continue
        seen_global.add(key)
        global_quotes.append({
            "text": t,
            "author": q.get("author", "unknown"),
            "subreddit": q.get("subreddit", ""),
            "likes": q.get("likes", 0),
            "score": q.get("score", 0),
            "timestamp": q.get("timestamp", ""),
        })
        if len(global_quotes) >= max_total_quotes:
            break

    return {
        "source": source_label,
        "n_comments": len(rows),
        "top_unigrams": [{"term": k, "count": int(v)} for k, v in unigram.most_common(25)],
        "top_bigrams": [{"term": k, "count": int(v)} for k, v in bigram.most_common(25)],
        "themes": [t.to_dict() for t in theme_summaries],
        "top_quotes": global_quotes,
    }

