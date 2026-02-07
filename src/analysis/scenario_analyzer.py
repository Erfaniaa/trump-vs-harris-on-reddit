"""
Scenario Analyzer - Deep analysis of US-Iran conflict predictions.
Includes embedding-based semantic classification, pattern matching,
scenario analysis, timeline extraction, and reasoning generation.

Two-phase pipeline:
  Phase 1 — Fast regex matching (threaded, ~2-20s for 10k comments)
  Phase 2 — Sentence-embedding similarity via all-MiniLM-L6-v2 (~80 MB,
            ~500-1000 texts/sec on CPU) for comments that Phase 1 could
            not classify.  Replaces the previous facebook/bart-large-mnli
            zero-shot pipeline (~1.5 GB, ~0.1-0.2 texts/sec on CPU).
"""

import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
import statistics
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
import threading
import os

try:
    # Optional: non-LLM summarization of user opinions (themes + quotes)
    from src.analysis.user_opinion_summarizer import summarize_user_opinions
    _USER_OPINION_SUMMARY_AVAILABLE = True
except Exception:
    summarize_user_opinions = None  # type: ignore[assignment]
    _USER_OPINION_SUMMARY_AVAILABLE = False

try:
    from src.core.config import (
        ENABLE_INDIVIDUAL_HARM_ANALYSIS,
        ZERO_SHOT_MIN_TEXT_LENGTH,
        ZERO_SHOT_KEYWORDS,
        ZERO_SHOT_MAX_COMMENTS,
        ZERO_SHOT_MAX_WORKERS,
        CLASSIFICATION_MODEL,
        ANALYSIS_MAX_WORKERS,
        ANALYSIS_PROGRESS_SECONDS,
        ANALYSIS_PROGRESS_MIN_COUNT,
        IRAN_RELEVANCE_ANCHORS,
        IRAN_RELEVANT_SUBREDDITS,
    )
except Exception:
    ENABLE_INDIVIDUAL_HARM_ANALYSIS = False
    ZERO_SHOT_MIN_TEXT_LENGTH = 30
    ZERO_SHOT_KEYWORDS = []  # disabled; pre-filter ensures Iran relevance
    ZERO_SHOT_MAX_COMMENTS = 0  # unlimited; pre-filter limits to ~10K
    ZERO_SHOT_MAX_WORKERS = 1
    CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
    ANALYSIS_MAX_WORKERS = 14
    ANALYSIS_PROGRESS_SECONDS = 5
    ANALYSIS_PROGRESS_MIN_COUNT = 200
    IRAN_RELEVANCE_ANCHORS = [
        "iran", "iranian", "tehran", "persia", "persian",
        "khamenei", "pezeshkian", "araghchi", "raisi", "rouhani", "zarif",
        "soleimani", "ayatollah", "supreme leader",
        "irgc", "revolutionary guard", "quds force", "basij", "sepah",
        "jcpoa", "nuclear deal", "natanz", "fordow", "bushehr",
        "strait of hormuz", "hormuz", "bandar abbas", "persian gulf",
        "pahlavi", "reza pahlavi", "mek", "rajavi",
        "us-iran", "iran-us", "iran war", "iran attack", "iran strike",
        "attack iran", "strike iran", "bomb iran", "invade iran",
        "iran sanction", "iran negotiat", "iran deal", "iran diplomacy",
        "iran conflict", "iran military", "iran missile",
        "iran proxy", "iran nuclear", "iran regime",
        "witkoff",
    ]
    IRAN_RELEVANT_SUBREDDITS = {
        "iran", "iranian", "newiran", "iranpolitics", "proiran",
        "shiapolitics",
    }


_PROCESS_ANALYZER = None


def _init_process_analyzer(use_zero_shot: bool, use_gpu: bool, fast_mode: bool) -> None:
    """Initializer for multiprocessing workers (loads model per process)."""
    global _PROCESS_ANALYZER
    _PROCESS_ANALYZER = ScenarioAnalyzer(
        use_zero_shot=use_zero_shot,
        use_gpu=use_gpu,
        fast_mode=fast_mode
    )


def _process_batch_with_analyzer(batch: List[Tuple[int, dict]]):
    """Process a batch using the per-process analyzer."""
    if _PROCESS_ANALYZER is None:
        _init_process_analyzer(use_zero_shot=True, use_gpu=False, fast_mode=True)
    return _PROCESS_ANALYZER._analyze_comment_batch(batch)


@dataclass
class CommentAnalysis:
    """Analysis result for a single comment."""
    comment_id: str
    author: str
    subreddit: str
    prediction: int  # 1=attack, -1=no attack, 0=neutral
    confidence: float  # 0.0 to 1.0
    pattern_matches: List[str]
    scenario_matches: List[str]
    timeline_matches: List[str]
    zs_attack_score: float
    zs_no_attack_score: float
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuthorAnalysis:
    """Aggregated analysis for an author."""
    author: str
    total_comments: int
    prediction: int
    avg_confidence: float
    subreddits: List[str]
    scenarios_mentioned: List[str]
    timelines_mentioned: List[str]


@dataclass 
class ScenarioStats:
    """Statistics for a specific scenario."""
    name: str
    mention_count: int
    supporting_attack: int
    opposing_attack: int
    neutral: int
    sample_comments: List[str]


@dataclass
class ExtendedPredictions:
    """Extended predictions beyond just attack/no-attack."""
    # Assassination predictions
    khamenei_assassination_likely: int = 0
    khamenei_assassination_unlikely: int = 0
    
    # Regime change predictions
    regime_falls: int = 0
    regime_survives: int = 0
    
    # War scale predictions
    major_war: int = 0
    limited_conflict: int = 0
    
    # War duration predictions
    war_days: int = 0
    war_weeks: int = 0
    war_months: int = 0
    war_years: int = 0
    
    # Negotiation predictions
    deal_likely: int = 0
    deal_unlikely: int = 0
    
    # Future government predictions
    monarchy_return: int = 0
    secular_democracy: int = 0
    islamic_reform: int = 0
    military_rule: int = 0
    chaos: int = 0
    
    # Pahlavi predictions
    pahlavi_returns: int = 0
    pahlavi_unlikely: int = 0
    
    # Country comparison predictions (Iran's future resembles which country?)
    like_iraq: int = 0
    like_libya: int = 0
    like_syria: int = 0  # General Syria reference
    like_syria_civil_war: int = 0  # Assad-era civil war (2011-2024)
    like_syria_post_assad: int = 0  # Post-Assad HTS/Jolani era (2024+)
    like_afghanistan: int = 0
    like_egypt: int = 0
    like_tunisia: int = 0
    like_russia: int = 0
    like_yugoslavia: int = 0
    like_venezuela: int = 0
    like_north_korea: int = 0
    like_south_korea: int = 0
    like_1979_iran: int = 0
    
    # Elon Musk Iran-related mentions
    musk_starlink_iran: int = 0
    musk_diplomacy: int = 0
    musk_pro_war: int = 0
    musk_anti_war: int = 0
    
    # Epstein documents mentions (Israel/Iran connections)
    epstein_israel: int = 0
    epstein_iran_contra: int = 0
    epstein_documents: int = 0
    
    # Axios news mentions - detailed breakdown
    axios_mentions: int = 0
    axios_iran_strike: int = 0      # Axios reports about strikes
    axios_negotiations: int = 0     # Axios reports about talks/diplomacy
    axios_trump_iran: int = 0       # Axios reports about Trump + Iran
    axios_witkoff: int = 0          # Axios reports about Witkoff negotiations
    axios_military: int = 0         # Axios reports about military buildup
    axios_sample_reports: list = field(default_factory=list)  # Store sample report texts
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalysisResults:
    """Complete analysis results."""
    # Overall predictions
    total_comments_analyzed: int = 0
    total_authors_analyzed: int = 0
    
    # Vote counts
    predict_attack: int = 0
    predict_no_attack: int = 0
    neutral: int = 0
    
    # Confidence metrics
    avg_confidence: float = 0.0
    high_confidence_attack: int = 0
    high_confidence_no_attack: int = 0
    
    # Scenario breakdown
    scenario_stats: Dict[str, dict] = field(default_factory=dict)
    
    # Timeline breakdown - now with granular time periods
    timeline_stats: Dict[str, dict] = field(default_factory=dict)
    
    # Subreddit breakdown
    subreddit_stats: Dict[str, dict] = field(default_factory=dict)
    
    # Top comments
    top_attack_comments: List[dict] = field(default_factory=list)
    top_no_attack_comments: List[dict] = field(default_factory=list)
    
    # Detailed per-author results
    author_predictions: Dict[str, dict] = field(default_factory=dict)
    
    # Reasoning summary
    attack_reasons: List[str] = field(default_factory=list)
    no_attack_reasons: List[str] = field(default_factory=list)
    
    # Extended predictions
    extended_predictions: Dict = field(default_factory=dict)
    
    # Non-LLM user opinion summaries (themes + representative quotes)
    # Note: keep a simple list alias too for older report templates.
    user_opinion_summary: Dict[str, Any] = field(default_factory=dict)
    user_opinion_themes: List[str] = field(default_factory=list)
    
    # Metadata
    analyzed_at: str = ""
    analysis_duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)


class ScenarioAnalyzer:
    """
    Comprehensive analyzer for US-Iran conflict predictions.
    Uses multiple analysis methods for robust predictions.
    """
    
    # Zero-shot classification labels
    ZS_LABEL_ATTACK = "The United States will launch a military attack on Iran"
    ZS_LABEL_NO_ATTACK = "The United States will not attack Iran militarily"
    
    # Regex patterns for attack predictions
    ATTACK_PATTERNS = [
        # Strong predictions
        (r"\b(will|going to|gonna|about to|preparing to|planning to)\s+(attack|strike|bomb|invade)\b", 0.8),
        (r"\b(war|attack|strike|conflict|military action)\s+(is|seems?|looks?)\s+(inevitable|imminent|coming|certain|likely)\b", 0.9),
        (r"\b(expect|expecting|predict|predicting)\s+(a\s+)?(war|attack|strike|conflict)\b", 0.7),
        (r"\bit'?s?\s+(only\s+)?a\s+matter\s+of\s+time\b", 0.7),
        (r"\b(definitely|certainly|surely|undoubtedly)\s+(will|going to)\s+(attack|strike|bomb)\b", 0.9),
        (r"\bwar\s+is\s+(coming|inevitable|unavoidable)\b", 0.9),
        (r"\b(no\s+doubt|without\s+doubt).*?(attack|strike|war)\b", 0.8),
        (r"\bpreparing\s+(for\s+)?(war|attack|strike)\b", 0.6),
        (r"\b(escalat|escalt)\w*\s+(to|into)\s+(war|conflict)\b", 0.7),
        # Medium predictions (added)
        (r"\b(probably|likely)\s+(will|going to)\s+(attack|strike|bomb)\b", 0.6),
        (r"\b(think|believe|bet)\s+(they'?ll|we'?ll|us will|america will|trump will)\s+(attack|strike)\b", 0.6),
        (r"\b(high|good|strong)\s+(chance|probability|odds)\s+(of\s+)?(war|attack|strike)\b", 0.7),
        (r"\bwar\s+(is\s+)?(probable|likely|possible)\b", 0.5),
        (r"\b(betting|wagering)\s+on\s+(war|attack|strike)\b", 0.6),
        (r"\bstrike\s+(seems?|looks?)\s+(likely|probable|inevitable)\b", 0.7),
        (r"\b(can'?t|cannot)\s+(avoid|prevent)\s+(war|attack)\b", 0.7),
        (r"\b(headed|heading)\s+(for|toward|to)\s+(war|conflict)\b", 0.7),
        # Weak predictions (added)
        (r"\bmight\s+(actually\s+)?(attack|strike|bomb)\b", 0.4),
        (r"\bcould\s+(actually\s+)?(attack|strike|bomb)\b", 0.4),
        (r"\b(wouldn'?t be surprised|won'?t be surprised)\s+if.*(attack|strike|war)\b", 0.5),
        (r"\b(possible|plausible)\s+(that\s+)?(they|we|us|trump)\s+(attack|strike)\b", 0.4),
        # ---- Indirect hawkish patterns (no explicit prediction but lean attack) ----
        (r"\bsanctions?\s+(won'?t|will not|aren'?t|not)\s+(work|stop|deter|prevent)\b", 0.35),
        (r"\b(only|no)\s+(option|choice|way)\s+(left\s+)?(is|but)\s+(military|force|war|strike)\b", 0.6),
        (r"\btalks?\s+(will|going to|gonna)\s+(fail|collapse|break down)\b", 0.5),
        (r"\bdiplomacy\s+(is\s+)?(dead|over|failed|useless|pointless|futile)\b", 0.5),
        (r"\b(no\s+way|never)\s+(iran\s+)?(will\s+)?(agree|accept|comply|surrender|back\s+down)\b", 0.4),
        (r"\b(iran|they)\s+(won'?t|will\s+not|refuse|never)\s+(give\s+up|stop|abandon)\s+(nuk|nuclear|enrich)\w*\b", 0.4),
        (r"\b(carrier|fleet|troops|bombers?|b-?2|f-?15|f-?35|tomahawk)\s+(deploy|sent|heading|moving|ready)\b", 0.35),
        (r"\b(military\s+)?build.?up\b", 0.3),
        (r"\b(regime\s+change|topple\s+the\s+regime|overthrow)\b", 0.35),
        (r"\b(trump|us|america)\s+(wants?|needs?|determined|ready)\s+(to\s+)?(strike|attack|act|fight|hit)\b", 0.5),
        (r"\b(red\s+line|crossed|trigger|casus\s+belli|provocation)\b", 0.3),
        (r"\b(nuke|nuclear\s+weapon|breakout)\b.*\b(close|near|imminent|threshold)\b", 0.4),
        (r"\b(this\s+ends?\s+in|path\s+to|road\s+to|leads?\s+to)\s+(war|conflict|strike)\b", 0.5),
        (r"\b(last\s+chance|final\s+warning|ultimatum)\b", 0.35),
        (r"\b(iran\s+)?(provok|escalat)\w+\b", 0.25),
    ]
    
    # Regex patterns for no-attack predictions
    NO_ATTACK_PATTERNS = [
        # Strong predictions
        (r"\b(won'?t|will\s+not|not\s+going\s+to|never)\s+(attack|strike|bomb|invade)\b", 0.8),
        (r"\b(war|attack|strike)\s+(is|seems?|looks?)\s+(unlikely|improbable|doubtful)\b", 0.8),
        (r"\b(won'?t|will\s+not)\s+happen\b", 0.6),
        (r"\b(no\s+war|no\s+attack|no\s+strike)\b", 0.7),
        (r"\b(just|only|merely)\s+(bluff|bluffing|posturing|rhetoric|saber.?rattl)\b", 0.8),
        (r"\b(empty|hollow)\s+threat", 0.8),
        (r"\b(diplomatic|peaceful)\s+(solution|resolution|outcome)\b", 0.5),
        (r"\b(avoid|avert|prevent)\s+(war|attack|conflict)\b", 0.5),
        (r"\b(too\s+)?(costly|risky|dangerous)\s+(to\s+)?attack\b", 0.6),
        (r"\b(de-?escalat|backing\s+down|stand\s+down)\b", 0.6),
        # Medium predictions (added)
        (r"\b(probably|likely)\s+(won'?t|will\s+not)\s+(attack|strike|bomb)\b", 0.6),
        (r"\b(doubt|doubtful)\s+(they'?ll|there'?ll be|there will be).*(attack|war|strike)\b", 0.6),
        (r"\b(low|small|slim)\s+(chance|probability|odds)\s+(of\s+)?(war|attack|strike)\b", 0.7),
        (r"\bwar\s+(is\s+)?(unlikely|improbable|not going to happen)\b", 0.7),
        (r"\b(not\s+going\s+to|won'?t)\s+risk\s+(war|attack)\b", 0.6),
        (r"\bnegotiat(e|ion|ing)\s+(will|can|should)\s+(work|succeed|happen)\b", 0.5),
        (r"\b(deal|agreement)\s+(is|seems?)\s+(possible|likely|coming)\b", 0.5),
        # Weak predictions (added)
        (r"\bmight\s+not\s+(attack|strike|bomb)\b", 0.4),
        (r"\bprobably\s+(won'?t|not going to)\s+(attack|strike|bomb|happen)\b", 0.5),
        (r"\b(hope|hoping)\s+(no\s+war|they don'?t attack|for peace)\b", 0.3),
        (r"\b(overblown|exaggerated|hype)\b.*?(war|attack|threat)\b", 0.5),
        # ---- Indirect dovish patterns (lean no-attack) ----
        (r"\b(deal|agreement|compromise)\s+(is\s+)?(close|near|almost|in\s+reach)\b", 0.5),
        (r"\b(talks?|negotiation)\s+(progress|advancing|productive|positive|hopeful)\b", 0.45),
        (r"\b(witkoff|araghchi)\s+(meeting|talks?|progress|positive)\b", 0.4),
        (r"\b(iran|they)\s+(willing|ready|open)\s+to\s+(talk|negotiate|deal|compromise)\b", 0.4),
        (r"\b(cooler\s+heads|calmer|restraint|de-?escalat)\b", 0.35),
        (r"\b(nobody|no\s+one)\s+(wants?|benefits?\s+from)\s+(war|conflict|attack)\b", 0.45),
        (r"\b(war\s+is\s+)?(too\s+)?(expensive|costly|destructive|unpopular)\b", 0.3),
        (r"\b(sanctions?\s+)?(work|working|effective|biting|crippling)\b", 0.25),
        (r"\b(china|russia|eu|europe)\s+(won'?t|will\s+not)\s+(allow|let|support)\s+(attack|war|strike)\b", 0.4),
        (r"\b(diplomacy|dialogue|engagement)\s+(is\s+)?(the\s+)?(answer|way|path|key|solution)\b", 0.4),
        (r"\b(back\s*channel|secret\s+talks?|indirect\s+talks?)\b", 0.3),
        (r"\b(not\s+worth|don'?t\s+want|avoid)\s+(the\s+)?(risk|war|escalation|conflict)\b", 0.4),
        (r"\b(peace|peaceful)\s+(is\s+)?(still\s+)?(possible|achievable|likely)\b", 0.45),
        (r"\b(trump|us)\s+(doesn'?t|don'?t|does\s+not)\s+(want|need)\s+(war|conflict)\b", 0.5),
    ]
    
    # Scenario patterns
    SCENARIO_PATTERNS = {
        "nuclear_strike": [
            r"\b(nuclear|atomic)\s+(facility|site|plant|program)\b",
            r"\b(natanz|fordow|arak|bushehr|isfahan)\b",
            r"\b(enrichment|centrifuge|uranium)\b",
            r"\bstrike\s+(on\s+)?nuclear\b",
        ],
        "military_bases": [
            r"\b(military|irgc|revolutionary\s+guard)\s+(base|facility|site)\b",
            r"\b(missile|drone)\s+(base|site|facility)\b",
            r"\bquds\s+force\b",
        ],
        "leadership_targeted": [
            r"\b(decapitation|targeted)\s+(strike|killing|assassination)\b",
            r"\b(kill|assassinate|eliminate)\s+.*?(khamenei|leader)\b",
            r"\bregime\s+(change|decapitation)\b",
        ],
        "limited_strike": [
            r"\b(limited|surgical|precision|targeted|proportional)\s+(strike|attack|response)\b",
            r"\btit[- ]for[- ]tat\b",
            r"\b(measured|calibrated)\s+(response|strike)\b",
        ],
        "full_scale_war": [
            r"\b(full[- ]?scale|total|all[- ]?out)\s+(war|invasion|attack)\b",
            r"\b(ground\s+)?(troops|invasion|occupation)\b",
            r"\bregime\s+change\b",
        ],
        "proxy_conflict": [
            r"\bproxy\s+(war|conflict|attack)\b",
            r"\b(hezbollah|houthi|militia)\s+(attack|strike)\b",
            r"\bthrough\s+prox(y|ies)\b",
        ],
        "cyber_attack": [
            r"\bcyber\s+(attack|war|operation|strike)\b",
            r"\b(stuxnet|hack|digital\s+attack)\b",
        ],
    }
    
    # Timeline patterns - now with granular day/week/month breakdown
    TIMELINE_PATTERNS = {
        "today": [
            r"\btoday\b", r"\btonight\b", r"\bright\s+now\b",
            r"\bcurrently\b", r"\bas\s+we\s+speak\b",
        ],
        "tomorrow": [
            r"\btomorrow\b", r"\bnext\s+day\b", r"\bin\s+24\s+hours\b",
        ],
        "this_week": [
            r"\bthis\s+week\b", r"\bdays?\s+away\b", r"\bwithin\s+days\b",
            r"\bany\s+day\s+now\b", r"\bimminent\b",
        ],
        "next_week": [
            r"\bnext\s+week\b", r"\bin\s+a\s+week\b", r"\bwithin\s+a\s+week\b",
            r"\b7\s+days\b",
        ],
        "this_month": [
            r"\bthis\s+month\b", r"\bwithin\s+weeks\b", r"\bfebruary\b",
            r"\bcoming\s+weeks\b", r"\bsoon\b",
        ],
        "next_month": [
            r"\bnext\s+month\b", r"\bmarch\b", r"\bin\s+a\s+month\b",
            r"\bwithin\s+a\s+month\b",
        ],
        "this_quarter": [
            r"\bQ1\b", r"\bQ2\b", r"\bby\s+spring\b", r"\bby\s+summer\b",
            r"\bnext\s+few\s+months\b",
        ],
        "this_year": [
            r"\bthis\s+year\b", r"\b2026\b", r"\bby\s+end\s+of\s+year\b",
            r"\bby\s+december\b", r"\bwithin\s+months\b",
        ],
        "long_term": [
            r"\b(eventually|someday|years?|decade|long[- ]?term)\b",
            r"\bin\s+the\s+(distant\s+)?future\b", r"\b202[7-9]\b",
        ],
        "conditional": [
            r"\bif\s+(iran|they|trump|us|america|israel)\b",
            r"\b(when|unless|depends\s+on|contingent|should)\b",
            r"\bin\s+case\s+of\b",
        ],
    }
    
    # Extended prediction patterns - more flexible matching
    ASSASSINATION_PATTERNS = {
        "khamenei_targeted": [
            r"\b(kill|assassinate|eliminate|target)\s+khamenei\b",
            r"\bkhamenei\s+(will\s+be\s+)?(killed|dead|assassinated|eliminated)\b",
            r"\bdecapitat(e|ion)\s+(strike|regime)\b",
            r"\bsupreme\s+leader\s+(will\s+be\s+)?(killed|targeted|dead)\b",
            r"\bassassinat\w+\s+khamenei\b",
            r"\bkill\w*\s+the\s+(supreme\s+)?leader\b",
        ],
        "khamenei_survives": [
            r"\bkhamenei\s+(survives?|safe|protected)\b",
            r"\bwon'?t\s+(kill|target|assassinate)\s+khamenei\b",
            r"\bnot\s+target(ing)?\s+(khamenei|leader)\b",
            r"\bkhamenei\s+will\s+(survive|live)\b",
        ],
    }
    
    REGIME_CHANGE_PATTERNS = {
        "regime_falls": [
            r"\bregime\s+(will\s+)?(falls?|collapses?|ends?|toppled|overthrown|fall)\b",
            r"\b(revolution|uprising)\s+(will\s+)?succeeds?\b",
            r"\bislamic\s+republic\s+(will\s+)?(falls?|ends?|collapses?|fall)\b",
            r"\bgovernment\s+(will\s+)?(collapses?|falls?|overthrown|fall)\b",
            r"\bregime\s+change\b",
            r"\bthe\s+regime\s+will\s+fall\b",
            r"\bregime\s+is\s+(doomed|finished|over)\b",
        ],
        "regime_survives": [
            r"\bregime\s+(will\s+)?(survives?|endures?|holds?|stable|survive)\b",
            r"\bwon'?t\s+fall\b",
            r"\bcrackdown\s+(will\s+)?succeeds?\b",
            r"\bregime\s+(is\s+)?too\s+strong\b",
            r"\bregime\s+will\s+(survive|hold|endure)\b",
        ],
    }
    
    WAR_SCALE_PATTERNS = {
        "major_war": [
            r"\b(major|large\s*scale|full|massive|total|all\s*out)\s+war\b",
            r"\bregional\s+war\b",
            r"\bworld\s+war\b",
            r"\b(devastating|catastrophic)\s+(war|conflict)\b",
            r"\bfull\s*scale\s+(war|conflict|attack)\b",
            r"\bmassive\s+(attack|strike|war)\b",
        ],
        "limited_conflict": [
            r"\b(limited|small\s*scale|contained|surgical)\s+(war|conflict|strike)\b",
            r"\btit\s*for\s*tat\b",
            r"\b(restrained|measured)\s+(response|attack)\b",
            r"\blimited\s+(strike|attack|response)\b",
            r"\bsurgical\s+strike\b",
        ],
    }
    
    WAR_DURATION_PATTERNS = {
        "days": [
            r"\b(few|several|couple|2|3|4|5)\s+days?\b",
            r"\b(quick|rapid|swift)\s+war\b",
            r"\bover\s+in\s+days\b",
            r"\bdays?\s+of\s+(war|fighting|conflict)\b",
        ],
        "weeks": [
            r"\b(few|several|couple|2|3|4)\s+weeks?\b",
            r"\bmonth\s+or\s+so\b",
            r"\bweeks?\s+of\s+(fighting|conflict|war)\b",
            r"\blast\s+(a\s+)?few\s+weeks\b",
        ],
        "months": [
            r"\b(several|many|few|2|3|6)\s+months\b",
            r"\bprolonged\s+(war|conflict)\b",
            r"\bextended\s+(conflict|war)\b",
            r"\bmonths?\s+of\s+(fighting|war)\b",
        ],
        "years": [
            r"\b(several|many|2|3|5|10)\s+years\b",
            r"\blong\s+(war|conflict)\b",
            r"\bendless\s+(war|conflict)\b",
            r"\bquagmire\b",
            r"\byears?\s+of\s+(war|fighting)\b",
        ],
    }
    
    NEGOTIATION_PATTERNS = {
        "deal_likely": [
            r"\b(deal|agreement|compromise)\s+(will\s+be\s+)?(reached|made|possible|likely)\b",
            r"\btalks\s+(will\s+)?(succeed|work)\b",
            r"\bdiplomatic\s+(victory|solution|success)\b",
            r"\bbreakthrough\b",
            r"\bnegotiat\w+\s+(will\s+)?(succeed|work)\b",
            r"\bwill\s+(make|reach)\s+a\s+deal\b",
        ],
        "deal_unlikely": [
            r"\bno\s+(deal|agreement)\b",
            r"\btalks\s+(will\s+)?(fail|collapse)\b",
            r"\b(deadlock|impasse|breakdown)\b",
            r"\bwon'?t\s+negotiate\b",
            r"\bnegotiat\w+\s+(will\s+)?fail\b",
            r"\bno\s+chance\s+of\s+(a\s+)?deal\b",
        ],
    }
    
    FUTURE_GOVERNMENT_PATTERNS = {
        "monarchy_return": [
            r"\b(monarchy|pahlavi|shah)\s+(will\s+)?(return|restore|back|come\s+back)\b",
            r"\b(constitutional|new)\s+monarchy\b",
            r"\breza\s+pahlavi\s+(will\s+)?(leads?|returns?|king|become)\b",
            r"\bmonarchy\s+(will\s+)?be\s+restored\b",
            r"\bshahist\b",
        ],
        "secular_democracy": [
            r"\bsecular\s+(democracy|republic|government)\b",
            r"\bdemocratic\s+iran\b",
            r"\bfree\s+(and\s+fair\s+)?elections\b",
            r"\bliberal\s+democracy\b",
        ],
        "islamic_reform": [
            r"\b(reform|moderate)\s+(islam|government|regime)\b",
            r"\breformist\b",
            r"\bgradual\s+change\b",
            r"\bmoderate\s+iran\b",
        ],
        "military_rule": [
            r"\bmilitary\s+(government|rule|dictatorship|takeover)\b",
            r"\birgc\s+(takeover|rule|government)\b",
            r"\bjunta\b",
            r"\bgenerals?\s+(will\s+)?take\s+(over|control)\b",
        ],
        "chaos": [
            r"\bcivil\s+war\b",
            r"\bfailed\s+state\b",
            r"\b(chaos|anarchy|instability)\b",
            r"\bfragmentation\b",
            r"\bbalkaniz\w+\b",
        ],
    }
    
    PAHLAVI_PATTERNS = {
        "pahlavi_returns": [
            r"\bpahlavi\s+(will\s+)?(returns?|back|leads?|come\s+back|return)\b",
            r"\bshah\s+(will\s+)?returns?\b",
            r"\b(crown\s+prince|reza\s+pahlavi)\s+(will\s+)?(returns?|leads?|president|come\s+back)\b",
            r"\bpahlavi\s+will\s+return\b",
            r"\bpahlavi\s+(as|for)\s+(king|leader|president)\b",
        ],
        "pahlavi_unlikely": [
            r"\bpahlavi\s+(won'?t|never|unlikely|will\s+not)\b",
            r"\bno\s+monarchy\b",
            r"\breject\s+(monarchy|pahlavi)\b",
            r"\bpahlavi\s+(is\s+)?(irrelevant|exiled|out\s+of\s+touch)\b",
            r"\bdon'?t\s+want\s+(pahlavi|monarchy|shah)\b",
        ],
    }
    
    # Country comparison patterns - Iran's future resembles which country?
    COUNTRY_COMPARISON_PATTERNS = {
        "like_iraq": [
            r"\b(like|another|become|end\s+up\s+like)\s+iraq\b",
            r"\biraq\s+(2\.?0|scenario|all\s+over\s+again)\b",
            r"\b(saddam|de-?baathification)\b",
            r"\bpower\s+vacuum\s+(like\s+)?iraq\b",
            r"\bsectarian\s+(violence|conflict|war)\b",
        ],
        "like_libya": [
            r"\b(like|another|become|end\s+up\s+like)\s+libya\b",
            r"\blibya\s+(scenario|2\.?0|chaos)\b",
            r"\bgaddafi\b",
            r"\bfailed\s+state\b",
            r"\bwarlords?\s+(like\s+libya)?\b",
        ],
        "like_syria": [
            r"\b(like|another|become|end\s+up\s+like)\s+syria\b",
            r"\bsyria\s+(scenario|model)\b",
        ],
        "like_syria_civil_war": [
            r"\bsyria.{0,20}civil\s+war\b",
            r"\bcivil\s+war.{0,20}syria\b",
            r"\bassad\s+(era|regime|style|war)\b",
            r"\bunder\s+assad\b",
            r"\bassad.{0,20}(years|decade|long)\b",
            r"\bproxy\s+war\s+(like\s+syria)?\b",
            r"\bbalkaniz(e|ation)\b",
            r"\byears\s+of\s+(civil\s+)?war\b",
            r"\bbarrel\s+bombs?\b",
            r"\baleppo\b",
            r"\bidlib\b",
            r"\bchemical\s+(weapons?|attack)\b",
            r"\bisis\s+(syria|territory)\b",
            r"\bdecade.{0,10}(war|conflict)\b",
            r"\bprolonged\s+(civil\s+)?war\b",
            r"\bmillion\s+refugees?\b",
            r"\bsyria.{0,20}(years|decade|long)\b",
            r"\b(years|decade).{0,10}like\s+syria\b",
        ],
        "like_syria_post_assad": [
            r"\bjol[aou]+ni\b",  # jolani, joulani, julani, jolaani
            r"\bhts\b",
            r"\bhay'?at\s+tahrir\b",
            r"\bpost[\s-]?assad\b",
            r"\bafter\s+assad\b",
            r"\bnew\s+syria\b",
            r"\bsyria\s+(transition|now|today|2024|2025|2026)\b",
            r"\bislamist\s+(takeover|government|rule)\b",
            r"\brebel\s+(victory|takeover|government)\b",
            r"\bdamascus\s+(fell|fall|falls)\b",
            r"\bquick\s+collapse\b",
            r"\bturkey[\s-]?backed\b",
            r"\bsyria.{0,30}collapse\b",
            r"\bcollapse.{0,30}syria\b",
            r"\bassad.{0,20}(fall|fell|collapse|end|gone|flee)\b",
            r"\b(fall|fell|collapse).{0,20}assad\b",
            r"\bcollapse\s+like\s+assad\b",
            r"\bquick.{0,15}(fall|collapse|end)\b",
        ],
        "like_afghanistan": [
            r"\b(like|another|become|end\s+up\s+like)\s+afghanistan\b",
            r"\bafghan\s+(scenario|quagmire)\b",
            r"\btaliban\s+(takes?\s+over|returns?|scenario)\b",
            r"\b20\s+years?\s+(war|occupation)\b",
            r"\bgraveyard\s+of\s+empires\b",
            r"\bendless\s+war\b",
        ],
        "like_egypt": [
            r"\b(like|another|become|end\s+up\s+like)\s+egypt\b",
            r"\begypt\s+(scenario|model)\b",
            r"\bmilitary\s+coup\b",
            r"\bsisi\s+(model|style)\b",
            r"\btahrir\b",
            r"\bbrief\s+democracy\b",
        ],
        "like_tunisia": [
            r"\b(like|another|become)\s+tunisia\b",
            r"\btunisia\s+(scenario|model|success)\b",
            r"\bsuccessful\s+(transition|democracy)\b",
            r"\barab\s+spring\s+success\b",
        ],
        "like_russia": [
            r"\b(like|another|become|end\s+up\s+like)\s+russia\b",
            r"\brussia\s+(scenario|model)\b",
            r"\bputin\s+(model|style)\b",
            r"\bsecurity\s+state\b",
            r"\birgc\s+(takes?\s+over|becomes?\s+government)\b",
            r"\bauthoritarian\s+stability\b",
        ],
        "like_yugoslavia": [
            r"\b(like|another|become|end\s+up\s+like)\s+yugoslavia\b",
            r"\byugoslavia\s+(scenario|breakup)\b",
            r"\bbalkaniz(e|ation)\s+(of\s+)?iran\b",
            r"\bbreak\s+up\s+iran\b",
            r"\b(kurds?|azeris?|baloch)\s+separat(e|ism|ist)\b",
            r"\bethnic\s+(conflict|cleansing)\b",
        ],
        "like_venezuela": [
            r"\b(like|another|become|end\s+up\s+like)\s+venezuela\b",
            r"\bvenezuela\s+(scenario|model)\b",
            r"\bmaduro\s+(style|model)\b",
            r"\beconomic\s+collapse\s+(but\s+)?regime\s+survives?\b",
            r"\bhyperinflation\s+(like\s+venezuela)?\b",
        ],
        "like_north_korea": [
            r"\b(like|another|become|end\s+up\s+like)\s+north\s+korea\b",
            r"\bnorth\s+korea\s+(scenario|model)\b",
            r"\bhermit\s+kingdom\b",
            r"\btotal\s+isolation\b",
            r"\bnuclear\s+blackmail\b",
        ],
        "like_south_korea": [
            r"\b(like|another|become)\s+south\s+korea\b",
            r"\bsouth\s+korea\s+(scenario|model|miracle)\b",
            r"\bkorean\s+miracle\b",
            r"\b(asian\s+tiger|economic\s+miracle)\b",
            r"\bsuccessful\s+(development|modernization)\b",
        ],
        "like_1979_iran": [
            r"\b1979\s+(again|repeats?|all\s+over)\b",
            r"\brevolution\s+repeats?\b",
            r"\bshah\s+falls?\s+again\b",
            r"\bhistory\s+repeats?\b",
            r"\bcycle\s+of\s+revolution\b",
            r"\banother\s+(islamic\s+)?revolution\b",
        ],
    }
    
    # Elon Musk & Starlink patterns (Iran-related)
    MUSK_IRAN_PATTERNS = {
        "musk_starlink_iran": [
            r"\b(starlink|musk|elon)\s+(iran|iranian|tehran)\b",
            r"\b(iran|iranian)\s+(starlink|musk|elon)\b",
            r"\bstarlink\s+(protest|blackout|internet)\b",
            r"\brestore\s+internet\s+iran\b",
            r"\bspacex\s+iran\b",
        ],
        "musk_diplomacy": [
            r"\bmusk\s+(ambassador|diplomat|talks|negotiate|channel)\b",
            r"\bmusk\s+iravani\b",
            r"\belon\s+(backchannel|diplomat)\b",
            r"\bmusk\s+defuse\b",
        ],
        "musk_pro_war": [
            r"\bmusk\s+(attack|strike|bomb|war)\s+iran\b",
            r"\bmusk\s+support(s)?\s+(strike|attack|war)\b",
        ],
        "musk_anti_war": [
            r"\bmusk\s+(peace|against\s+war|diplomacy|negotiate)\b",
            r"\bmusk\s+de-?escalat\b",
        ],
    }
    
    # Epstein documents patterns (Israel/Iran connections)
    EPSTEIN_PATTERNS = {
        "epstein_israel": [
            r"\bepstein\s+(israel|israeli|mossad|barak|netanyahu)\b",
            r"\b(israel|mossad|barak)\s+epstein\b",
            r"\behud\s+barak\s+epstein\b",
        ],
        "epstein_iran_contra": [
            r"\bepstein\s+(iran.?contra|arms|weapons|cia)\b",
            r"\bepstein\s+khashoggi\b",
            r"\bepstein\s+smuggling\b",
        ],
        "epstein_documents": [
            r"\bepstein\s+(files?|documents?|papers?|list|leak|release)\b",
            r"\bepstein\s+(unsealed|names|kompromat)\b",
        ],
    }
    
    # Axios news patterns - detailed categorization
    AXIOS_PATTERNS = {
        "general": [
            r"\baxios\s+(report|scoop|breaking|exclusive|says)\b",
            r"\baccording\s+to\s+axios\b",
            r"\baxios\s+reported\b",
            r"\baxios\s+sources\b",
        ],
        "iran_strike": [
            r"\baxios.{0,50}(strike|attack|bomb|military action).{0,30}iran\b",
            r"\baxios.{0,50}iran.{0,30}(strike|attack|bomb)\b",
            r"\baxios.{0,30}(airstrike|air strike|missile)\b",
        ],
        "negotiations": [
            r"\baxios.{0,50}(talk|negotiat|diplom|deal|agreement)\b",
            r"\baxios.{0,50}(istanbul|vienna|doha|oman)\b",
            r"\baxios.{0,50}(nuclear deal|jcpoa|nuclear agreement)\b",
        ],
        "trump_iran": [
            r"\baxios.{0,30}trump.{0,30}iran\b",
            r"\baxios.{0,30}iran.{0,30}trump\b",
            r"\baxios.{0,30}(president|white house).{0,30}iran\b",
        ],
        "witkoff": [
            r"\baxios.{0,50}witkoff\b",
            r"\bwitkoff.{0,50}axios\b",
            r"\baxios.{0,50}(envoy|negotiator|emissary)\b",
        ],
        "military": [
            r"\baxios.{0,50}(carrier|pentagon|military|defense)\b",
            r"\baxios.{0,50}(abraham lincoln|troops|deployment)\b",
            r"\baxios.{0,50}(centcom|irgc|revolutionary guard)\b",
        ],
    }

    def __init__(self, use_zero_shot: bool = True, use_gpu: bool = False, fast_mode: bool = True):
        """
        Initialize the analyzer.
        
        Args:
            use_zero_shot: Whether to use zero-shot classification model
            use_gpu: Whether to use GPU for inference
            fast_mode: Skip less important patterns for speed (default: True)
        """
        self.use_zero_shot = use_zero_shot
        self.use_gpu = use_gpu
        self.fast_mode = fast_mode
        self._zero_shot_max_comments = int(ZERO_SHOT_MAX_COMMENTS) if ZERO_SHOT_MAX_COMMENTS else 0
        self._zero_shot_used = 0
        # Safety default: do not analyze/score assassination or individual-death outcomes.
        self.enable_individual_harm_analysis = bool(ENABLE_INDIVIDUAL_HARM_ANALYSIS)
        self.classifier = None
        
        # Pre-compile all regex patterns for speed
        self._compile_patterns()
        
        if use_zero_shot:
            self._load_classifier()
    
    def _compile_patterns(self):
        """Pre-compile all regex patterns for faster matching."""
        # Compile attack patterns
        self._compiled_attack = [(re.compile(p, re.IGNORECASE), w) for p, w in self.ATTACK_PATTERNS]
        self._compiled_no_attack = [(re.compile(p, re.IGNORECASE), w) for p, w in self.NO_ATTACK_PATTERNS]
        
        # Compile scenario patterns - also create combined single patterns for fast screening
        self._compiled_scenarios = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.SCENARIO_PATTERNS.items()
        }
        # Combined pattern for quick screening
        all_scenario_patterns = [p for patterns in self.SCENARIO_PATTERNS.values() for p in patterns]
        self._scenario_quick_check = re.compile('|'.join(all_scenario_patterns[:20]), re.IGNORECASE)
        
        # Compile timeline patterns - combined for speed
        self._compiled_timelines = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.TIMELINE_PATTERNS.items()
        }
        # Combined pattern for quick screening
        all_timeline_patterns = [p for patterns in self.TIMELINE_PATTERNS.values() for p in patterns]
        self._timeline_quick_check = re.compile('|'.join(all_timeline_patterns[:30]), re.IGNORECASE)
        
        # Compile extended prediction patterns - with combined versions
        # Safety: assassination/individual-harm patterns are disabled by default.
        self._compiled_assassination = {}
        if self.enable_individual_harm_analysis:
            self._compiled_assassination = {
                k: [re.compile(p, re.IGNORECASE) for p in v]
                for k, v in self.ASSASSINATION_PATTERNS.items()
            }
        self._compiled_regime = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.REGIME_CHANGE_PATTERNS.items()
        }
        self._compiled_war_scale = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.WAR_SCALE_PATTERNS.items()
        }
        self._compiled_war_duration = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.WAR_DURATION_PATTERNS.items()
        }
        self._compiled_negotiation = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.NEGOTIATION_PATTERNS.items()
        }
        self._compiled_future_gov = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.FUTURE_GOVERNMENT_PATTERNS.items()
        }
        self._compiled_pahlavi = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.PAHLAVI_PATTERNS.items()
        }
        self._compiled_country = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.COUNTRY_COMPARISON_PATTERNS.items()
        }
        self._compiled_musk = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.MUSK_IRAN_PATTERNS.items()
        }
        self._compiled_epstein = {
            k: [re.compile(p, re.IGNORECASE) for p in v]
            for k, v in self.EPSTEIN_PATTERNS.items()
        }
        self._compiled_axios = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in self.AXIOS_PATTERNS.items()
        }
        
        # Create keyword sets for faster pre-filtering
        self._scenario_keywords = frozenset(['nuclear', 'military', 'base', 'strike', 'drone', 'missile', 
                                             'quds', 'leadership', 'limited', 'surgical', 'full', 'scale', 
                                             'war', 'invasion', 'proxy', 'hezbollah', 'houthi', 'cyber'])
        self._timeline_keywords = frozenset(['today', 'tonight', 'tomorrow', 'week', 'month', 'year',
                                              'soon', 'imminent', 'day', 'february', 'march', 'spring',
                                              'summer', 'eventually', 'Q1', 'Q2', '2026', '2027'])
    
    # ---- Reference sentences for embedding-based classification ----
    _ATTACK_REFS = [
        "The US will launch military strikes against Iran",
        "War between America and Iran is coming",
        "Military action against Iran is imminent",
        "Iran will be attacked and bombed by the United States",
        "Trump will order strikes on Iran",
        "The US military will attack Iran's nuclear facilities",
        "Armed conflict with Iran is inevitable",
        "Iran is about to be struck militarily by America",
        "Bombing Iran is the only option left",
        "US forces are preparing to strike Iran",
    ]
    _NO_ATTACK_REFS = [
        "The US will not attack Iran",
        "There will be no war with Iran",
        "Diplomacy will prevent conflict with Iran",
        "US-Iran tensions will de-escalate peacefully",
        "America will negotiate with Iran instead of war",
        "Military action against Iran is very unlikely",
        "Peace between the US and Iran is achievable",
        "Iran will not be attacked by the United States",
        "Diplomatic talks will resolve the Iran crisis",
        "There is no chance of a US military strike on Iran",
    ]
    _EMB_TEMPERATURE = 5.0  # softmax temperature for similarity → probability

    def _load_classifier(self):
        """Load a lightweight sentence-embedding model for fast semantic classification.

        Uses ``sentence-transformers/all-MiniLM-L6-v2`` (~80 MB) instead of the
        previous ``facebook/bart-large-mnli`` (~1.5 GB zero-shot pipeline).
        Embedding + cosine-similarity is ~500-1000× faster than NLI zero-shot on
        CPU because it needs only **one** forward pass per text rather than one
        per text × label pair.
        """
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel

            print("📦 Loading semantic embedding model (~80 MB)...", flush=True)
            print("   (First run will download the model)", flush=True)

            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self._embed_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._embed_model = AutoModel.from_pretrained(model_name)
            self._embed_model.eval()

            # Device selection
            if self.use_gpu and torch.cuda.is_available():
                self._embed_device = "cuda"
                self._embed_model = self._embed_model.cuda()
                print("   🚀 Using GPU for embeddings", flush=True)
            else:
                self._embed_device = "cpu"

            # Pre-compute class centroids from reference sentences
            attack_embs = self._encode_texts(self._ATTACK_REFS)
            no_attack_embs = self._encode_texts(self._NO_ATTACK_REFS)

            self._attack_centroid = attack_embs.mean(dim=0)
            self._attack_centroid = self._attack_centroid / self._attack_centroid.norm()
            self._no_attack_centroid = no_attack_embs.mean(dim=0)
            self._no_attack_centroid = self._no_attack_centroid / self._no_attack_centroid.norm()

            # Set classifier flag so Phase-2 check succeeds
            self.classifier = True

            print("   ✅ Embedding model loaded successfully!", flush=True)
        except Exception as e:
            print(f"   ⚠️ Could not load embedding model: {e}", flush=True)
            print("   Falling back to pattern-only analysis", flush=True)
            self.classifier = None
            self.use_zero_shot = False

    # ---- Batched text encoding ----
    def _encode_texts(self, texts: list, batch_size: int = 256) -> "torch.Tensor":
        """Encode *texts* to L2-normalised embeddings using the sentence model.

        Returns a ``torch.Tensor`` of shape ``(len(texts), hidden_dim)``.
        """
        import torch

        all_embs: list = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = self._embed_tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            if self._embed_device == "cuda":
                encoded = {k: v.cuda() for k, v in encoded.items()}

            with torch.no_grad():
                outputs = self._embed_model(**encoded)

            # Mean-pooling over token embeddings (ignoring padding tokens)
            attention_mask = encoded["attention_mask"]
            token_embs = outputs.last_hidden_state  # (B, T, D)
            mask = attention_mask.unsqueeze(-1).expand(token_embs.size()).float()
            sum_embs = (token_embs * mask).sum(dim=1)
            counts = mask.sum(dim=1).clamp(min=1e-9)
            embeddings = sum_embs / counts

            # L2-normalise so dot-product == cosine similarity
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            all_embs.append(embeddings.cpu())

        return torch.cat(all_embs, dim=0)

    # Keywords for quick filtering before expensive regex
    _attack_keywords = frozenset([
        'attack', 'strike', 'bomb', 'war', 'invade', 'inevitable',
        'coming', 'imminent', 'will', 'going', 'certainly',
        'definitely', 'escalat', 'preparing', 'doubt',
        # indirect hawkish
        'sanction', 'option', 'fail', 'dead', 'refuse', 'carrier',
        'deploy', 'build', 'regime', 'trump', 'red line', 'trigger',
        'breakout', 'nuke', 'ultimatum', 'provok', 'path', 'leads',
    ])
    _no_attack_keywords = frozenset([
        'won', 'not', 'never', 'unlikely', 'bluff', 'posturing',
        'diplomatic', 'peaceful', 'avoid', 'escalat', 'doubt',
        'empty', 'hollow', 'deal', 'negotiat',
        # indirect dovish
        'close', 'progress', 'positive', 'willing', 'ready',
        'cooler', 'restraint', 'expensive', 'costly', 'working',
        'allow', 'dialogue', 'channel', 'peace', 'worth', 'want',
    ])
    
    def _match_patterns_compiled(self, text: str, compiled_patterns: list, 
                                  keywords: frozenset = None) -> Tuple[float, List[str]]:
        """
        Match pre-compiled patterns against text (optimized).
        
        Returns:
            Tuple of (total_score, list_of_matched_patterns)
        """
        # Quick keyword pre-filter
        if keywords:
            text_lower = text.lower()
            if not any(kw in text_lower for kw in keywords):
                return 0.0, []
        
        total_score = 0.0
        matches = []
        
        for compiled_re, weight in compiled_patterns:
            if compiled_re.search(text):
                total_score += weight
                matches.append(compiled_re.pattern)
        
        return total_score, matches

    def _detect_scenarios(self, text: str) -> List[str]:
        """Detect which conflict scenarios are mentioned in text (optimized)."""
        # Quick pre-check - skip detailed analysis if no relevant content
        text_lower = text.lower()
        if not any(kw in text_lower for kw in self._scenario_keywords):
            return []
        
        detected = []
        for scenario, compiled_patterns in self._compiled_scenarios.items():
            for compiled_re in compiled_patterns:
                if compiled_re.search(text):
                    detected.append(scenario)
                    break
        
        return detected

    def _detect_timelines(self, text: str) -> List[str]:
        """Detect timeline mentions in text (optimized)."""
        # Quick pre-check - skip detailed analysis if no relevant content
        text_lower = text.lower()
        if not any(kw in text_lower for kw in self._timeline_keywords):
            return []
        
        detected = []
        for timeline, compiled_patterns in self._compiled_timelines.items():
            for compiled_re in compiled_patterns:
                if compiled_re.search(text):
                    detected.append(timeline)
                    break
        
        return detected
    
    # Pre-computed keyword sets for fast filtering in extended predictions
    _EXT_KEYWORDS = {
        'assassination': frozenset(['khamenei', 'leader', 'assassin', 'kill', 'supreme']),
        'regime': frozenset(['regime', 'fall', 'collapse', 'overthrow', 'survive']),
        'war_scale': frozenset(['war', 'conflict', 'strike', 'attack', 'invasion', 'limited', 'full']),
        'war_duration': frozenset(['day', 'week', 'month', 'year', 'long', 'quick', 'brief']),
        'negotiation': frozenset(['deal', 'negotiat', 'talk', 'diplomacy', 'agreement']),
        'future_gov': frozenset(['government', 'democracy', 'monarchy', 'military', 'chaos', 'reform']),
        'pahlavi': frozenset(['pahlavi', 'shah', 'crown', 'monarchy', 'reza']),
        'country': frozenset(['iraq', 'libya', 'syria', 'afghan', 'balkaniz', 'civil', 'failed', 
                             'yugoslavia', 'venezuela', 'korea', 'jolani', 'joulani', 'hts', 
                             'assad', 'collapse', 'aleppo', 'idlib', 'damascus', 'egypt', 'tunisia']),
    }
    
    def _detect_extended_predictions(self, text: str) -> Dict[str, List[str]]:
        """Detect extended predictions using pre-compiled patterns (optimized)."""
        detected = {
            "assassination": [],
            "regime_change": [],
            "war_scale": [],
            "war_duration": [],
            "negotiation": [],
            "future_government": [],
            "pahlavi": [],
            "country_comparison": [],
            "musk_iran": [],
            "epstein": [],
            "axios": [],
        }
        
        # Quick keyword pre-filter for speed (single lowercase pass)
        text_lower = text.lower()
        words_in_text = set(text_lower.split())  # Quick word extraction
        
        # Check each category with set intersection (faster than any())
        if self.enable_individual_harm_analysis and self._compiled_assassination:
            if words_in_text & self._EXT_KEYWORDS['assassination']:
                for key, compiled_patterns in self._compiled_assassination.items():
                    for compiled_re in compiled_patterns:
                        if compiled_re.search(text):
                            detected["assassination"].append(key)
                            break
        
        if words_in_text & self._EXT_KEYWORDS['regime']:
            for key, compiled_patterns in self._compiled_regime.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["regime_change"].append(key)
                        break
        
        if words_in_text & self._EXT_KEYWORDS['war_scale']:
            for key, compiled_patterns in self._compiled_war_scale.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["war_scale"].append(key)
                        break
        
        if words_in_text & self._EXT_KEYWORDS['war_duration']:
            for key, compiled_patterns in self._compiled_war_duration.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["war_duration"].append(key)
                        break
        
        if words_in_text & self._EXT_KEYWORDS['negotiation']:
            for key, compiled_patterns in self._compiled_negotiation.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["negotiation"].append(key)
                        break
        
        if words_in_text & self._EXT_KEYWORDS['future_gov']:
            for key, compiled_patterns in self._compiled_future_gov.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["future_government"].append(key)
                        break
        
        if words_in_text & self._EXT_KEYWORDS['pahlavi']:
            for key, compiled_patterns in self._compiled_pahlavi.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["pahlavi"].append(key)
                        break
        
        # Country comparisons
        if words_in_text & self._EXT_KEYWORDS['country']:
            for key, compiled_patterns in self._compiled_country.items():
                for compiled_re in compiled_patterns:
                    if compiled_re.search(text):
                        detected["country_comparison"].append(key)
                        break
        
        # Skip less important patterns in fast mode
        if not self.fast_mode:
            if any(w in text_lower for w in ['musk', 'elon', 'starlink', 'spacex']):
                for key, compiled_patterns in self._compiled_musk.items():
                    for compiled_re in compiled_patterns:
                        if compiled_re.search(text):
                            detected["musk_iran"].append(key)
                            break
            
            if any(w in text_lower for w in ['epstein', 'barak', 'kompromat']):
                for key, compiled_patterns in self._compiled_epstein.items():
                    for compiled_re in compiled_patterns:
                        if compiled_re.search(text):
                            detected["epstein"].append(key)
                            break
            
            if 'axios' in text_lower:
                axios_cats = []
                for cat, compiled_list in self._compiled_axios.items():
                    for compiled_re in compiled_list:
                        if compiled_re.search(text):
                            axios_cats.append(cat)
                            break
                detected["axios"] = axios_cats if axios_cats else ["general"]
                # Store sample text for report (first 200 chars)
                detected["axios_sample"] = text[:200] if len(text) > 200 else text
        else:
            # In fast mode, just do simple keyword checks
            if 'starlink' in text_lower or ('musk' in text_lower and 'iran' in text_lower):
                detected["musk_iran"].append("musk_starlink_iran")
            if 'epstein' in text_lower:
                detected["epstein"].append("epstein_documents")
            if 'axios' in text_lower:
                detected["axios"] = ["general"]
                detected["axios_sample"] = text[:200] if len(text) > 200 else text
        
        return detected

    def _zero_shot_classify(self, text: str) -> Tuple[float, float]:
        """Classify a single text using embedding similarity.

        Returns:
            Tuple of (attack_score, no_attack_score) in [0, 1].
        """
        if not self.classifier:
            return 0.0, 0.0

        try:
            import torch
            text = text[:512] if len(text) > 512 else text
            emb = self._encode_texts([text])  # (1, D)
            sim_a = float(torch.dot(emb[0], self._attack_centroid))
            sim_n = float(torch.dot(emb[0], self._no_attack_centroid))
            # Softmax with temperature → probability
            import math
            mx = max(sim_a, sim_n)
            ea = math.exp((sim_a - mx) * self._EMB_TEMPERATURE)
            en = math.exp((sim_n - mx) * self._EMB_TEMPERATURE)
            s = ea + en
            return ea / s, en / s
        except Exception:
            return 0.0, 0.0

    def _is_zero_shot_candidate(self, text: str, attack_score: float, no_attack_score: float) -> bool:
        """Decide whether to run zero-shot for this text.

        Since the pre-filter already ensures every comment is Iran-relevant,
        we run zero-shot on ALL comments that meet the minimum length.
        The old keyword gate and "weak/ambiguous pattern only" logic are removed
        — they were the main reason 99% of Iran-relevant comments ended up
        classified as neutral (no pattern hit → no zero-shot → score 0/0 → neutral).
        """
        if not self.use_zero_shot or not self.classifier:
            return False
        if self._zero_shot_max_comments and self._zero_shot_used >= self._zero_shot_max_comments:
            return False
        if len(text) < ZERO_SHOT_MIN_TEXT_LENGTH:
            return False
        # No keyword gate — pre-filter already ensures Iran relevance.
        # No weak/ambiguous gate — we WANT zero-shot on every Iran comment.
        return True

    def analyze_comment(self, text: str, comment_id: str = "", 
                       author: str = "", subreddit: str = "") -> CommentAnalysis:
        """
        Analyze a single comment for prediction stance.

        Scoring hierarchy (revised for higher yield):
        1. Regex patterns → attack_score, no_attack_score (fast, high precision)
        2. Zero-shot BART-MNLI → zs_attack, zs_no_attack (slower, broader recall)
        3. Combine:
           - If regex gives strong signal (>= 0.5), trust it (2× weight).
           - Zero-shot ALWAYS contributes (1× weight).
           - Final decision uses a LOW margin (0.03) so that even a slight
             lean from the classifier counts as an opinion.
        """
        # Pattern matching (fast)
        attack_score, attack_matches = self._match_patterns_compiled(
            text, self._compiled_attack, self._attack_keywords)
        no_attack_score, no_attack_matches = self._match_patterns_compiled(
            text, self._compiled_no_attack, self._no_attack_keywords)
        
        # Scenario and timeline detection
        scenarios = self._detect_scenarios(text)
        timelines = self._detect_timelines(text)
        
        # Zero-shot classification — runs on ALL pre-filtered comments
        zs_attack, zs_no_attack = 0.0, 0.0
        if self._is_zero_shot_candidate(text, attack_score, no_attack_score):
            zs_attack, zs_no_attack = self._zero_shot_classify(text)
            self._zero_shot_used += 1
        
        # ---- Combine scores ----
        # Regex patterns are high-precision but low-recall → 2× weight
        # Zero-shot is broader but noisier → 1× weight
        # When BOTH agree, confidence is high.
        total_attack = (attack_score * 2.0) + zs_attack
        total_no_attack = (no_attack_score * 2.0) + zs_no_attack

        # ---- Decision logic (3 tiers) ----
        # Tier 1: Clear signal (pattern OR strong zero-shot)
        if total_attack > total_no_attack + 0.08:
            prediction = 1
            confidence = min(total_attack / (total_attack + total_no_attack + 0.01), 1.0)
        elif total_no_attack > total_attack + 0.08:
            prediction = -1
            confidence = min(total_no_attack / (total_attack + total_no_attack + 0.01), 1.0)
        # Tier 2: Modest lean — zero-shot alone has a detectable lean (> 0.55)
        elif zs_attack > 0.55 and zs_attack > zs_no_attack + 0.05:
            prediction = 1
            confidence = min(zs_attack, 0.65)
        elif zs_no_attack > 0.55 and zs_no_attack > zs_attack + 0.05:
            prediction = -1
            confidence = min(zs_no_attack, 0.65)
        # Tier 3: Weak lean — any consistent signal above noise floor
        elif total_attack > 0.10 and total_attack > total_no_attack + 0.02:
            prediction = 1
            confidence = min(total_attack / (total_attack + total_no_attack + 0.01), 0.55)
        elif total_no_attack > 0.10 and total_no_attack > total_attack + 0.02:
            prediction = -1
            confidence = min(total_no_attack / (total_attack + total_no_attack + 0.01), 0.55)
        else:
            prediction = 0
            confidence = 0.0
        
        return CommentAnalysis(
            comment_id=comment_id,
            author=author,
            subreddit=subreddit,
            prediction=prediction,
            confidence=confidence,
            pattern_matches=attack_matches + no_attack_matches,
            scenario_matches=scenarios,
            timeline_matches=timelines,
            zs_attack_score=zs_attack,
            zs_no_attack_score=zs_no_attack
        )
    
    def analyze_extended_predictions(self, text: str) -> Dict:
        """Analyze a comment for extended predictions."""
        return self._detect_extended_predictions(text)
    
    def _analyze_single_comment_fast(self, comment: dict, index: int) -> Tuple[int, 'CommentAnalysis', Dict]:
        """Analyze a single comment and return results (for batch processing)."""
        text = comment.get('body', '')
        
        analysis = self.analyze_comment(
            text=text,
            comment_id=comment.get('comment_id', str(index)),
            author=comment.get('author', 'unknown'),
            subreddit=comment.get('subreddit', 'unknown')
        )
        
        ext_pred = self._detect_extended_predictions(text)
        
        return index, analysis, ext_pred

    def _update_extended_predictions(self, extended: ExtendedPredictions, ext_pred: Dict) -> None:
        """Update extended predictions from detection results (optimized)."""
        # Use mapping for faster lookup
        assassination = ext_pred.get("assassination", [])
        if assassination:
            if "khamenei_targeted" in assassination:
                extended.khamenei_assassination_likely += 1
            if "khamenei_survives" in assassination:
                extended.khamenei_assassination_unlikely += 1
        
        regime = ext_pred.get("regime_change", [])
        if regime:
            if "regime_falls" in regime:
                extended.regime_falls += 1
            if "regime_survives" in regime:
                extended.regime_survives += 1
        
        war_scale = ext_pred.get("war_scale", [])
        if war_scale:
            if "major_war" in war_scale:
                extended.major_war += 1
            if "limited_conflict" in war_scale:
                extended.limited_conflict += 1
        
        war_duration = ext_pred.get("war_duration", [])
        if war_duration:
            dur_set = set(war_duration)
            if "days" in dur_set: extended.war_days += 1
            if "weeks" in dur_set: extended.war_weeks += 1
            if "months" in dur_set: extended.war_months += 1
            if "years" in dur_set: extended.war_years += 1
        
        negotiation = ext_pred.get("negotiation", [])
        if negotiation:
            if "deal_likely" in negotiation:
                extended.deal_likely += 1
            if "deal_unlikely" in negotiation:
                extended.deal_unlikely += 1
        
        future_gov = ext_pred.get("future_government", [])
        if future_gov:
            gov_set = set(future_gov)
            if "monarchy_return" in gov_set: extended.monarchy_return += 1
            if "secular_democracy" in gov_set: extended.secular_democracy += 1
            if "islamic_reform" in gov_set: extended.islamic_reform += 1
            if "military_rule" in gov_set: extended.military_rule += 1
            if "chaos" in gov_set: extended.chaos += 1
        
        pahlavi = ext_pred.get("pahlavi", [])
        if pahlavi:
            if "pahlavi_returns" in pahlavi:
                extended.pahlavi_returns += 1
            if "pahlavi_unlikely" in pahlavi:
                extended.pahlavi_unlikely += 1
        
        country = ext_pred.get("country_comparison", [])
        if country:
            country_set = set(country)
            if "like_iraq" in country_set: extended.like_iraq += 1
            if "like_libya" in country_set: extended.like_libya += 1
            if "like_syria" in country_set: extended.like_syria += 1
            if "like_syria_civil_war" in country_set: extended.like_syria_civil_war += 1
            if "like_syria_post_assad" in country_set: extended.like_syria_post_assad += 1
            if "like_afghanistan" in country_set: extended.like_afghanistan += 1
            if "like_egypt" in country_set: extended.like_egypt += 1
            if "like_tunisia" in country_set: extended.like_tunisia += 1
            if "like_russia" in country_set: extended.like_russia += 1
            if "like_yugoslavia" in country_set: extended.like_yugoslavia += 1
            if "like_venezuela" in country_set: extended.like_venezuela += 1
            if "like_north_korea" in country_set: extended.like_north_korea += 1
            if "like_south_korea" in country_set: extended.like_south_korea += 1
            if "like_1979_iran" in country_set: extended.like_1979_iran += 1
        
        musk = ext_pred.get("musk_iran", [])
        if musk:
            musk_set = set(musk)
            if "musk_starlink_iran" in musk_set: extended.musk_starlink_iran += 1
            if "musk_diplomacy" in musk_set: extended.musk_diplomacy += 1
            if "musk_pro_war" in musk_set: extended.musk_pro_war += 1
            if "musk_anti_war" in musk_set: extended.musk_anti_war += 1
        
        epstein = ext_pred.get("epstein", [])
        if epstein:
            epstein_set = set(epstein)
            if "epstein_israel" in epstein_set: extended.epstein_israel += 1
            if "epstein_iran_contra" in epstein_set: extended.epstein_iran_contra += 1
            if "epstein_documents" in epstein_set: extended.epstein_documents += 1
        
        # Axios detailed tracking
        axios_cats = ext_pred.get("axios", [])
        if axios_cats:
            extended.axios_mentions += 1
            axios_set = set(axios_cats) if isinstance(axios_cats, list) else {axios_cats}
            if "iran_strike" in axios_set: extended.axios_iran_strike += 1
            if "negotiations" in axios_set: extended.axios_negotiations += 1
            if "trump_iran" in axios_set: extended.axios_trump_iran += 1
            if "witkoff" in axios_set: extended.axios_witkoff += 1
            if "military" in axios_set: extended.axios_military += 1
            # Store sample reports (up to 10)
            if ext_pred.get("axios_sample") and len(extended.axios_sample_reports) < 10:
                extended.axios_sample_reports.append(ext_pred["axios_sample"])
    
    def _update_stats(self, stats_dict: Dict, key: str, prediction: int) -> None:
        """Update stats dict efficiently."""
        if key not in stats_dict:
            stats_dict[key] = {"count": 0, "attack": 0, "no_attack": 0, "neutral": 0}
        stats_dict[key]["count"] += 1
        if prediction == 1:
            stats_dict[key]["attack"] += 1
        elif prediction == -1:
            stats_dict[key]["no_attack"] += 1
        else:
            stats_dict[key]["neutral"] += 1

    def _analyze_comment_batch(self, batch: List[Tuple[int, dict]]) -> List[Tuple[int, 'CommentAnalysis', dict, dict]]:
        """Analyze a batch of comments (for parallel processing).
        
        Returns list of (index, analysis, ext_pred, comment_info) tuples.
        """
        results = []
        for idx, comment in batch:
            text = comment.get('body') or ''
            comment_id = comment.get('comment_id') or str(idx)
            author = comment.get('author') or 'unknown'
            subreddit = comment.get('subreddit') or 'unknown'
            
            analysis = self.analyze_comment(
                text=text,
                comment_id=comment_id,
                author=author,
                subreddit=subreddit
            )
            
            ext_pred = self._detect_extended_predictions(text)
            comment_info = {'text': text, 'author': author, 'subreddit': subreddit}
            results.append((idx, analysis, ext_pred, comment_info))
        
        return results

    # ------------------------------------------------------------------
    # Pre-filter: keep only Iran-relevant comments
    # ------------------------------------------------------------------
    @staticmethod
    def _is_iran_relevant(text: str, subreddit: str) -> bool:
        """Return True if the comment is plausibly about US-Iran conflict.

        A comment must contain at least one IRAN_RELEVANCE_ANCHOR keyword
        **or** originate from an Iran-focused subreddit.  This eliminates
        the vast majority of noise (Norwegian royal family stories, domestic
        US politics, etc.) that previously inflated the dataset to 99.5%
        neutral.
        """
        sub_lower = subreddit.lower()
        if sub_lower in IRAN_RELEVANT_SUBREDDITS:
            return True
        text_lower = text.lower()
        return any(anchor in text_lower for anchor in IRAN_RELEVANCE_ANCHORS)

    def _prefilter_comments(self, comments: List[dict]) -> List[dict]:
        """Pre-filter comments to only Iran-relevant ones.

        Returns a new list (does not mutate *comments*).
        """
        relevant = [
            c for c in comments
            if self._is_iran_relevant(
                c.get("body") or "",
                c.get("subreddit") or "",
            )
        ]
        return relevant

    # ------------------------------------------------------------------

    def analyze_comments(self, comments: List[dict], 
                        progress_callback=None,
                        use_parallel: bool = True,
                        max_workers: int = None) -> AnalysisResults:
        """
        Analyze multiple comments and aggregate results.

        Two-phase architecture:
          Phase 1 – regex-only pass (threads, ~2 s for 10 K comments)
          Phase 2 – batched zero-shot on neutrals only (single model, ~1.5 GB)
        """
        start_time = datetime.now()
        results = AnalysisResults()

        # ---- Stage 0: Pre-filter to Iran-relevant comments only ----
        raw_count = len(comments)
        comments = self._prefilter_comments(comments)
        filtered_count = len(comments)
        if raw_count:
            print(f"\n🔎 Pre-filter: {raw_count:,} → {filtered_count:,} Iran-relevant "
                  f"comments ({filtered_count/raw_count*100:.1f}% kept)", flush=True)

        n_comments = len(comments)
        print(f"\n🔍 Analyzing {n_comments:,} comments...", flush=True)

        # Per-author aggregation
        author_analyses: Dict[str, List[CommentAnalysis]] = defaultdict(list)
        extended = ExtendedPredictions()
        top_attack: list = []
        top_no_attack: list = []

        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, ANALYSIS_MAX_WORKERS)

        # ================================================================
        # PHASE 1 — Fast regex-only pass (threads)
        # ================================================================
        phase1_start = datetime.now()
        print(f"\n📋 Phase 1: Pattern matching ({max_workers} threads)...", flush=True)

        # Temporarily disable zero-shot so analyze_comment uses regex only
        zs_backup = self.use_zero_shot
        classifier_backup = self.classifier
        self.use_zero_shot = False
        self.classifier = None

        # all_results[i] = (analysis, ext_pred, comment_info)
        all_results: list = [None] * n_comments

        if use_parallel and n_comments > 100:
            batch_size = max(50, n_comments // (max_workers * 4))
            indexed_comments = list(enumerate(comments))
            batches = [indexed_comments[i:i + batch_size]
                       for i in range(0, n_comments, batch_size)]

            processed = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self._analyze_comment_batch, b): b
                           for b in batches}
                for future in as_completed(futures):
                    try:
                        batch_results = future.result()
                    except Exception as e:
                        print(f"   ⚠️ Batch error: {e}", flush=True)
                        continue
                    for idx, analysis, ext_pred, comment_info in batch_results:
                        all_results[idx] = (analysis, ext_pred, comment_info)
                    processed += len(batch_results)
                    if processed % 2000 < batch_size or processed == n_comments:
                        print(f"   ✏️  Phase 1: {processed:,}/{n_comments:,}", flush=True)
        else:
            for i, comment in enumerate(comments):
                text = comment.get('body') or ''
                analysis = self.analyze_comment(
                    text=text,
                    comment_id=comment.get('comment_id') or str(i),
                    author=comment.get('author') or 'unknown',
                    subreddit=comment.get('subreddit') or 'unknown',
                )
                ext_pred = self._detect_extended_predictions(text)
                all_results[i] = (analysis, ext_pred,
                                  {'text': text,
                                   'author': comment.get('author') or 'unknown',
                                   'subreddit': comment.get('subreddit') or 'unknown'})

        # Restore zero-shot state
        self.use_zero_shot = zs_backup
        self.classifier = classifier_backup

        processed_count = sum(1 for r in all_results if r is not None)
        neutral_count = sum(1 for r in all_results if r and r[0].prediction == 0)
        # Comments with weak regex-only signal (no zero-shot ran in Phase 1)
        # also need re-evaluation — a single low-weight pattern can inflate
        # confidence to ~98% without opposing signal from zero-shot.
        weak_regex_count = sum(
            1 for r in all_results
            if r and r[0].prediction != 0
            and r[0].zs_attack_score == 0.0 and r[0].zs_no_attack_score == 0.0
            and r[0].confidence < 0.85
        )
        opinionated_p1 = processed_count - neutral_count
        phase1_sec = (datetime.now() - phase1_start).total_seconds()
        print(f"   ✅ Phase 1 done in {phase1_sec:.1f}s — "
              f"{opinionated_p1:,} opinionated, {neutral_count:,} neutral, "
              f"{weak_regex_count:,} weak-regex (will re-check)", flush=True)

        # ================================================================
        # PHASE 2 — Embedding similarity on neutral + weak-regex comments
        # ================================================================
        needs_zs = neutral_count + weak_regex_count
        if zs_backup and classifier_backup and needs_zs > 0:
            zs_cap = self._zero_shot_max_comments or needs_zs
            # Collect comments needing zero-shot: neutral OR weak regex-only
            neutral_indices: List[int] = []
            for idx in range(n_comments):
                r = all_results[idx]
                if r is None:
                    continue
                needs_reeval = (
                    r[0].prediction == 0  # neutral
                    or (  # weak regex-only (no ZS ran, low confidence)
                        r[0].zs_attack_score == 0.0
                        and r[0].zs_no_attack_score == 0.0
                        and r[0].confidence < 0.85
                    )
                )
                if needs_reeval:
                    txt = r[2].get('text', '')
                    if len(txt) >= ZERO_SHOT_MIN_TEXT_LENGTH:
                        neutral_indices.append(idx)
                        if len(neutral_indices) >= zs_cap:
                            break

            zs_total = len(neutral_indices)
            EMB_BATCH = 256  # much larger batches — embedding is fast
            print(f"\n🧠 Phase 2: Embedding similarity on {zs_total:,} comments "
                  f"(batch_size={EMB_BATCH}, model ≈80 MB RAM)...", flush=True)

            import torch
            import numpy as np

            phase2_start = datetime.now()
            zs_reclassified = 0
            TEMP = self._EMB_TEMPERATURE

            # Encode ALL candidate texts at once (fast — ~10-20s for 10k on CPU)
            all_texts = [
                all_results[i][2].get('text', '')[:512]
                for i in neutral_indices
            ]
            print(f"   ⏳ Encoding {zs_total:,} texts...", flush=True)
            all_embeddings = self._encode_texts(all_texts, batch_size=EMB_BATCH)

            encode_sec = (datetime.now() - phase2_start).total_seconds()
            print(f"   ✅ Encoded in {encode_sec:.1f}s "
                  f"({zs_total / max(encode_sec, 0.01):.0f} texts/sec)", flush=True)

            # Vectorised cosine similarities (dot product — vectors are L2-normed)
            attack_sims = torch.mv(all_embeddings, self._attack_centroid)    # (N,)
            no_attack_sims = torch.mv(all_embeddings, self._no_attack_centroid)  # (N,)

            # Softmax with temperature → probability-like scores per comment
            logits = torch.stack([attack_sims * TEMP, no_attack_sims * TEMP], dim=1)
            probs = torch.softmax(logits, dim=1).numpy()  # (N, 2)

            emb_attack_scores = probs[:, 0]   # float array, 0–1
            emb_no_attack_scores = probs[:, 1]

            # Apply 3-tier decision logic per comment
            for j, idx in enumerate(neutral_indices):
                emb_attack = float(emb_attack_scores[j])
                emb_no_attack = float(emb_no_attack_scores[j])

                old = all_results[idx][0]
                # Re-run fast regex for raw pattern scores
                txt = all_results[idx][2].get('text', '')
                pat_a, m_a = self._match_patterns_compiled(
                    txt, self._compiled_attack, self._attack_keywords)
                pat_n, m_n = self._match_patterns_compiled(
                    txt, self._compiled_no_attack, self._no_attack_keywords)

                ta = (pat_a * 2.0) + emb_attack
                tn = (pat_n * 2.0) + emb_no_attack

                # Same 3-tier decision as analyze_comment
                if ta > tn + 0.08:
                    pred, conf = 1, min(ta / (ta + tn + 0.01), 1.0)
                elif tn > ta + 0.08:
                    pred, conf = -1, min(tn / (ta + tn + 0.01), 1.0)
                elif emb_attack > 0.55 and emb_attack > emb_no_attack + 0.05:
                    pred, conf = 1, min(emb_attack, 0.65)
                elif emb_no_attack > 0.55 and emb_no_attack > emb_attack + 0.05:
                    pred, conf = -1, min(emb_no_attack, 0.65)
                elif ta > 0.10 and ta > tn + 0.02:
                    pred, conf = 1, min(ta / (ta + tn + 0.01), 0.55)
                elif tn > 0.10 and tn > ta + 0.02:
                    pred, conf = -1, min(tn / (ta + tn + 0.01), 0.55)
                else:
                    pred, conf = 0, 0.0

                if pred != 0:
                    zs_reclassified += 1

                new_a = CommentAnalysis(
                    comment_id=old.comment_id, author=old.author,
                    subreddit=old.subreddit, prediction=pred,
                    confidence=conf,
                    pattern_matches=m_a + m_n,
                    scenario_matches=old.scenario_matches,
                    timeline_matches=old.timeline_matches,
                    zs_attack_score=emb_attack,
                    zs_no_attack_score=emb_no_attack,
                )
                all_results[idx] = (new_a, all_results[idx][1],
                                    all_results[idx][2])

            phase2_sec = (datetime.now() - phase2_start).total_seconds()
            print(f"   ✅ Phase 2 done in {phase2_sec:.1f}s — "
                  f"{zs_reclassified:,} comments reclassified", flush=True)

        # ================================================================
        # PHASE 3 — Aggregate all results
        # ================================================================
        print(f"\n📊 Aggregating results...", flush=True)

        for idx in range(n_comments):
            r = all_results[idx]
            if r is None:
                continue
            analysis, ext_pred, comment_info = r
            text = comment_info['text']
            author = comment_info['author']
            subreddit = comment_info['subreddit']

            self._update_extended_predictions(extended, ext_pred)
            author_analyses[author].append(analysis)
            results.total_comments_analyzed += 1

            prediction = analysis.prediction
            for scenario in analysis.scenario_matches:
                self._update_stats(results.scenario_stats, scenario, prediction)
            for timeline in analysis.timeline_matches:
                self._update_stats(results.timeline_stats, timeline, prediction)
            self._update_stats(results.subreddit_stats, subreddit, prediction)

            confidence = analysis.confidence
            if confidence > 0.6:
                entry = {"text": text[:500], "confidence": confidence,
                         "author": author, "subreddit": subreddit}
                if prediction == 1:
                    top_attack.append(entry)
                elif prediction == -1:
                    top_no_attack.append(entry)

        # Store extended predictions
        results.extended_predictions = extended.to_dict()

        # Non-LLM user opinion summary
        if _USER_OPINION_SUMMARY_AVAILABLE and summarize_user_opinions:
            try:
                summary = summarize_user_opinions(
                    comments=comments, source_label="Reddit",
                    top_n_themes=8, max_quotes_per_theme=3, max_total_quotes=20,
                )
                results.user_opinion_summary = summary
                results.user_opinion_themes = [
                    t.get("theme") for t in (summary.get("themes") or [])
                    if isinstance(t, dict)
                ]
            except Exception:
                results.user_opinion_summary = {}

        # Sort and limit top comments
        results.top_attack_comments = sorted(
            top_attack, key=lambda x: x['confidence'], reverse=True)[:20]
        results.top_no_attack_comments = sorted(
            top_no_attack, key=lambda x: x['confidence'], reverse=True)[:20]

        # Aggregate by author
        confidences: list = []
        for author, analyses in author_analyses.items():
            attack_count = sum(1 for a in analyses if a.prediction == 1)
            no_attack_count = sum(1 for a in analyses if a.prediction == -1)
            conf_vals = [a.confidence for a in analyses if a.confidence > 0]
            avg_conf = sum(conf_vals) / len(conf_vals) if conf_vals else 0
            subreddits_set = {a.subreddit for a in analyses}

            if attack_count > no_attack_count:
                results.predict_attack += 1
                if avg_conf > 0.7:
                    results.high_confidence_attack += 1
                prediction = 1
            elif no_attack_count > attack_count:
                results.predict_no_attack += 1
                if avg_conf > 0.7:
                    results.high_confidence_no_attack += 1
                prediction = -1
            else:
                results.neutral += 1
                prediction = 0

            if avg_conf > 0:
                confidences.append(avg_conf)

            results.author_predictions[author] = {
                "prediction": prediction,
                "confidence": avg_conf,
                "comments_analyzed": len(analyses),
                "subreddits": list(subreddits_set),
            }

        results.total_authors_analyzed = len(author_analyses)
        results.avg_confidence = (sum(confidences) / len(confidences)
                                  if confidences else 0.0)

        # Reasoning summary
        results.attack_reasons = self._extract_reasons(results.top_attack_comments)
        results.no_attack_reasons = self._extract_reasons(results.top_no_attack_comments)

        # Metadata
        results.analyzed_at = datetime.now().isoformat()
        results.analysis_duration_seconds = (datetime.now() - start_time).total_seconds()

        opinionated = results.predict_attack + results.predict_no_attack
        print(f"\n✅ Analysis complete in {results.analysis_duration_seconds:.1f} seconds",
              flush=True)
        print(f"   📊 {results.total_comments_analyzed:,} comments from "
              f"{results.total_authors_analyzed:,} authors", flush=True)
        if results.total_authors_analyzed:
            print(f"   🗣️  {opinionated:,} users with clear opinion "
                  f"({100*opinionated/results.total_authors_analyzed:.1f}% of analysed)",
                  flush=True)
        print(f"   🔴 Attack: {results.predict_attack}  |  "
              f"🟢 No Attack: {results.predict_no_attack}  |  "
              f"⚪ Neutral: {results.neutral}", flush=True)

        return results

    def _extract_reasons(self, comments: List[dict]) -> List[str]:
        """Extract key reasons/arguments from top comments."""
        reasons = []
        
        # Common reason patterns
        reason_patterns = [
            r"because\s+(.{20,100}?)[\.\,\!]",
            r"since\s+(.{20,100}?)[\.\,\!]",
            r"the reason is\s+(.{20,100}?)[\.\,\!]",
            r"due to\s+(.{20,100}?)[\.\,\!]",
        ]
        
        for comment in comments[:10]:
            text = comment.get('text', '')
            for pattern in reason_patterns:
                matches = re.findall(pattern, text.lower())
                for match in matches[:1]:  # Take first match only
                    reason = match.strip().capitalize()
                    if len(reason) > 20 and reason not in reasons:
                        reasons.append(reason)
        
        return reasons[:10]

    def generate_reasoning(self, results: AnalysisResults) -> dict:
        """
        Generate detailed reasoning about the analysis results.
        
        Returns:
            Dictionary with reasoning components
        """
        reasoning = {
            "summary": "",
            "confidence_assessment": "",
            "scenario_analysis": "",
            "timeline_analysis": "",
            "key_factors": [],
            "uncertainties": [],
            "comparison_notes": ""
        }
        
        total_opinionated = results.predict_attack + results.predict_no_attack
        total_users = results.total_authors_analyzed
        
        if total_opinionated == 0:
            reasoning["summary"] = "Insufficient data to make a prediction."
            return reasoning
        
        attack_pct = 100 * results.predict_attack / total_opinionated
        no_attack_pct = 100 * results.predict_no_attack / total_opinionated
        opinionated_pct = 100 * total_opinionated / total_users if total_users > 0 else 0
        
        # Summary - CRITICAL: Be clear about sample sizes to avoid confusion
        sample_note = f"(Note: Only {total_opinionated:,} of {total_users:,} users ({opinionated_pct:.1f}%) expressed clear opinions)"
        
        if attack_pct > 60:
            reasoning["summary"] = (
                f"Among Reddit users who expressed a clear opinion, {attack_pct:.1f}% predict US military action against Iran. "
                f"{sample_note}"
            )
        elif no_attack_pct > 60:
            reasoning["summary"] = (
                f"Among Reddit users who expressed a clear opinion, {no_attack_pct:.1f}% predict NO US military action against Iran. "
                f"{sample_note}"
            )
        else:
            reasoning["summary"] = (
                f"Reddit users with opinions are divided on US-Iran conflict: {attack_pct:.1f}% predict attack, {no_attack_pct:.1f}% predict no attack. "
                f"{sample_note}"
            )
        
        # Confidence assessment
        if results.avg_confidence > 0.7:
            reasoning["confidence_assessment"] = (
                f"High average confidence ({results.avg_confidence:.2f}). "
                f"Users express strong opinions on this topic."
            )
        elif results.avg_confidence > 0.5:
            reasoning["confidence_assessment"] = (
                f"Moderate confidence ({results.avg_confidence:.2f}). "
                f"Some uncertainty in user predictions."
            )
        else:
            reasoning["confidence_assessment"] = (
                f"Low confidence ({results.avg_confidence:.2f}). "
                f"Users seem uncertain about outcomes."
            )
        
        # Scenario analysis
        if results.scenario_stats:
            most_discussed = max(results.scenario_stats.items(), key=lambda x: x[1]["count"])
            reasoning["scenario_analysis"] = (
                f"Most discussed scenario: {most_discussed[0].replace('_', ' ').title()} "
                f"({most_discussed[1]['count']} mentions). "
            )
            
            attack_count = most_discussed[1]["attack"]
            no_attack_count = most_discussed[1]["no_attack"]
            total_opinions = attack_count + no_attack_count
            
            if total_opinions > 0:
                attack_ratio = attack_count / total_opinions
                if attack_ratio > 0.55:
                    reasoning["scenario_analysis"] += f"This scenario is associated with attack predictions ({attack_count} vs {no_attack_count})."
                elif attack_ratio < 0.45:
                    reasoning["scenario_analysis"] += f"This scenario is associated with no-attack predictions ({no_attack_count} vs {attack_count})."
                else:
                    reasoning["scenario_analysis"] += f"This scenario shows mixed opinions ({attack_count} attack vs {no_attack_count} no-attack, ~50/50 split)."
            else:
                reasoning["scenario_analysis"] += "No clear prediction direction for this scenario."
        
        # Timeline analysis  
        if results.timeline_stats:
            timeline_order = [
                "today", "tomorrow", "this_week", "next_week",
                "this_month", "next_month", "this_quarter",
                "this_year", "long_term", "conditional",
            ]
            mentioned_timelines = [t for t in timeline_order if t in results.timeline_stats]
            
            if mentioned_timelines:
                primary_timeline = mentioned_timelines[0]
                reasoning["timeline_analysis"] = (
                    f"Primary timeline discussed: {primary_timeline.replace('_', ' ').title()}. "
                )
                
                if primary_timeline in ["immediate", "short_term"]:
                    reasoning["timeline_analysis"] += "Users expect near-term developments."
                elif primary_timeline == "conditional":
                    reasoning["timeline_analysis"] += "Outcomes seen as dependent on specific triggers."
        
        # Key factors
        reasoning["key_factors"] = results.attack_reasons[:5] + results.no_attack_reasons[:5]
        
        # Uncertainties
        reasoning["uncertainties"] = [
            "Social media sentiment may not reflect actual geopolitical developments",
            "Reddit users may have limited access to classified intelligence",
            "Predictions can be influenced by recent news cycles",
            f"Sample size: {results.total_authors_analyzed} users analyzed"
        ]
        
        return reasoning
