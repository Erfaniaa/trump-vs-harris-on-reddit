"""
Configuration for US-Iran Conflict Prediction Analyzer
======================================================
Updated: February 2026

Includes comprehensive analysis of:
- Attack probability by day/week/month
- Regime change scenarios
- War duration estimates
- Negotiation outcomes
- Future government scenarios
- Reza Pahlavi return probability
"""

# ==============================================================================
# SUBREDDIT CONFIGURATION
# ==============================================================================

# OPTIMIZED FOR SPEED: ~70 subreddits (was 347)
# Focus on HIGH-RELEVANCE sources only. Removed:
# - Sports (soccer, football, worldcup)
# - Generic finance (personal finance, ETFs, brokerage-specific)
# - Conspiracy/misc
# - Low-relevance regional subs
#
# This reduces download time by ~5x while capturing 95%+ of relevant content

SUBREDDIT_NAMES_LIST = [
    # ====== TIER 1: IRAN SPECIFIC (highest signal) ======
    "iran",
    "iranian",
    "NewIran",
    "IranPolitics",
    "ProIran",
    "ShiaPolitics",
    
    # ====== TIER 1: MIDDLE EAST CONFLICT ======
    "MiddleEastNews",
    "MiddleEast",
    "IsraelPalestine",
    "syriancivilwar",
    "Israel",
    "lebanon",
    "Iraq",
    "Syria",
    "Yemen",
    "AskMiddleEast",
    
    # ====== TIER 1: MILITARY & DEFENSE ======
    "CredibleDefense",
    "Military",
    "WarCollege",
    "CombatFootage",
    "NonCredibleDefense",
    "LessCredibleDefence",
    "navy",
    "AirForce",
    
    # ====== TIER 1: PREDICTION MARKETS ======
    "Polymarket",
    "predictit",
    "PredictionMarket",
    "metaculus",
    
    # ====== TIER 2: GEOPOLITICS ======
    "geopolitics",
    "IRstudies",
    "worldnews",
    "anime_titties",  # Actually serious world news
    "InternationalNews",
    
    # ====== TIER 2: US POLITICS (foreign policy focus) ======
    "politics",
    "NeutralPolitics",
    "Conservative",
    "trump",
    "moderatepolitics",
    
    # ====== TIER 2: KEY NEWS ======
    "news",
    "TrueReddit",
    "neutralnews",
    
    # ====== TIER 2: REGIONAL PLAYERS ======
    "Turkey",
    "SaudiArabia",
    "russia",
    "ukraine",
    "UkrainianConflict",
    "China",
    
    # ====== TIER 3: OIL & COMMODITIES (conflict indicator) ======
    "oil",
    "Commodities",
    "energy",
    "Gold",
    
    # ====== TIER 3: FINANCIAL MARKETS (conflict indicator) ======
    "wallstreetbets",
    "stocks",
    "investing",
    "Economics",
    "CryptoCurrency",
    "Bitcoin",
    
    # ====== TIER 3: MUSK (potential backchannel) ======
    "elonmusk",
    "SpaceX",
    
    # ====== TIER 3: MISC HIGH-VALUE ======
    "collapse",
    "preppers",
]

# ==============================================================================
# CONTEXT KEYWORDS (for filtering relevant comments)
# ==============================================================================

# Comments must contain at least one of these to be considered relevant
CONTEXT_KEYWORDS = [
    # Country/Region names
    "Iran", "Iranian", "Tehran", "Persia", "Persian", "Islamic Republic",
    
    # Political figures - Iran
    "Khamenei", "Raisi", "Rouhani", "Zarif", "Soleimani", "Pezeshkian",
    "Araghchi", "supreme leader", "ayatollah",
    "Larijani", "Ali Larijani", "Radan", "Ahmad Reza Radan",
    "لاریجانی", "رادان",
    
    # Political figures - US/Israel
    "Trump", "Donald Trump", "POTUS", "Netanyahu", "Witkoff", "Biden",
    "Blinken", "Austin", "Gallant",
    
    # Opposition figures
    "Pahlavi", "Reza Pahlavi", "Shah", "Crown Prince", "MEK", "Rajavi",
    "Mojahedin", "monarchist", "exiled",
    
    # Iranian media
    "Fars News", "Fars", "IRNA", "IRIB", "Mehr News", "Mehr", "Press TV",
    "Tasnim", "ISNA",
    
    # Military/Organizations
    "IRGC", "Revolutionary Guard", "Quds Force", "Basij", "Sepah",
    "Hezbollah", "Houthi", "proxy", "proxies", "militia",
    "USS", "aircraft carrier", "Abraham Lincoln", "Pentagon", "IDF",
    
    # Nuclear program
    "nuclear", "uranium", "enrichment", "centrifuge", "JCPOA", "nuclear deal",
    "Natanz", "Fordow", "breakout", "bomb", "atomic", "fissile",
    
    # Geopolitical terms
    "sanction", "sanctions", "embargo", "strait of hormuz", "persian gulf",
    "regime change", "regime", "overthrow", "topple", "collapse",
    
    # US-Iran specific
    "US-Iran", "Iran-US", "American-Iranian", "Iranian-American",
    "strike", "attack", "war", "bomb", "invade", "retaliate",
    
    # Diplomacy
    "negotiate", "deal", "negotiation", "talks", "diplomacy", "diplomatic",
    "Oman", "Qatar", "mediator", "ceasefire", "de-escalation",
    
    # Protests
    "protest", "uprising", "revolution", "demonstrator", "crackdown",
    "execution", "death toll", "Mahsa Amini",
    
    # Prediction markets
    "Polymarket", "prediction market", "odds", "probability", "bet",
    
    # Gold & Precious Metals (Iran conflict signal)
    "gold", "XAUUSD", "gold price", "precious metals", "bullion",
    "gold spike", "gold surge", "safe haven", "gold rally",
    "gold record", "gold high", "gold ATH", "gold all-time high",
    "war premium", "geopolitical premium", "flight to safety",
    "gold iran", "gold middle east", "gold war", "gold conflict",
    "silver", "platinum", "palladium",
    
    # Cryptocurrency (geopolitical sensitivity)
    "bitcoin", "BTC", "ethereum", "ETH", "crypto",
    "bitcoin iran", "crypto iran", "bitcoin war", "crypto war",
    "bitcoin geopolitics", "crypto geopolitics",
    "risk-off", "risk-on", "risk asset", "digital gold",
    "bitcoin safe haven", "crypto sanctions",
    
    # Global Economy & Markets
    "oil price", "crude oil", "brent", "WTI", "oil spike",
    "oil iran", "hormuz oil", "strait oil", "oil supply",
    "global markets", "market crash", "stock crash",
    "recession", "economic crisis", "financial crisis",
    "inflation", "stagflation", "hyperinflation",
    "dollar", "USD", "DXY", "dollar index",
    "treasury", "bonds", "yields", "interest rates",
    "VIX", "volatility", "fear index",
    "commodities", "commodity spike",
    
    # Economic sanctions & Iran
    "sanctions iran", "iran sanctions", "swift iran",
    "oil sanctions", "banking sanctions", "secondary sanctions",
    "sanctions evasion", "iran economy", "rial",
    
    # News sources
    "reuters", "bbc", "cnn", "aljazeera", "nytimes", "washington post",
    "axios", "axios news", "scoop", "breaking axios",
    
    # Israel/Palestine
    "israel", "israeli", "palestine", "palestinian", "Gaza", "West Bank",
    "IDF", "Mossad", "assassination",
    
    # Persian Gulf
    "Persian Gulf", "Gulf", "Strait of Hormuz", "Hormuz", "Bandar Abbas",
    "Gulf of Oman", "Sea of Oman", "Oman Sea",
    "naval", "navy", "fleet", "armada", "carrier", "destroyer",
    
    # Explosions/Attacks in Iran
    "explosion", "blast", "attack", "bombed", "bombing", "sabotage",
    "Natanz", "Fordow", "Isfahan", "Ahvaz", "Karaj", "Parand",
    
    # Protests/Crackdown
    "protest", "protester", "demonstrator", "crackdown", "death toll",
    "killed", "executed", "execution", "massacre", "bloodshed",
    "uprising", "revolution", "Mahsa Amini",
    
    # IRGC/Basij/Regime
    "IRGC", "Sepah", "Revolutionary Guard", "Basij", "Basiji",
    "regime", "Islamic Republic", "mullah", "ayatollah",
    "Pezeshkian", "Khamenei", "supreme leader",
    
    # Pentagon Pizza indicator
    "Pentagon pizza", "pizza index", "pizza report", "busy night",
    "military activity", "late night Pentagon",
    
    # ====== US STOCK MARKET KEYWORDS ======
    # Major Indices
    "S&P 500", "SPX", "SPY", "S&P500", "sp500",
    "NASDAQ", "QQQ", "IXIC", "nasdaq100",
    "Dow Jones", "DJIA", "DJI", "Dow", "dow30",
    "Russell 2000", "IWM", "small cap",
    "VIX", "CBOE", "fear index", "volatility index",
    
    # Market Movements
    "stock market crash", "market selloff", "market correction",
    "bear market", "bull market", "market rally",
    "stock surge", "stock plunge", "stocks tumble",
    "market volatility", "risk-off", "risk-on",
    "flight to safety", "safe haven assets",
    "market panic", "market fear", "investor sentiment",
    
    # Sector Keywords
    "energy stocks", "oil stocks", "XLE",
    "defense stocks", "ITA", "aerospace stocks",
    "tech stocks", "XLK", "FAANG", "magnificent seven",
    "healthcare stocks", "XLV", "pharma stocks",
    "utility stocks", "XLU", "defensive stocks",
    "financial stocks", "XLF", "bank stocks",
    "airline stocks", "JETS", "travel stocks",
    "consumer stocks", "XLY", "XLP",
    "industrial stocks", "XLI",
    "materials stocks", "XLB", "mining stocks",
    "real estate", "XLRE", "REITs",
    
    # Individual Stocks (geopolitically sensitive)
    "Lockheed", "LMT", "Raytheon", "RTX",
    "Northrop", "NOC", "Boeing", "BA",
    "General Dynamics", "GD", "L3Harris", "LHX",
    "Exxon", "XOM", "Chevron", "CVX",
    "ConocoPhillips", "COP", "Halliburton", "HAL",
    "Schlumberger", "SLB",
    
    # Market Analysis Terms
    "P/E ratio", "earnings", "dividend",
    "market cap", "valuation", "overvalued", "undervalued",
    "technical analysis", "fundamental analysis",
    "support level", "resistance level",
    "moving average", "RSI", "MACD",
    
    # ====== REGIONAL PLAYERS KEYWORDS ======
    # Turkey
    "Turkey", "Turkish", "Ankara", "Erdogan",
    "Turkish lira", "TRY", "Turkish military",
    "NATO Turkey", "Turkey Iran", "Turkish mediation",
    
    # Saudi Arabia
    "Saudi Arabia", "Saudi", "Riyadh", "MBS",
    "Mohammed bin Salman", "Saudi Aramco",
    "Saudi oil", "OPEC", "Saudi Iran",
    
    # UAE
    "UAE", "Emirates", "Abu Dhabi", "Dubai",
    "MBZ", "Mohammed bin Zayed", "Emirati",
    
    # Qatar
    "Qatar", "Doha", "Qatari", "Al Jazeera",
    "Qatar mediation", "Al Thani",
    
    # Oman
    "Oman", "Muscat", "Omani", "Oman mediation",
    "Sultan of Oman", "back channel",
    
    # Egypt
    "Egypt", "Egyptian", "Cairo", "Sisi",
    "Suez Canal", "Egyptian military",
    
    # Iraq
    "Iraq", "Iraqi", "Baghdad", "PMF",
    "Iraqi militia", "Kata'ib", "Hashd al-Shaabi",
    
    # Syria
    "Syria", "Syrian", "Damascus", "Assad",
    "Jolani", "HTS", "Syrian civil war",
    
    # Lebanon
    "Lebanon", "Lebanese", "Beirut",
    "Hezbollah", "Nasrallah",
    
    # ====== US DOMESTIC POLITICS ======
    "Congress", "Senate", "House", "Capitol",
    "AUMF", "war powers", "authorization",
    "impeachment", "election", "2026 midterms",
    "Biden", "Harris", "Vance", "JD Vance",
    "DeSantis", "Haley", "Pompeo",
    "Secretary of State", "Secretary of Defense",
    "National Security Advisor", "NSC",
    "CIA", "DNI", "intelligence community",
    
    # World Cup 2026 (US hosting)
    "World Cup", "FIFA", "World Cup 2026",
    "soccer", "football", "tournament",
    
    # ====== INTERNAL IRANIAN POLITICS ======
    # Current Leadership
    "Pezeshkian", "Mojtaba Khamenei", "Larijani",
    "Radan", "Ahmad Jannati", "Guardian Council",
    "Assembly of Experts", "Expediency Council",
    
    # Factions
    "hardliners", "reformists", "moderates",
    "principalists", "Raisi faction",
    "IRGC political", "clergy",
    
    # Internal Crisis
    "rial collapse", "toman", "Iranian economy",
    "inflation Iran", "unemployment Iran",
    "brain drain", "emigration Iran",
    "Woman Life Freedom", "Jin Jiyan Azadi",
    "hijab protests", "morality police",
    
    # Succession
    "succession", "next supreme leader",
    "Khamenei health", "Khamenei age",
    "leadership transition", "power vacuum",
    
    # Opposition
    "MEK", "Mojahedin", "NCRI",
    "Reza Pahlavi", "monarchist", "Crown Prince",
    "diaspora", "exiled opposition",
    
    # ====== ZELENSKY & UKRAINE CONNECTION ======
    "Zelensky", "Ukraine", "Ukrainian",
    "Russia Ukraine", "NATO", "European security",
    "Iran drones Ukraine", "Shahed", "drone attack",
    "Iran Russia alliance", "Moscow Tehran",
    
    # ====== CHINA CONNECTION ======
    "China Iran", "Beijing Tehran", "Chinese oil",
    "Iran oil imports", "sanctions evasion China",
    "Belt and Road", "BRI Iran",
    "Xi Jinping", "Chinese mediation",
    
    # ====== IRGC TERRORIST DESIGNATION ======
    "IRGC terrorist", "terrorist designation",
    "FTO", "foreign terrorist organization",
    "IRGC sanctions", "Quds Force terrorist",
    "delisting IRGC", "IRGC designation",
    
    # ====== OIL & ENERGY GEOPOLITICS ======
    "Iranian oil", "oil exports Iran", "oil tanker",
    "oil sanctions", "oil waivers",
    "OPEC+ Iran", "oil smuggling",
    "Strait of Hormuz oil", "oil chokepoint",
    "LNG", "natural gas Iran", "South Pars",
    
    # ====== NAVAL & MILITARY PRESENCE ======
    "Fifth Fleet", "CENTCOM", "NAVCENT",
    "carrier strike group", "CSG",
    "USS", "aircraft carrier", "destroyer",
    "naval exercises", "military exercises",
    "Persian Gulf deployment", "Gulf of Oman",
    "B-52", "B-2", "stealth bomber",
    "F-35", "F-22", "air superiority",
    "Tomahawk", "cruise missile", "JDAM",
    "bunker buster", "MOP", "GBU-57",
]

# ==============================================================================
# PREDICTION KEYWORDS
# ==============================================================================

# Keywords suggesting attack/war WILL happen
ATTACK_WILL_HAPPEN_KEYWORDS = [
    # Certainty expressions
    "will attack", "going to attack", "will strike", "going to strike",
    "will bomb", "going to bomb", "will invade", "inevitable",
    "imminent", "matter of time", "war is coming", "strike is coming",
    "about to attack", "preparing to attack", "planning to attack",
    
    # Predictions
    "expect war", "expecting attack", "predict war", "war inevitable",
    "conflict unavoidable", "attack certain", "strike inevitable",
    "military action imminent", "invasion coming",
    
    # Escalation language
    "escalate to war", "lead to war", "trigger attack", "provoke strike",
    "no choice but to attack", "forced to strike", "must attack",
    
    # Timeline predictions
    "attack soon", "strike soon", "war soon", "within weeks",
    "within months", "before end of year", "this year",
]

# Keywords suggesting attack/war WON'T happen
ATTACK_WONT_HAPPEN_KEYWORDS = [
    # Negation expressions
    "won't attack", "will not attack", "not going to attack",
    "won't strike", "will not strike", "no attack", "no war",
    "won't bomb", "no invasion", "won't invade",
    
    # Uncertainty/Doubt
    "unlikely", "improbable", "doubtful", "won't happen",
    "not going to happen", "never attack", "never strike",
    
    # Diplomatic language
    "diplomatic solution", "negotiate", "negotiation", "talks",
    "de-escalation", "de-escalate", "peace", "peaceful resolution",
    "avoid war", "prevent war", "avert attack",
    
    # Bluff/Posturing
    "just bluffing", "bluff", "posturing", "saber rattling",
    "empty threat", "empty threats", "all talk", "rhetoric",
    "won't follow through", "backing down",
    
    # Constraints
    "too costly", "too risky", "can't afford", "no appetite for war",
    "war weary", "public opinion against",
]

# ==============================================================================
# SCENARIO ANALYSIS KEYWORDS
# ==============================================================================

# Keywords for different attack scenarios
SCENARIO_KEYWORDS = {
    "nuclear_strike": [
        "nuclear facility", "nuclear site", "Natanz", "Fordow", "Arak",
        "enrichment facility", "centrifuge", "nuclear strike", "Bushehr",
        "Isfahan", "nuclear scientist", "bomb program",
    ],
    "military_bases": [
        "IRGC base", "military base", "missile site", "drone facility",
        "Revolutionary Guard", "Quds Force headquarters", "air defense",
        "radar site", "command center",
    ],
    "leadership_targeted": [
        "decapitation strike", "leadership", "kill Khamenei",
        "Khamenei", "assassinate", "targeted killing", "supreme leader",
        "assassination", "regime head", "ayatollah",
    ],
    "limited_strike": [
        "limited strike", "surgical strike", "precision strike",
        "limited attack", "proportional response", "tit for tat",
        "measured response", "calibrated strike",
    ],
    "full_scale_war": [
        "full scale war", "invasion", "ground troops", "occupation",
        "regime change", "total war", "all out war", "boots on ground",
        "land invasion", "massive attack",
    ],
    "proxy_conflict": [
        "proxy war", "proxy conflict", "Hezbollah", "Houthi",
        "militia", "indirect", "through proxies", "Iraqi militias",
        "PMF", "Hashd", "Kata'ib Hezbollah",
    ],
    "cyber_attack": [
        "cyber attack", "cyber war", "Stuxnet", "hack",
        "cyber operation", "digital attack", "infrastructure hack",
    ],
}

# Timeline keywords - granular
TIMELINE_KEYWORDS = {
    "today": ["today", "tonight", "right now", "currently", "as we speak"],
    "tomorrow": ["tomorrow", "next day", "in 24 hours"],
    "this_week": ["this week", "days away", "within days", "any day now", "imminent"],
    "next_week": ["next week", "in a week", "within a week", "7 days"],
    "this_month": ["this month", "within weeks", "february", "coming weeks"],
    "next_month": ["next month", "march", "in a month", "within a month"],
    "this_quarter": ["Q1", "Q2", "by spring", "by summer", "next few months"],
    "this_year": ["this year", "2026", "by end of year", "by december"],
    "long_term": ["eventually", "someday", "years", "decade", "long term", "2027", "2028"],
    "conditional": ["if", "when", "unless", "depends on", "contingent", "should"],
}

# ==============================================================================
# NEW PREDICTION CATEGORIES
# ==============================================================================

# Assassination/Leadership targeting keywords
ASSASSINATION_KEYWORDS = {
    "khamenei_targeted": [
        "kill khamenei", "assassinate khamenei", "target khamenei",
        "supreme leader killed", "eliminate khamenei", "decapitate regime",
        "khamenei dead", "leadership strike",
    ],
    "other_leaders_targeted": [
        "assassinate", "targeted killing", "eliminate leader",
        "kill president", "Pezeshkian killed", "IRGC commander",
        "general killed", "leadership eliminated",
    ],
    "khamenei_survives": [
        "khamenei survives", "leader protected", "won't kill khamenei",
        "not targeting khamenei", "khamenei safe", "succession",
    ],
}

# War scale keywords
WAR_SCALE_KEYWORDS = {
    "major_war": [
        "major war", "large scale", "full war", "massive conflict",
        "regional war", "world war", "big war", "all out",
        "devastating", "catastrophic", "total war",
    ],
    "limited_conflict": [
        "limited war", "small scale", "contained", "surgical",
        "limited conflict", "brief exchange", "tit for tat",
        "restrained", "measured",
    ],
    "no_war": [
        "no war", "won't escalate", "avoid war", "prevent conflict",
        "peaceful", "diplomatic solution", "talks succeed",
    ],
}

# War duration keywords
WAR_DURATION_KEYWORDS = {
    "days": ["few days", "within days", "quick war", "rapid", "swift"],
    "weeks": ["few weeks", "several weeks", "weeks of fighting", "month or so"],
    "months": ["months", "prolonged", "extended conflict", "several months"],
    "years": ["years", "long war", "endless", "quagmire", "decade"],
}

# Negotiation outcome keywords
NEGOTIATION_KEYWORDS = {
    "deal_likely": [
        "deal reached", "agreement", "breakthrough", "compromise",
        "talks succeed", "diplomatic victory", "peace deal",
        "negotiations working", "good progress",
    ],
    "deal_unlikely": [
        "no deal", "talks failed", "negotiations collapsed",
        "deadlock", "impasse", "no agreement", "breakdown",
        "won't negotiate", "impossible",
    ],
    "conditional": [
        "if they agree", "depends on concessions", "requires",
        "needs to", "must accept", "only if",
    ],
}

# Regime change keywords
REGIME_CHANGE_KEYWORDS = {
    "regime_falls": [
        "regime falls", "regime change", "overthrow", "collapse",
        "topple government", "revolution succeeds", "islamic republic falls",
        "end of regime", "government collapses", "regime crumbles",
    ],
    "regime_survives": [
        "regime survives", "won't fall", "stable", "resilient",
        "regime endures", "government holds", "suppresses protests",
        "crackdown succeeds", "regime too strong",
    ],
    "uncertain": [
        "unclear", "uncertain", "could go either way", "depends",
        "hard to predict", "unpredictable",
    ],
}

# Future government keywords
FUTURE_GOVERNMENT_KEYWORDS = {
    "monarchy_return": [
        "monarchy", "pahlavi", "shah", "crown prince", "reza pahlavi",
        "constitutional monarchy", "restore monarchy", "shah returns",
    ],
    "secular_democracy": [
        "secular democracy", "democratic iran", "republic", "elections",
        "democratic government", "secular republic", "liberal democracy",
    ],
    "islamic_reform": [
        "reform", "moderate", "reformist", "islamic democracy",
        "gradual change", "evolution", "moderate islam",
    ],
    "military_rule": [
        "military government", "IRGC takeover", "junta", "military rule",
        "generals in charge", "military dictatorship",
    ],
    "chaos": [
        "chaos", "civil war", "failed state", "instability",
        "fragmentation", "warlords", "anarchy",
    ],
}

# Reza Pahlavi specific keywords
PAHLAVI_KEYWORDS = {
    "pahlavi_returns": [
        "pahlavi returns", "reza pahlavi iran", "shah returns",
        "crown prince returns", "pahlavi government", "pahlavi leads",
        "pahlavi president", "pahlavi king",
    ],
    "pahlavi_unlikely": [
        "pahlavi won't return", "no monarchy", "anti-pahlavi",
        "reject monarchy", "pahlavi irrelevant", "pahlavi exiled",
    ],
    "pahlavi_support": [
        "support pahlavi", "pahlavi popular", "want shah", "pro-monarchy",
        "long live shah", "javid shah",
    ],
}

# ==============================================================================
# PERSIAN GULF & MILITARY ACTIVITY KEYWORDS
# ==============================================================================

PERSIAN_GULF_KEYWORDS = {
    "naval_buildup": [
        "carrier", "fleet", "armada", "destroyer", "naval",
        "USS", "Abraham Lincoln", "strike group", "navy",
        "Persian Gulf", "Strait of Hormuz", "Gulf deployment",
    ],
    "blockade": [
        "blockade", "block strait", "close hormuz", "mine",
        "shipping", "tanker", "oil route", "choke point",
    ],
    "naval_clash": [
        "naval battle", "ship attack", "sink", "torpedo",
        "drone boat", "speedboat", "intercept",
    ],
}

# ==============================================================================
# EXPLOSIONS & SABOTAGE IN IRAN KEYWORDS
# ==============================================================================

EXPLOSIONS_KEYWORDS = {
    "sabotage_attack": [
        "explosion", "blast", "sabotage", "attack", "bombed",
        "Natanz", "Fordow", "Isfahan", "nuclear site",
        "mysterious explosion", "unexplained blast",
    ],
    "internal_incident": [
        "gas leak", "accident", "fire", "industrial accident",
        "pipeline explosion", "factory fire",
    ],
    "israeli_attack": [
        "Israel attack", "Mossad", "Israeli strike",
        "covert operation", "assassination",
    ],
}

# ==============================================================================
# IRAN PROTESTS & CRACKDOWN KEYWORDS
# ==============================================================================

PROTEST_CRACKDOWN_KEYWORDS = {
    "high_casualties": [
        "death toll", "killed", "massacre", "bloodshed",
        "thousands dead", "hundreds killed", "mass killing",
        "shooting protesters", "machine gun", "body bags",
    ],
    "executions": [
        "execution", "executed", "hanging", "death sentence",
        "fast trial", "revolutionary court", "death penalty",
    ],
    "regime_brutal": [
        "crackdown", "brutal", "violent suppression",
        "internet blackout", "mass arrest", "torture",
    ],
    "protest_success": [
        "protest spreading", "revolution", "regime weakening",
        "strikes", "general strike", "civil disobedience",
    ],
}

# ==============================================================================
# IRGC & BASIJ STATEMENTS KEYWORDS
# ==============================================================================

REGIME_STATEMENTS_KEYWORDS = {
    "defiant": [
        "IRGC statement", "Basij", "Revolutionary Guard",
        "will defend", "ready for war", "defeat arrogance",
        "crush enemies", "destroy Israel", "victory",
    ],
    "threatening": [
        "regional war", "attack US bases", "target Israel",
        "retaliate", "revenge", "missile response",
        "Hezbollah", "proxy attack",
    ],
    "negotiating": [
        "diplomacy", "negotiate", "talks", "peaceful solution",
        "Araghchi", "foreign minister", "dialogue",
    ],
}

# ==============================================================================
# PENTAGON PIZZA INDEX KEYWORDS
# ==============================================================================

PENTAGON_PIZZA_KEYWORDS = [
    "pentagon pizza", "pizza index", "pizza report", "pizza tracker",
    "busy night", "late night pentagon", "pizza delivery pentagon",
    "military activity indicator", "pizza surge",
]

# ==============================================================================
# ELON MUSK & STARLINK KEYWORDS (Iran-related)
# ==============================================================================

ELON_MUSK_IRAN_KEYWORDS = {
    "starlink_iran": [
        "starlink iran", "musk iran", "elon iran", "starlink protest",
        "internet iran musk", "satellite internet iran", "spacex iran",
        "restore internet iran", "bypass blackout",
    ],
    "musk_diplomacy": [
        "musk ambassador", "musk iran talks", "musk iravani",
        "musk defuse tensions", "musk channel", "musk backchannel",
        "musk negotiate iran", "elon diplomat",
    ],
    "musk_pro_war": [
        "musk attack iran", "musk supports strike", "musk war iran",
        "musk military action",
    ],
    "musk_anti_war": [
        "musk peace iran", "musk against war", "musk diplomacy iran",
        "musk negotiate", "musk de-escalate",
    ],
    "doge_iran": [
        "doge iran", "musk trump iran", "musk influence iran",
        "musk white house iran", "musk policy iran",
    ],
}

# ==============================================================================
# EPSTEIN DOCUMENTS KEYWORDS (Israel/Iran connections)
# ==============================================================================

EPSTEIN_KEYWORDS = {
    "epstein_israel": [
        "epstein israel", "epstein ehud barak", "epstein mossad",
        "epstein israeli", "epstein netanyahu", "epstein barak",
        "epstein tel aviv", "epstein jerusalem",
    ],
    "epstein_iran_contra": [
        "epstein iran contra", "epstein arms deal", "epstein weapons",
        "epstein cia", "epstein khashoggi", "epstein smuggling",
    ],
    "epstein_uae": [
        "epstein uae", "epstein dubai", "epstein abraham accords",
        "epstein emirates", "epstein gulf states", "epstein sulayem",
    ],
    "epstein_documents": [
        "epstein files", "epstein documents", "epstein release",
        "epstein leak", "epstein papers", "epstein list",
        "epstein unsealed", "epstein names",
    ],
    "epstein_kompromat": [
        "epstein kompromat", "epstein blackmail", "epstein leverage",
        "epstein intelligence", "epstein operation",
    ],
}

# ==============================================================================
# AXIOS NEWS KEYWORDS
# ==============================================================================

AXIOS_KEYWORDS = [
    "axios", "axios scoop", "axios report", "axios breaking",
    "axios exclusive", "axios iran", "axios trump", "axios witkoff",
    "axios nuclear talks", "axios military",
]

# ==============================================================================
# IRANIAN POLITICAL FIGURES KEYWORDS
# ==============================================================================

IRANIAN_FIGURES_KEYWORDS = {
    "larijani": [
        "larijani", "ali larijani", "larijani brothers",
        "security council", "snsc secretary",
    ],
    "radan": [
        "radan", "ahmad reza radan", "police chief",
        "riot police", "crackdown", "ultimatum",
    ],
    "raisi_successor": [
        "pezeshkian", "mokhber", "ghalibaf", "jalili",
        "presidential election", "new president",
    ],
    "irgc_commanders": [
        "salami", "hossein salami", "irgc commander",
        "quds force", "qaani", "esmail qaani",
    ],
    "reformists": [
        "mousavi", "karroubi", "khatami", "rouhani",
        "reformist", "green movement", "house arrest",
    ],
}

# ==============================================================================
# GEOPOLITICAL CONTEXT KEYWORDS
# ==============================================================================

GEOPOLITICAL_KEYWORDS = {
    "china_iran": [
        "china iran", "beijing tehran", "chinese support",
        "belt and road iran", "oil to china", "yuan payment",
        "trilateral", "china russia iran",
    ],
    "russia_iran": [
        "russia iran", "moscow tehran", "russian support",
        "shahed drone", "iranian drone ukraine",
        "military cooperation russia",
    ],
    "ukraine_iran": [
        "ukraine iran", "iranian drones ukraine", "zelensky iran",
        "shahed attack", "drone war", "kyiv iran",
    ],
    "india_iran": [
        "india iran", "chabahar", "indian oil", "rupee trade",
        "delhi tehran", "indian sanctions",
    ],
    "venezuela_iran": [
        "venezuela iran", "maduro khamenei", "oil swap",
        "caracas tehran", "sanctions evasion",
    ],
    "world_cup_2026": [
        "world cup 2026", "fifa iran", "world cup usa",
        "iran team", "visa ban soccer", "iran football",
    ],
    "us_navy_gulf": [
        "abraham lincoln", "carrier strike", "persian gulf navy",
        "uss", "destroyer", "tomahawk", "strait of hormuz",
        "gulf of oman", "fifth fleet",
    ],
}

# ==============================================================================
# REGIONAL ACTORS - MIDDLE EAST
# ==============================================================================

REGIONAL_ACTORS_KEYWORDS = {
    "oman": [
        "oman", "muscat", "sultan haitham", "omani mediation",
        "oman iran", "oman channel", "oman backchannel",
        "strait of hormuz oman", "gulf of oman",
    ],
    "turkey": [
        "turkey iran", "ankara tehran", "erdogan",
        "turkish mediation", "istanbul talks", "turkey nato iran",
        "turkish border", "turkey sanctions",
    ],
    "saudi_arabia": [
        "saudi iran", "riyadh tehran", "mbs iran",
        "saudi arabia", "saudi normalization", "china mediation saudi",
        "iran saudi deal", "sectarian", "sunni shia",
    ],
    "egypt": [
        "egypt iran", "cairo tehran", "sisi iran",
        "suez canal", "egypt mediation", "arab league iran",
    ],
    "uae": [
        "uae iran", "emirates iran", "dubai tehran",
        "abu dhabi", "uae sanctions", "uae trade iran",
        "abraham accords uae", "uae israel iran",
    ],
    "qatar": [
        "qatar iran", "doha tehran", "al jazeera iran",
        "qatar mediation", "al udeid", "us base qatar",
    ],
    "iraq": [
        "iraq iran", "baghdad tehran", "shia militias",
        "popular mobilization", "hashd", "iraqi border",
        "iraq mediation", "sistani",
    ],
}

REGIONAL_ACTORS_CONTEXT = {
    "oman": {
        "role": "Traditional mediator between Iran and West",
        "relationship_with_iran": "Neutral, maintains ties despite US pressure",
        "key_facts": [
            "Mediated secret US-Iran talks leading to JCPOA (2013-2015)",
            "Sultan Qaboos was trusted by both sides",
            "Sultan Haitham continues neutral policy",
            "Shares Strait of Hormuz with Iran",
            "Does not participate in anti-Iran coalitions",
        ],
        "current_role_2026": "Likely facilitating backchannel communications",
        "impact_on_conflict": "De-escalatory - provides diplomatic channel",
    },
    "turkey": {
        "role": "NATO member with Iran economic ties",
        "relationship_with_iran": "Complex - competitor but also partner",
        "key_facts": [
            "Hosting Istanbul talks (Feb 7, 2026)",
            "Major trade partner despite sanctions",
            "Both oppose Kurdish independence",
            "Erdogan critical of US/Israeli pressure on Iran",
            "Won't allow Turkish bases for Iran attack",
            "But NATO member, can't fully oppose US",
        ],
        "current_role_2026": "Mediator for nuclear talks",
        "impact_on_conflict": "De-escalatory - pushing diplomacy",
    },
    "saudi_arabia": {
        "role": "Iran's regional rival, now normalizing",
        "relationship_with_iran": "Historic enemy, recent thaw",
        "key_facts": [
            "China-brokered normalization deal (March 2023)",
            "Embassies reopened after 7 years",
            "MBS wants to reduce regional tensions",
            "Vision 2030 requires stability",
            "No longer funding anti-Iran proxies openly",
            "BUT still competes for regional influence",
        ],
        "current_role_2026": "Cautiously neutral, doesn't want war on doorstep",
        "impact_on_conflict": "Neutral - won't support Iran but won't help US attack",
    },
    "egypt": {
        "role": "Arab heavyweight, US ally",
        "relationship_with_iran": "Cold, no relations since 1979",
        "key_facts": [
            "No diplomatic relations since revolution",
            "Sisi government is pragmatic",
            "Controls Suez Canal - critical for oil shipping",
            "Part of negotiations organizing with Turkey/Qatar",
            "Doesn't want regional destabilization",
        ],
        "current_role_2026": "Behind-scenes diplomacy support",
        "impact_on_conflict": "Neutral to de-escalatory",
    },
    "uae": {
        "role": "Business hub, Abraham Accords signatory",
        "relationship_with_iran": "Economic ties despite political tension",
        "key_facts": [
            "Dubai is major Iran trade hub (despite sanctions)",
            "Large Iranian expat community",
            "Abraham Accords aligned UAE with Israel",
            "BUT UAE doesn't want war disrupting business",
            "Withdrew from Yemen coalition",
            "More pragmatic than Saudi",
        ],
        "current_role_2026": "Won't provide airspace for Iran attack",
        "impact_on_conflict": "De-escalatory - prioritizes stability",
    },
    "qatar": {
        "role": "US military host, Iran neighbor",
        "relationship_with_iran": "Maintains ties, shared gas field",
        "key_facts": [
            "Al Udeid - largest US base in Middle East",
            "Shares world's largest gas field with Iran",
            "Blockaded by Saudi/UAE (2017-2021) - Iran helped",
            "Hosts Taliban office, Hamas leaders",
            "Al Jazeera critical of all sides",
            "June 2025: Iran retaliated by hitting Qatar base",
        ],
        "current_role_2026": "Nervous about being target, pushing diplomacy",
        "impact_on_conflict": "Strongly de-escalatory",
    },
    "iraq": {
        "role": "Buffer state, Iran-aligned government",
        "relationship_with_iran": "Close, Shia-majority government",
        "key_facts": [
            "Iran has major influence via Shia militias",
            "Popular Mobilization Forces (PMF/Hashd) are Iran proxies",
            "US troops still present (~2,500)",
            "Caught between US and Iran",
            "Border with Iran is porous",
            "Would be transit route for any ground war",
        ],
        "current_role_2026": "Trying to stay neutral, failing",
        "impact_on_conflict": "Escalatory risk - potential battleground",
    },
}

# ==============================================================================
# PRO-REGIME IRANIAN VOICES KEYWORDS
# ==============================================================================

PRO_REGIME_KEYWORDS = {
    "regime_defense": [
        "iran will win", "defeat america", "islamic republic strong",
        "hezbollah victory", "axis of resistance", "resistance front",
        "zionist defeat", "western propaganda",
    ],
    "regime_rhetoric": [
        "death to america", "death to israel", "great satan",
        "islamic revolution", "imam khomeini", "velayat faqih",
        "basij volunteer", "revolutionary values",
    ],
    "regime_claims": [
        "protesters are terrorists", "foreign agents", "rioters",
        "mek terrorist", "cia plot", "regime change plot",
        "color revolution", "soft war",
    ],
}

# ==============================================================================
# IRAN PROTESTS & SOCIAL MOVEMENTS KEYWORDS
# ==============================================================================

IRAN_PROTESTS_KEYWORDS = {
    "woman_life_freedom": [
        "woman life freedom", "zan zendegi azadi", "زن زندگی آزادی",
        "jin jiyan azadi", "women's rights iran", "feminist revolution",
        "hijab protest", "compulsory hijab", "mandatory hijab",
        "morality police", "gasht ershad", "گشت ارشاد",
    ],
    "mahsa_amini": [
        "mahsa amini", "jina amini", "مهسا امینی", "ژینا امینی",
        "amini death", "amini killing", "september 2022",
        "1401 protests", "امینی", "مهسا",
    ],
    "protest_movements": [
        "iran protests", "iranian protests", "iran uprising",
        "iran revolution 2022", "iran revolution 2024", "iran revolution 2026",
        "bloody november", "آبان خونین", "december protests",
        "january protests", "nationwide protests",
    ],
    "protest_casualties": [
        "killed protesters", "protest deaths", "massacre",
        "shot protesters", "execution protesters", "hanging protesters",
        "nikta esfandani", "nika shakarami", "mohsen shekari",
        "majidreza rahnavard", "protest martyrs",
    ],
    "protest_symbols": [
        "cut hair", "burn hijab", "remove hijab",
        "baraye", "برای", "shervin hajipour",
        "white wednesday", "my stealthy freedom",
    ],
}

# ==============================================================================
# IRAN ECONOMY & CURRENCY KEYWORDS
# ==============================================================================

IRAN_ECONOMY_KEYWORDS = {
    "currency_crisis": [
        "rial crash", "rial collapse", "iranian rial",
        "dollar rate iran", "exchange rate iran", "نرخ دلار",
        "toman", "تومان", "currency devaluation",
        "black market rate", "official rate", "parallel market",
        "70000 toman", "80000 toman", "90000 toman", "100000 toman",
    ],
    "central_bank": [
        "central bank iran", "cbi iran", "بانک مرکزی",
        "farzin", "فرزین", "hemmati", "همتی",
        "seif", "سیف", "monetary policy iran",
        "foreign reserves", "gold reserves iran",
    ],
    "economic_crisis": [
        "iran inflation", "iran hyperinflation", "iran economy collapse",
        "sanctions effect", "iran poverty", "iran unemployment",
        "brain drain iran", "iran emigration",
        "economic mismanagement", "corruption iran",
    ],
    "sanctions_impact": [
        "swift ban iran", "banking sanctions", "oil sanctions",
        "secondary sanctions", "sanctions evasion",
        "hawala", "حواله", "cryptocurrency iran",
    ],
}

# ==============================================================================
# IRAN PROTESTS TIMELINE (for context)
# ==============================================================================

IRAN_PROTESTS_TIMELINE = {
    "2017_2018": "Dey protests - economic grievances, 25+ killed",
    "2019_november": "Bloody November (Aban 98) - fuel price protests, 1,500+ killed",
    "2022_september": "Mahsa Amini - Woman Life Freedom, 500+ killed, largest since 1979",
    "2024_protests": "Sporadic protests continue, regime tightens control",
    "2025_december": "New wave begins - economic crisis + regional tensions",
    "2026_january": "Massive protests - 6,000+ killed, regime crisis",
}

# ==============================================================================
# IRAN SUCCESSION & LEADERSHIP SCENARIOS
# ==============================================================================

IRAN_SUCCESSION_KEYWORDS = {
    "mojtaba_khamenei": [
        "mojtaba khamenei", "مجتبی خامنه‌ای", "khamenei son",
        "mojtaba", "مجتبی", "hereditary succession",
        "beit rahbari", "بیت رهبری", "khamenei family",
    ],
    "hassan_rouhani": [
        "hassan rouhani", "حسن روحانی", "rouhani return",
        "rouhani president", "moderate faction",
        "jcpoa architect", "nuclear deal rouhani",
    ],
    "regime_reform": [
        "regime reform", "policy change", "opening iran",
        "moderation", "reform faction", "اصلاحات",
        "change from within", "soft landing",
    ],
    "hardliner_consolidation": [
        "hardliner", "اصولگرا", "principlist",
        "jalili", "جلیلی", "ghalibaf", "قالیباف",
        "raisi successor", "جانشین رئیسی",
    ],
}

IRAN_SUCCESSION_SCENARIOS = {
    "mojtaba_khamenei": {
        "name": "Mojtaba Khamenei (Hereditary)",
        "description": "Khamenei's son takes over as Supreme Leader",
        "base_probability": 0.15,
        "factors_for": [
            "Controls Beit Rahbari (Leader's office)",
            "Has built power base in IRGC intelligence",
            "Father can arrange succession through Assembly of Experts",
            "Hardliners prefer continuity",
        ],
        "factors_against": [
            "No religious credentials (not Ayatollah)",
            "Hereditary succession contradicts revolutionary ideology",
            "Unpopular - seen as corrupt by public",
            "Other clerics may oppose",
            "If regime falls, irrelevant",
        ],
    },
    "rouhani_return": {
        "name": "Hassan Rouhani Return",
        "description": "Rouhani or moderate faction returns to prominence",
        "base_probability": 0.08,
        "factors_for": [
            "Has experience negotiating with West (JCPOA)",
            "Could offer 'soft landing' for regime",
            "Some Western preference for dealing with moderates",
            "If Khamenei dies, moderates might gain influence",
        ],
        "factors_against": [
            "Rouhani is politically marginalized",
            "Guardian Council blocks reformist candidates",
            "Hardliners control all power centers",
            "IRGC won't allow return to JCPOA-style deals",
            "Public doesn't trust 'reformists' anymore",
        ],
    },
    "regime_survives_changes_policy": {
        "name": "Regime Survives with Policy Change",
        "description": "Current regime survives but adopts new policies",
        "base_probability": 0.25,
        "possible_changes": [
            "Relax hijab enforcement",
            "Economic opening to China/Russia",
            "Tactical nuclear deal (not full JCPOA)",
            "Reduce regional proxy activities",
            "Allow limited political space",
        ],
        "factors_for": [
            "Regime has survived 45 years of crises",
            "IRGC controls economy, won't give up power",
            "China/Russia provide lifeline",
            "No organized opposition leadership",
            "Historical precedent: adapted after Iran-Iraq war",
        ],
        "factors_against": [
            "Khamenei (85) is inflexible ideologue",
            "Economic crisis is structural, not policy-fixable",
            "Population doesn't trust any reform promises",
            "US/Israel pressure won't ease with minor changes",
        ],
    },
    "hardliner_consolidation": {
        "name": "Hardliner Consolidation",
        "description": "Hardliners tighten control, no reform",
        "base_probability": 0.35,
        "likely_leaders": [
            "Saeed Jalili (current frontrunner)",
            "Mohammad Bagher Ghalibaf",
            "IRGC general (unprecedented)",
        ],
        "factors_for": [
            "Current trajectory under Raisi",
            "IRGC dominates all institutions",
            "Guardian Council blocks alternatives",
            "Crisis justifies 'security first' approach",
        ],
        "factors_against": [
            "Hardline approach not solving problems",
            "International isolation worsening",
            "Protests getting larger despite crackdown",
        ],
    },
    "regime_collapse": {
        "name": "Regime Collapse / Revolution",
        "description": "Islamic Republic falls, replaced by new system",
        "base_probability": 0.12,
        "possible_outcomes": [
            "Secular democracy (unlikely without organization)",
            "Military rule (IRGC junta)",
            "Chaos / civil war (Libya model)",
            "Pahlavi restoration (unlikely)",
            "Regional fragmentation",
        ],
    },
}

# ==============================================================================
# IRAN FUTURE SCENARIO COMPARISON KEYWORDS (Which Country Will Iran Resemble?)
# ==============================================================================

COUNTRY_COMPARISON_KEYWORDS = {
    # Iraq scenario - US invasion, regime change, chaos, sectarian conflict
    "iraq_scenario": [
        "like iraq", "another iraq", "iraq 2.0", "iraq war", "iraqi scenario",
        "saddam", "de-baathification", "sectarian", "civil war iraq",
        "occupation", "insurgency", "isis", "power vacuum iraq",
    ],
    
    # Libya scenario - NATO intervention, Gaddafi fall, failed state
    "libya_scenario": [
        "like libya", "another libya", "libya scenario", "gaddafi",
        "failed state", "warlords", "tribal conflict", "no government",
        "libya chaos", "slave markets", "nato intervention",
    ],
    
    # Syria Civil War scenario (2011-2024) - Prolonged civil war under Assad, proxy war
    "syria_civil_war": [
        "like syria civil war", "syrian civil war", "assad", "barrel bombs",
        "proxy war", "russia iran syria", "refugees crisis", "decade of war",
        "balkanization", "fragmentation syria", "aleppo", "idlib",
        "chemical weapons", "isis territory", "years of conflict",
        "prolonged war", "endless civil war", "million refugees",
    ],
    
    # Syria Post-Assad scenario (2024+) - HTS/Jolani takeover, Islamist transition
    "syria_post_assad": [
        "like new syria", "jolani", "joulani", "hts", "hayat tahrir",
        "post assad", "after assad", "syria transition", "islamist takeover",
        "syria now", "new syrian government", "syria 2024", "syria 2025",
        "syrian transition", "moderate islamist", "turkey backed",
        "rebel victory", "damascus fell", "quick collapse",
    ],
    
    # Syria general (if specific phase unclear)
    "syria_scenario": [
        "like syria", "syrian scenario", "syria model",
    ],
    
    # Afghanistan scenario - Long war, Taliban return, US withdrawal
    "afghanistan_scenario": [
        "like afghanistan", "afghan scenario", "taliban", "20 years",
        "endless war", "us withdrawal", "failed nation building",
        "graveyard of empires", "trillion dollars wasted",
    ],
    
    # Egypt scenario - Military coup, brief democracy, authoritarian return
    "egypt_scenario": [
        "like egypt", "egyptian scenario", "military coup", "sisi",
        "arab spring egypt", "muslim brotherhood", "military rule",
        "back to dictatorship", "tahrir", "brief democracy",
    ],
    
    # Tunisia scenario - Successful democratic transition (rare positive)
    "tunisia_scenario": [
        "like tunisia", "tunisian scenario", "successful transition",
        "arab spring success", "democracy works", "peaceful transition",
    ],
    
    # Russia scenario - Security state, authoritarian stability
    "russia_scenario": [
        "like russia", "russian scenario", "putin model", "security state",
        "kgb takes over", "irgc becomes government", "authoritarian stability",
        "managed democracy", "strongman rule",
    ],
    
    # Yugoslavia scenario - Breakup, ethnic conflict, Balkanization
    "yugoslavia_scenario": [
        "like yugoslavia", "balkanization", "break up iran", "ethnic conflict",
        "kurds separate", "azeris separate", "baloch", "arab regions",
        "ethnic cleansing", "partition iran",
    ],
    
    # Venezuela scenario - Economic collapse, regime survives
    "venezuela_scenario": [
        "like venezuela", "venezuelan scenario", "maduro", "economic collapse",
        "regime survives", "hyperinflation", "oil curse", "sanctions forever",
        "brain drain", "mass emigration",
    ],
    
    # North Korea scenario - Complete isolation, totalitarian survival
    "north_korea_scenario": [
        "like north korea", "north korean scenario", "kim jong", "hermit kingdom",
        "total isolation", "nuclear blackmail", "dynasty rule",
        "survive through fear", "cult of personality",
    ],
    
    # South Korea scenario - Successful development (very optimistic)
    "south_korea_scenario": [
        "like south korea", "korean miracle", "economic development",
        "democracy after dictatorship", "successful transition",
        "asian tiger", "modernization success",
    ],
    
    # 1979 Iran Revolution scenario - History repeats
    "revolution_1979_scenario": [
        "1979 again", "revolution repeats", "shah falls again",
        "history repeats", "another revolution", "cycle of revolution",
    ],
}

# ==============================================================================
# CONCURRENCY SETTINGS
# ==============================================================================

# Maximum concurrent workers for parallel operations.
# Set this based on your CPU cores. Most modern CPUs can handle 8-16 workers.
# This affects Reddit data gathering, Polymarket comment fetching, and other I/O-bound tasks.
MAX_CONCURRENT_WORKERS = 16

# ==============================================================================
# DATA GATHERING SETTINGS
# ==============================================================================

# Enable concurrent data gathering by default for faster Reddit collection.
# Reddit API rate limits are handled automatically with exponential backoff.
USE_CONCURRENT_REDDIT_GATHERING = True

TOP_POSTS_TIME_FILTER = "week"  # "all", "day", "hour", "month", "week", or "year"

# OPTIMIZED: 200 posts per subreddit (was 1000)
# With ~70 subreddits, this gives ~14,000 posts max, still plenty of coverage
MAXIMUM_POSTS_PER_SUBREDDIT = 1000

MINIMUM_COMMENT_LENGTH = 20  # Filter out very short comments
MAXIMUM_COMMENT_LENGTH = 10000  # Filter out extremely long comments

# ==============================================================================
# REDDIT COLLECTION PERFORMANCE TUNING
# ==============================================================================
#
# OPTIMIZED for speed while maintaining accuracy:
# - Reduced per-post/subreddit limits (was 10000, now 500-2000)
# - Focus on top comments for signal quality
# - Recent comment feed for freshness

# Per-post cap: 100 comments per post is enough for top discussions
MAX_COMMENTS_PER_POST = 100

# Per-subreddit cap: 2000 comments captures most relevant content
MAX_COMMENTS_PER_SUBREDDIT = 2000

# Recent comments feed - captures fresh discussions without deep traversal
INCLUDE_RECENT_COMMENT_FEED = True
RECENT_COMMENTS_PER_SUBREDDIT = 10000

# Sorting for submission comments: "top" for highest signal
SUBMISSION_COMMENT_SORT = "top"

# replace_more limit: 0 = no deep tree expansion (much faster)
REPLACE_MORE_LIMIT = 0

# ==============================================================================
# ANALYSIS SETTINGS
# ==============================================================================

# ---------------------------------------------------------------------------
# PRE-FILTER: Iran Relevance Anchors
# ---------------------------------------------------------------------------
# A comment MUST contain at least one of these to be analysed.  This replaces
# the old approach of running every comment through the classifier and ending
# up with 99.5% neutral (i.e. irrelevant) results.
#
# Tier 1 – Iran-specific terms (single keyword = relevant)
IRAN_RELEVANCE_ANCHORS = [
    # Country / region
    "iran", "iranian", "tehran", "persia", "persian",
    "islamic republic of iran",
    # Leadership / politics
    "khamenei", "pezeshkian", "araghchi", "raisi", "rouhani", "zarif",
    "soleimani", "ayatollah", "supreme leader",
    # Military / security
    "irgc", "revolutionary guard", "quds force", "basij", "sepah",
    # Nuclear programme
    "jcpoa", "nuclear deal", "natanz", "fordow", "bushehr",
    "iran nuclear", "iranian nuclear",
    # Geography
    "strait of hormuz", "hormuz", "bandar abbas", "persian gulf",
    # Opposition
    "pahlavi", "reza pahlavi", "mek", "rajavi",
    # Hyphened / compound
    "us-iran", "iran-us", "iran war", "iran attack", "iran strike",
    "attack iran", "strike iran", "bomb iran", "invade iran",
    "iran sanction", "iran negotiat", "iran deal", "iran diplomacy",
    "iran conflict", "iran military", "iran missile",
    "iran proxy", "iran nuclear", "iran regime",
    # Witkoff negotiations
    "witkoff",
]

# Subreddits where ALL comments are considered relevant (Iran-focused subs)
IRAN_RELEVANT_SUBREDDITS = {
    "iran", "iranian", "newiran", "iranpolitics", "proiran",
    "shiapolitics",
}

# ---------------------------------------------------------------------------
# Zero-shot classification model
# ---------------------------------------------------------------------------
CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
USE_GPU = False  # Set to True if you have CUDA GPU

# Zero-shot speed/quality controls
ZERO_SHOT_MIN_TEXT_LENGTH = 30   # shorter texts can still carry opinion
# Keyword gate DISABLED — the Iran pre-filter ensures relevance already.
ZERO_SHOT_KEYWORDS = []
# Cap = 0 means UNLIMITED.  Safe because the pre-filter limits to ~10K.
ZERO_SHOT_MAX_COMMENTS = 0
# Workers kept for back-compat.  Phase-2 now uses sentence-embedding
# similarity (all-MiniLM-L6-v2, ~80 MB) instead of the old BART-MNLI
# zero-shot pipeline (~1.5 GB).  ~500-1000× faster on CPU.
ZERO_SHOT_MAX_WORKERS = 1

# ---------------------------------------------------------------------------
# Analysis runtime tuning  (Phase 1 = threads/regex, Phase 2 = single-proc ZS)
# ---------------------------------------------------------------------------
ANALYSIS_MAX_WORKERS = 14  # Thread count for Phase 1 regex pass
ANALYSIS_PROGRESS_SECONDS = 5  # Log every 5s so user sees movement
ANALYSIS_PROGRESS_MIN_COUNT = 200  # Log after every 200 comments too

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.7
MEDIUM_CONFIDENCE_THRESHOLD = 0.5

# Minimum sample size for reliable statistics
MINIMUM_SAMPLE_SIZE = 30

# ==============================================================================
# POLYMARKET COMPARISON
# ==============================================================================

POLYMARKET_MARKETS = [
    # US Strike Markets (granular timeline)
    {
        "name": "US strikes Iran by February 3, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-03"
    },
    {
        "name": "US strikes Iran by February 4, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-04"
    },
    {
        "name": "US strikes Iran by February 5, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-05"
    },
    {
        "name": "US strikes Iran by February 6, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-06"
    },
    {
        "name": "US strikes Iran by February 13, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-13"
    },
    {
        "name": "US strikes Iran by February 20, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-20"
    },
    {
        "name": "US strikes Iran by February 28, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-02-28"
    },
    {
        "name": "US strikes Iran by March 31, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-03-31"
    },
    {
        "name": "US strikes Iran by June 30, 2026",
        "url": "https://polymarket.com/event/us-strikes-iran-by",
        "type": "us_strike",
        "deadline": "2026-06-30"
    },
    # Israel Strike Markets
    {
        "name": "Israel strikes Iran by February 28, 2026",
        "url": "https://polymarket.com/event/israel-strikes-iran-by-february-28-2026",
        "type": "israel_strike",
        "deadline": "2026-02-28"
    },
    # Iran Retaliation Markets
    {
        "name": "Iran strikes Israel by February 28, 2026",
        "url": "https://polymarket.com/event/iran-strike-on-israel-by",
        "type": "iran_strike_israel",
        "deadline": "2026-02-28"
    },
    {
        "name": "Iran strikes US military by February 28, 2026",
        "url": "https://polymarket.com/event/iran-strike-on-us-military-by-february-28",
        "type": "iran_strike_us",
        "deadline": "2026-02-28"
    },
]

# Polymarket APIs
# - Gamma API: market discovery/metadata + comments (public, read-only)
# - Data API: leaderboard and user positions (public, read-only)
POLYMARKET_GAMMA_API_BASE = "https://gamma-api.polymarket.com"
POLYMARKET_DATA_API_BASE = "https://data-api.polymarket.com"

# Comment fetching (Gamma /comments)
# Note: These limits are intentionally high to satisfy "analyze MANY comments".
# The fetcher applies pagination + de-duplication + polite rate limiting.
POLYMARKET_COMMENTS_PAGE_SIZE = 200
POLYMARKET_MAX_COMMENTS_PER_MARKET = 5000
POLYMARKET_MAX_TOTAL_COMMENTS = 30000
POLYMARKET_COMMENTS_ORDER = "createdAt"
POLYMARKET_COMMENTS_ASCENDING = False
POLYMARKET_COMMENTS_HOLDERS_ONLY = False
POLYMARKET_COMMENTS_GET_POSITIONS = False

# Safety: do NOT estimate or score assassination / individual-death outcomes.
# This project focuses on market-implied strike timelines and broad geopolitical scenarios.
ENABLE_INDIVIDUAL_HARM_ANALYSIS = False

# Basic polite rate-limiting between paginated requests
# Keep this small but non-zero to reduce the chance of HTTP 429.
POLYMARKET_RATE_LIMIT_SLEEP_SEC = 0.10

# ==============================================================================
# CROSS-MARKET SMART MONEY ANALYSIS
# ==============================================================================
# Search queries used to discover related Polymarket events for cross-market
# trader intelligence.  For each qualified high-win-rate / high-PnL trader we
# fetch ALL their open positions and categorize them into these buckets.

CROSS_MARKET_SEARCH_QUERIES = [
    # Geopolitical – Iran / Middle East
    "Iran", "Iran nuclear", "Iran strike", "US Iran",
    "Israel Iran", "Hezbollah", "Houthi",
    # Geopolitical – Russia / Ukraine
    "Russia", "Ukraine", "Russia Ukraine war", "Crimea",
    "Zelensky", "Putin",
    # Geopolitical – China / Taiwan
    "China", "Taiwan", "China Taiwan", "Xi Jinping",
    "South China Sea",
    # Gold & Commodities
    "Gold price", "Gold", "XAUUSD", "silver price",
    "oil price", "crude oil",
    # Bitcoin & Crypto
    "Bitcoin", "Bitcoin price", "BTC", "Ethereum", "ETH",
    "crypto",
    # US Stocks & Economy
    "S&P 500", "stock market", "recession", "Fed rate",
    "NASDAQ", "Dow Jones", "US economy",
    # Broader geopolitics
    "World War", "NATO", "nuclear war",
]

# How we categorize a market's question text into a bucket.
# The first matching category wins (order matters).
CROSS_MARKET_CATEGORIES = {
    "iran":           ["iran", "jcpoa", "khamenei", "tehran", "irgc",
                       "persian gulf", "hormuz", "witkoff", "pezeshkian"],
    "israel":         ["israel", "netanyahu", "idf", "hamas", "gaza",
                       "hezbollah", "west bank", "mossad"],
    "russia_ukraine": ["russia", "ukraine", "putin", "zelensky", "crimea",
                       "donbas", "nato", "moscow", "kyiv"],
    "china":          ["china", "taiwan", "xi jinping", "beijing",
                       "south china sea", "pla"],
    "gold":           ["gold", "xauusd", "precious metal", "bullion",
                       "gold price"],
    "bitcoin":        ["bitcoin", "btc", "crypto", "ethereum", "eth",
                       "digital asset"],
    "us_stocks":      ["s&p", "sp500", "nasdaq", "dow jones", "stock market",
                       "fed rate", "recession", "us economy", "interest rate"],
    "oil":            ["oil price", "crude oil", "brent", "wti", "opec",
                       "oil supply"],
}

# Leaderboard categories to pull traders from (Polymarket Data API).
# Each category adds more traders; duplicates are de-duped by wallet.
CROSS_MARKET_LEADERBOARD_CATEGORIES = [
    ("POLITICS", "MONTH", 50),     # geopolitics / war traders
    ("POLITICS", "ALL", 50),       # all-time politics PnL leaders
    ("CRYPTO", "MONTH", 40),       # crypto-heavy traders
    ("ALL", "MONTH", 40),          # overall top traders
]

# Minimum thresholds for a trader to qualify
CROSS_MARKET_MIN_WIN_RATE = 0.65       # 65 %
CROSS_MARKET_MIN_SAMPLE_N = 10         # at least 10 closed positions
CROSS_MARKET_MIN_PNL_OVERRIDE = 250_000  # $250K PnL bypasses win-rate check
CROSS_MARKET_MAX_TRADERS = 60          # how many qualified traders max
CROSS_MARKET_MAX_POSITIONS_PER_TRADER = 100  # positions to fetch per trader

# ==============================================================================
# REPORT SETTINGS
# ==============================================================================

# Optional Persian-language sources (RSS/API).
# These feeds are only used by the news aggregator when enabled.
INCLUDE_PERSIAN_LANGUAGE_SOURCES = True

# Public RSS feeds (no API key). Note: availability may vary by region/network.
PERSIAN_RSS_FEEDS = [
    {"name": "BBC Persian", "url": "https://feeds.bbci.co.uk/persian/rss.xml"},
    {"name": "DW Persian", "url": "https://rss.dw.com/xml/rss-per-all"},
    {"name": "Radio Farda", "url": "https://www.radiofarda.com/api/zrqiteuuir"},
    {"name": "VOA Persian", "url": "https://ir.voanews.com/api/zprieeuuir"},
    {"name": "Iran International", "url": "https://www.iranintl.com/feed"},
]

# Optional English-language RSS sources (no API key). These are best-effort:
# if a feed blocks automated requests in your network, it will be skipped silently.
INCLUDE_ENGLISH_RSS_SOURCES = True
ENGLISH_RSS_FEEDS = [
    # Axios (if reachable)
    {"name": "Axios (main)", "url": "https://www.axios.com/feeds/feed.rss"},
    {"name": "Axios (api)", "url": "https://api.axios.com/feed/"},
]

REPORT_LANGUAGE = "en"  # "en" or "fa" for Persian
INCLUDE_RAW_COMMENTS = False  # Whether to include sample comments in report
MAX_SAMPLE_COMMENTS = 20  # Maximum sample comments to include

# ==============================================================================
# CACHE SETTINGS
# ==============================================================================

CACHE_DIRECTORY = "cache"
AUTO_CACHE = True  # Automatically cache results after each step

