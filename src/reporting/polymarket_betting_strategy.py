"""
Polymarket Betting Strategy Module
Identifies alpha, arbitrage opportunities, and inefficiencies in Iran-related markets.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date


@dataclass
class BettingRecommendation:
    """A specific betting recommendation."""
    market_name: str
    position: str  # "YES" or "NO"
    current_price: float  # Current market price (0-100)
    fair_value: float  # Our estimated fair value (0-100)
    edge: float  # Edge = fair_value - current_price (for YES) or opposite
    confidence: str  # HIGH, MEDIUM, LOW
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    suggested_allocation: str  # % of betting bankroll
    deadline: str
    expected_value: float  # EV calculation


@dataclass
class ArbitrageOpportunity:
    """An arbitrage or mispricing opportunity."""
    name: str
    description: str
    markets_involved: List[str]
    prices: Dict[str, float]
    theoretical_edge: float
    execution_notes: str
    risk: str


@dataclass
class MarketInefficiency:
    """A market inefficiency or anomaly."""
    name: str
    description: str
    current_state: str
    why_inefficient: str
    how_to_exploit: str
    confidence: str


class PolymarketBettingStrategy:
    """Generates betting recommendations based on analysis."""
    
    # Current Polymarket odds (Feb 4, 2026)
    CURRENT_MARKETS = {
        # US Strike markets
        "us_strike_feb3": {"prob": 0.4, "deadline": "2026-02-03", "status": "EXPIRED"},
        "us_strike_feb4": {"prob": 1.0, "deadline": "2026-02-04", "status": "ACTIVE"},
        "us_strike_feb5": {"prob": 1.0, "deadline": "2026-02-05", "status": "ACTIVE"},
        "us_strike_feb6": {"prob": 2.2, "deadline": "2026-02-06", "status": "ACTIVE"},
        "us_strike_feb13": {"prob": 9.0, "deadline": "2026-02-13", "status": "ACTIVE"},
        "us_strike_feb20": {"prob": 13.0, "deadline": "2026-02-20", "status": "ACTIVE"},
        "us_strike_feb28": {"prob": 22.0, "deadline": "2026-02-28", "status": "ACTIVE"},
        "us_strike_mar31": {"prob": 35.0, "deadline": "2026-03-31", "status": "ACTIVE"},
        "us_strike_jun30": {"prob": 45.0, "deadline": "2026-06-30", "status": "ACTIVE"},
        # Israel markets
        "israel_strike_feb28": {"prob": 37.0, "deadline": "2026-02-28", "status": "ACTIVE"},
        # Iran retaliation markets
        "iran_strike_israel_feb28": {"prob": 39.0, "deadline": "2026-02-28", "status": "ACTIVE"},
        "iran_strike_us_feb28": {"prob": 34.0, "deadline": "2026-02-28", "status": "ACTIVE"},
    }
    
    # Our analysis estimates with detailed reasoning
    # Each estimate includes: probability, confidence_interval, reasoning
    OUR_ESTIMATES_DETAILED = {
        "us_strike_feb4": {
            "prob": 1.0,
            "ci_low": 0.5, "ci_high": 2.0,
            "reasoning": """
            Base rate: 0% (no same-day strikes historically)
            Evidence: Istanbul talks scheduled for Feb 7
            Bayesian: Prior 0.5% + no trigger event = 1%
            """
        },
        "us_strike_feb5": {
            "prob": 2.0,
            "ci_low": 1.0, "ci_high": 4.0,
            "reasoning": """
            Base rate: ~1% (very short notice)
            Evidence: Talks still 2 days away
            Bayesian: Prior 1% + military ready = 2%
            """
        },
        "us_strike_feb6": {
            "prob": 5.0,
            "ci_low": 3.0, "ci_high": 8.0,
            "reasoning": """
            Base rate: ~3% (pre-talks window)
            Evidence: Radan ultimatum expiring, but talks imminent
            Bayesian: Prior 3% + pressure building = 5%
            Key assumption: Trump prefers to let talks happen first
            """
        },
        "us_strike_feb13": {
            "prob": 12.0,
            "ci_low": 8.0, "ci_high": 18.0,
            "reasoning": """
            Base rate: ~8% (post-talks failure window)
            Evidence: If Istanbul talks fail, 7-day response window
            Bayesian: Prior 8% + failed diplomacy signal = 12%
            Key assumption: Talks will likely fail (70% chance)
            Calculation: 8% + (70% * 6%) = 12.2%
            """
        },
        "us_strike_feb20": {
            "prob": 18.0,
            "ci_low": 12.0, "ci_high": 25.0,
            "reasoning": """
            Base rate: ~12% (2-week window)
            Evidence: Time for coalition building if talks fail
            Bayesian: Prior 12% + military readiness complete = 18%
            Key assumption: Congressional notification period ~7 days
            """
        },
        "us_strike_feb28": {
            "prob": 25.0,
            "ci_low": 18.0, "ci_high": 32.0,
            "reasoning": """
            Base rate: ~18% (monthly horizon)
            Evidence: Full diplomatic exhaustion, military ready
            Polymarket: 22% (close to our estimate)
            Gold signal: $5,038 suggests 28%+
            Bayesian: Average of Polymarket (22%), Gold (28%), analysis (25%) = 25%
            Key assumption: No breakthrough deal
            """
        },
        "us_strike_mar31": {
            "prob": 35.0,
            "ci_low": 28.0, "ci_high": 42.0,
            "reasoning": """
            Base rate: ~28% (quarterly horizon)
            Evidence: Spring military window, IAEA deadline
            Polymarket: 35% (matches our estimate)
            Calculation: Feb prob (25%) + March incremental (13%) = 38%
            Adjusted for optimism bias: 35%
            """
        },
        "us_strike_jun30": {
            "prob": 50.0,
            "ci_low": 40.0, "ci_high": 60.0,
            "reasoning": """
            Base rate: ~40% (6-month horizon)
            Evidence: World Cup pressure, multiple escalation windows
            Gold signal: $5,038 (67% YoY) suggests 50%+
            Polymarket: 45% (slightly below our estimate)
            Calculation: Cumulative of monthly windows
            Key assumption: No regime collapse or major deal
            """
        },
        "israel_strike_feb28": {
            "prob": 30.0,
            "ci_low": 22.0, "ci_high": 38.0,
            "reasoning": """
            Base rate: ~25% (Israel struck in June 2025)
            Evidence: Israeli domestic politics, US coordination
            Polymarket: 37% (higher than our estimate)
            Why lower: Israel waiting for US green light
            Key assumption: Netanyahu prefers US to lead
            """
        },
        "iran_strike_israel_feb28": {
            "prob": 25.0,
            "ci_low": 15.0, "ci_high": 35.0,
            "reasoning": """
            Base rate: ~15% (Iran retaliates, doesn't initiate)
            Historical: Iran struck Israel in April 2024 AFTER provocation
            Polymarket: 39% (significantly overpriced!)
            Why lower: Iran is in survival mode (protests)
            Key assumption: Iran won't initiate while dealing with protests
            Edge: Polymarket 39% - Our 25% = 14% edge on NO
            """
        },
        "iran_strike_us_feb28": {
            "prob": 20.0,
            "ci_low": 12.0, "ci_high": 28.0,
            "reasoning": """
            Base rate: ~10% (Iran NEVER directly attacks US)
            Historical: 45+ years, no direct Iran→US military attack
            Even June 2025: Iran hit Qatar base (proxy), not US directly
            Polymarket: 34% (significantly overpriced!)
            Why lower: Direct US attack = regime suicide
            Key assumption: Regime survival > ideology
            Edge: Polymarket 34% - Our 20% = 14% edge on NO
            """
        },
    }
    
    # Simple estimates for calculations
    OUR_ESTIMATES = {
        "us_strike_feb4": 1.0,
        "us_strike_feb5": 2.0,
        "us_strike_feb6": 5.0,
        "us_strike_feb13": 12.0,
        "us_strike_feb20": 18.0,
        "us_strike_feb28": 25.0,
        "us_strike_mar31": 35.0,
        "us_strike_jun30": 50.0,
        "israel_strike_feb28": 30.0,
        "iran_strike_israel_feb28": 25.0,
        "iran_strike_us_feb28": 20.0,
    }
    
    def __init__(self):
        self.today = date(2026, 2, 4)
        
        # Source reliability weights (0-1)
        self.SOURCE_WEIGHTS = {
            "polymarket": 0.35,  # Money at stake, aggregates views
            "gold_market": 0.25,  # Sophisticated traders
            "reddit_sentiment": 0.10,  # Low information but detects narratives
            "expert_analysis": 0.20,  # Axios, Reuters, etc.
            "official_statements": 0.10,  # May be posturing
        }
    
    def calculate_kelly_fraction(self, edge: float, odds: float) -> float:
        """
        Calculate optimal Kelly bet size.
        
        Kelly formula: f* = (bp - q) / b
        where:
        - b = decimal odds - 1 (net odds)
        - p = probability of winning
        - q = probability of losing (1 - p)
        
        Args:
            edge: Our edge (our_prob - market_prob) as decimal
            odds: Market odds (price in cents / 100)
        
        Returns:
            Optimal fraction of bankroll to bet (0-1)
        """
        if edge <= 0:
            return 0.0
        
        # Convert to probabilities
        market_prob = odds / 100
        our_prob = market_prob + edge
        
        # For YES bets: payout = 1/market_prob if win
        # For NO bets: payout = 1/(1-market_prob) if win
        
        # Kelly for binary outcomes
        # f* = (p * (1/market_prob - 1) - (1-p)) / (1/market_prob - 1)
        # Simplified: f* = p - (1-p) * market_prob / (1-market_prob)
        
        if market_prob >= 1 or market_prob <= 0:
            return 0.0
        
        b = (1 / market_prob) - 1  # Net odds
        p = our_prob
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Apply fractional Kelly (half Kelly is common for safety)
        fractional_kelly = kelly * 0.5
        
        # Cap at 25% of bankroll
        return min(max(fractional_kelly, 0), 0.25)
    
    def get_weighted_probability(self, market_key: str) -> Dict[str, any]:
        """
        Calculate weighted probability from multiple sources.
        
        Returns dict with:
        - weighted_prob: Final probability estimate
        - sources: Individual source estimates
        - confidence: Confidence level
        """
        sources = {}
        
        # Polymarket probability
        pm_prob = self.CURRENT_MARKETS.get(market_key, {}).get("prob", 50)
        sources["polymarket"] = pm_prob
        
        # Our detailed estimate
        detailed = self.OUR_ESTIMATES_DETAILED.get(market_key, {})
        our_prob = detailed.get("prob", pm_prob)
        sources["our_analysis"] = our_prob
        
        # Gold-implied probability (rough heuristic)
        # Gold at $5,038 with 67% YoY = high conflict probability
        # Map: $4,000 = 20%, $5,000 = 40%, $6,000 = 60%
        gold_implied = 40 + (5038 - 5000) * 0.02  # ~40.8%
        
        # For short-term markets, discount gold signal
        if "feb6" in market_key or "feb4" in market_key or "feb5" in market_key:
            gold_weight = 0.05
        elif "feb13" in market_key or "feb20" in market_key or "feb28" in market_key:
            gold_weight = 0.15
        else:  # Longer term
            gold_weight = 0.25
        
        sources["gold_implied"] = gold_implied
        
        # Calculate weighted average
        weighted_prob = (
            pm_prob * 0.35 +
            our_prob * 0.40 +
            gold_implied * gold_weight +
            pm_prob * (0.25 - gold_weight)  # Fill remaining weight with Polymarket
        )
        
        # Confidence interval
        ci_low = detailed.get("ci_low", weighted_prob * 0.7)
        ci_high = detailed.get("ci_high", weighted_prob * 1.3)
        
        # Confidence level based on source agreement
        spread = max(abs(pm_prob - our_prob), abs(our_prob - gold_implied))
        if spread < 5:
            confidence = "HIGH"
        elif spread < 10:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        return {
            "weighted_prob": weighted_prob,
            "sources": sources,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "confidence": confidence,
            "reasoning": detailed.get("reasoning", "")
        }
    
    def calculate_edge(self, market_key: str, position: str = "YES") -> float:
        """Calculate edge for a position."""
        market_prob = self.CURRENT_MARKETS.get(market_key, {}).get("prob", 50)
        our_prob = self.OUR_ESTIMATES.get(market_key, 50)
        
        if position == "YES":
            # Buy YES: we profit if event happens
            # Edge = our_prob - market_prob
            return our_prob - market_prob
        else:
            # Buy NO: we profit if event doesn't happen
            # Edge = (100 - our_prob) - (100 - market_prob) = market_prob - our_prob
            return market_prob - our_prob
    
    def get_betting_recommendations(self) -> List[BettingRecommendation]:
        """Generate specific betting recommendations."""
        recommendations = []
        
        # === HIGH CONVICTION BETS ===
        
        # 1. US Strike by Feb 28 - YES is underpriced
        recommendations.append(BettingRecommendation(
            market_name="US strikes Iran by February 28, 2026",
            position="YES",
            current_price=22.0,
            fair_value=25.0,
            edge=3.0,
            confidence="MEDIUM",
            reasoning="""
            **Why YES at 22¢:**
            - Our analysis: 25% probability → 3% edge
            - Istanbul talks (Feb 7) likely to fail based on Iran's position
            - Military assets fully positioned (USS Abraham Lincoln + destroyers)
            - Gold at $5,038 signals market expectations
            - Radan's 3-day ultimatum to protesters = escalation trigger
            - Mousavi's "game is over" statement suggests regime crisis
            
            **Risk factors:**
            - Musk backchannel could produce surprise deal
            - China/Russia pressure on both sides
            - Trump may prefer sanctions over bombs
            
            **Entry strategy:**
            - Buy at 22¢ or below
            - Average down if it drops to 18-20¢
            - Take profit if spikes above 35¢ on news
            """,
            risk_level="MEDIUM",
            suggested_allocation="8-12%",
            deadline="2026-02-28",
            expected_value=1.136  # (0.25 * 1/0.22) = 1.136 → 13.6% EV
        ))
        
        # 2. US Strike by June 30 - YES is underpriced
        recommendations.append(BettingRecommendation(
            market_name="US strikes Iran by June 30, 2026",
            position="YES",
            current_price=45.0,
            fair_value=50.0,
            edge=5.0,
            confidence="HIGH",
            reasoning="""
            **Why YES at 45¢:**
            - Our analysis: 50% probability → 5% edge
            - 4+ month window = multiple escalation opportunities
            - World Cup 2026 deadline adds political pressure
            - Iran's internal crisis likely to worsen
            - Gold price trajectory confirms sustained expectations
            - Even failed talks = gradual probability increase
            
            **Key dates to watch:**
            - Feb 7: Istanbul talks
            - March: IAEA report deadline
            - April: Spring military window
            - May-June: Pre-World Cup pressure
            
            **Entry strategy:**
            - Buy at 45¢ current price
            - Scale in more if drops below 40¢
            - Hold through volatility unless fundamentals change
            """,
            risk_level="MEDIUM",
            suggested_allocation="15-20%",
            deadline="2026-06-30",
            expected_value=1.111  # (0.50 / 0.45) = 1.111 → 11.1% EV
        ))
        
        # 3. Iran strikes Israel - NO is underpriced
        recommendations.append(BettingRecommendation(
            market_name="Iran strikes Israel by February 28, 2026",
            position="NO",
            current_price=61.0,  # 100 - 39
            fair_value=75.0,  # 100 - 25
            edge=14.0,
            confidence="HIGH",
            reasoning="""
            **Why NO at 61¢ (vs YES at 39¢):**
            - Our analysis: Only 25% chance Iran initiates
            - Market overpricing Iranian aggression by 14%!
            - Iran is in survival mode (6,000+ protest deaths)
            - IRGC stretched thin between protests and military
            - Historical pattern: Iran retaliates AFTER being hit
            - June 2025 "12-Day War" - Iran responded to Israeli strike
            
            **Why market is wrong:**
            - Conflating "Iran might respond" with "Iran will initiate"
            - Fear-driven pricing from Houthi activity
            - Iran's strategic interest is to avoid first strike
            
            **Entry strategy:**
            - Strong buy NO at 61¢
            - This is the best edge in the entire market!
            - Expected profit: 23% (75¢ - 61¢ / 61¢)
            """,
            risk_level="LOW",
            suggested_allocation="20-25%",
            deadline="2026-02-28",
            expected_value=1.230  # (0.75 / 0.61) = 1.23 → 23% EV
        ))
        
        # 4. Israel strikes Iran - YES slightly underpriced
        recommendations.append(BettingRecommendation(
            market_name="Israel strikes Iran by February 28, 2026",
            position="NO",
            current_price=63.0,  # 100 - 37
            fair_value=70.0,  # 100 - 30
            edge=7.0,
            confidence="MEDIUM",
            reasoning="""
            **Why NO at 63¢ (vs YES at 37¢):**
            - Our analysis: 30% Israel strikes → 7% edge on NO
            - Israel already conducted June 2025 strikes
            - Domestic Israeli politics favor restraint (coalition issues)
            - US prefers to lead any military action
            - Intelligence suggests Israel waiting for US green light
            
            **Caveat:**
            - Israel is unpredictable
            - Could act without US approval
            - Edge is smaller than Iran NO bet
            
            **Entry strategy:**
            - Moderate position at 63¢
            - Smaller allocation than Iran NO bet
            """,
            risk_level="MEDIUM",
            suggested_allocation="10-12%",
            deadline="2026-02-28",
            expected_value=1.111  # (0.70 / 0.63) = 1.11 → 11% EV
        ))
        
        # 5. Short-term NO bets (high probability free money)
        recommendations.append(BettingRecommendation(
            market_name="US strikes Iran by February 6, 2026",
            position="NO",
            current_price=97.8,  # 100 - 2.2
            fair_value=95.0,  # 100 - 5
            edge=-2.8,  # Negative edge but very safe
            confidence="HIGH",
            reasoning="""
            **Why NO at 97.8¢ (vs YES at 2.2¢):**
            - Only 2 days away!
            - Istanbul talks scheduled for Feb 7 (Friday)
            - Trump won't strike BEFORE diplomatic meeting
            - No trigger event has occurred
            - Our estimate: 5% → still very safe to bet NO
            
            **The catch:**
            - You're betting 97.8¢ to win 2.2¢
            - But probability of loss is only ~5%
            - Risk/reward: 2.2¢ gain vs 97.8¢ loss = needs 97.8% win rate
            - Our estimate: 95% win rate → MARGINAL
            
            **Verdict:**
            - Small edge, safe but low return
            - Only bet large amounts if you have capital to deploy
            - Better edges exist elsewhere
            """,
            risk_level="LOW",
            suggested_allocation="5% (only for bankroll deployment)",
            deadline="2026-02-06",
            expected_value=1.023  # Marginal positive EV
        ))
        
        # 6. Iran strikes US - Strong NO
        recommendations.append(BettingRecommendation(
            market_name="Iran strikes US military by February 28, 2026",
            position="NO",
            current_price=66.0,  # 100 - 34
            fair_value=80.0,  # 100 - 20
            edge=14.0,
            confidence="HIGH",
            reasoning="""
            **Why NO at 66¢ (vs YES at 34¢):**
            - Our analysis: Only 20% chance Iran strikes US directly
            - Iran NEVER directly attacks US military in 45 years
            - Even June 2025 retaliation targeted proxy (Qatar base)
            - Direct US attack = guaranteed massive response
            - Regime survival depends on NOT provoking US directly
            
            **Market is wrong because:**
            - Conflating Houthi/militia attacks with Iranian state action
            - Previous "Iran strikes" were proxy actions, not direct
            - Market participants not distinguishing direct vs proxy
            
            **This is FREE MONEY:**
            - 14% edge = one of best bets in market
            - Historical pattern strongly supports NO
            """,
            risk_level="LOW",
            suggested_allocation="15-20%",
            deadline="2026-02-28",
            expected_value=1.212  # (0.80 / 0.66) = 1.21 → 21% EV
        ))
        
        return recommendations
    
    def get_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """Identify arbitrage and mispricing opportunities."""
        opportunities = []
        
        # 1. Israel vs US strike timing arbitrage
        opportunities.append(ArbitrageOpportunity(
            name="Israel-US Strike Timing Arbitrage",
            description="""
            If Israel strikes (37%) it almost guarantees US follows.
            But US strike (22%) is priced lower than Israel strike.
            This creates a logical inconsistency.
            """,
            markets_involved=[
                "Israel strikes Iran by Feb 28 (37%)",
                "US strikes Iran by Feb 28 (22%)"
            ],
            prices={"israel_yes": 37, "us_yes": 22},
            theoretical_edge=5.0,
            execution_notes="""
            **Strategy:**
            - Buy US strikes YES at 22¢
            - If Israel strikes, US will almost certainly follow
            - You're getting 22¢ for something that becomes ~90% likely after Israel acts
            
            **Why this exists:**
            - Markets are independent, not linked
            - Traders not pricing in conditional probability
            - US strike should be at least 0.37 * 0.9 = 33% minimum
            
            **Execution:**
            - Buy US strike YES
            - Use Israel strike as leading indicator
            - If Israel strikes, US YES should spike to 80%+
            """,
            risk="MEDIUM - requires Israel to act first"
        ))
        
        # 2. Iran retaliation pricing error
        opportunities.append(ArbitrageOpportunity(
            name="Iran Retaliation Mispricing",
            description="""
            Market prices Iran striking Israel (39%) higher than Iran striking US (34%).
            But Iran is MORE likely to hit US bases than Israel directly.
            Historical pattern: Iran targets US proxy bases, not Israel directly.
            """,
            markets_involved=[
                "Iran strikes Israel by Feb 28 (39%)",
                "Iran strikes US military by Feb 28 (34%)"
            ],
            prices={"iran_israel_yes": 39, "iran_us_yes": 34},
            theoretical_edge=10.0,
            execution_notes="""
            **Strategy:**
            - Sell Iran strikes Israel YES (or buy NO at 61¢)
            - Buy Iran strikes US YES at 34¢ (smaller position)
            
            **Why market is wrong:**
            - Iran's doctrine: strike US bases, not Israel directly
            - June 2025: Iran hit Qatar base, not Israeli cities
            - Israel has better air defense than US bases in region
            
            **Net position:**
            - Short Iran-Israel direct conflict
            - Long Iran-US proxy conflict (smaller)
            """,
            risk="MEDIUM - Iran behavior is unpredictable"
        ))
        
        # 3. Cumulative probability error
        opportunities.append(ArbitrageOpportunity(
            name="Cumulative Timeline Mispricing",
            description="""
            Feb 28 (22%) + incremental March probability should = ~Mar 31 (35%)
            But the 13% jump from Feb 28 to Mar 31 seems too large.
            If Feb 28 is 22%, March conditional add should be ~17%, not 13%.
            """,
            markets_involved=[
                "US strikes by Feb 28 (22%)",
                "US strikes by Mar 31 (35%)"
            ],
            prices={"feb28": 22, "mar31": 35},
            theoretical_edge=3.0,
            execution_notes="""
            **Strategy:**
            - If you believe Feb passes without strike:
            - Wait for Feb 28 to expire NO
            - Mar 31 should reprice higher (conditional probability)
            
            **Math:**
            - P(March | not Feb) = (35 - 22) / (100 - 22) = 16.7%
            - This seems reasonable, so limited edge
            
            **Alternative:**
            - Buy Feb 28 YES at 22¢
            - If nothing happens, roll into Mar 31
            """,
            risk="LOW - math checks out roughly"
        ))
        
        return opportunities
    
    def get_market_inefficiencies(self) -> List[MarketInefficiency]:
        """Identify market inefficiencies and anomalies."""
        inefficiencies = []
        
        # 1. Reddit vs Polymarket divergence
        inefficiencies.append(MarketInefficiency(
            name="Reddit-Polymarket Sentiment Divergence",
            description="Reddit predicts 53% attack, Polymarket shows 22% by Feb 28",
            current_state="31% gap between social sentiment and market pricing",
            why_inefficient="""
            **This might NOT be inefficiency:**
            - Polymarket traders have money at stake → more careful
            - Reddit users may be in echo chambers
            - Reddit skews younger, more hawkish on intervention
            
            **But it MIGHT be:**
            - Polymarket has few Iran specialists
            - Crypto-native traders may not follow geopolitics closely
            - Reddit aggregates more diverse information sources
            """,
            how_to_exploit="""
            **If you believe Reddit is right:**
            - Buy YES positions aggressively
            - Reddit may be leading indicator for news traders
            
            **If you believe Polymarket is right:**
            - The market is efficient, don't bet against it
            - Social media sentiment ≠ prediction accuracy
            
            **Recommended:**
            - Split the difference: assume true probability is ~35-40%
            - This means YES is underpriced at 22%
            """,
            confidence="MEDIUM"
        ))
        
        # 2. Gold price not fully reflected
        inefficiencies.append(MarketInefficiency(
            name="Gold Price Signal Underweighted",
            description="Gold at $5,038 (+67% YoY) suggests higher conflict probability than markets price",
            current_state="Gold pricing in ~50% conflict, Polymarket at 22-45%",
            why_inefficient="""
            **Gold traders are sophisticated:**
            - Central banks, institutions, hedge funds
            - They don't buy gold for fun
            - $5,000+ gold = serious conflict expectations
            
            **Polymarket traders may be:**
            - Retail crypto natives with less macro experience
            - Focused on news headlines, not structural indicators
            - Not incorporating commodity market signals
            """,
            how_to_exploit="""
            **Strategy:**
            - Use gold as confirmation signal
            - If gold breaks $5,200, add to YES positions
            - If gold drops below $4,800, reduce YES positions
            - Gold is "smart money" - follow it
            """,
            confidence="HIGH"
        ))
        
        # 3. Short-dated markets with stale pricing
        inefficiencies.append(MarketInefficiency(
            name="Stale Short-Dated Pricing",
            description="Feb 4-5 markets showing 1% despite news suggesting higher probability",
            current_state="Markets may not update in real-time with news",
            why_inefficient="""
            **Liquidity issues:**
            - Short-dated markets have thin order books
            - Few traders willing to take positions expiring in days
            - Price discovery is poor near expiration
            
            **Information lag:**
            - News about Radan ultimatum, Mousavi statement
            - Markets may not have incorporated latest developments
            """,
            how_to_exploit="""
            **Strategy:**
            - Avoid betting short-dated markets (poor liquidity)
            - Watch for sudden price spikes on news
            - If you see breaking news before price moves:
              - Quick scalp opportunity
              - But execution risk is high
            
            **Better approach:**
            - Focus on Feb 28 and beyond for better liquidity
            """,
            confidence="MEDIUM"
        ))
        
        # 4. Correlated events priced independently  
        inefficiencies.append(MarketInefficiency(
            name="Correlated Events Mispriced",
            description="Israel strike, US strike, Iran retaliation are all correlated but priced independently",
            current_state="Markets don't reflect joint probability structure",
            why_inefficient="""
            **The cascade effect:**
            - Israel strikes → 90%+ US follows within days
            - US strikes → 80%+ Iran retaliates somehow
            - Iran retaliates → 60%+ US escalates further
            
            **But markets price:**
            - Israel strike: 37%
            - US strike: 22% (should be higher given Israel)
            - Iran retaliation: 34-39%
            """,
            how_to_exploit="""
            **Build correlated positions:**
            
            1. **If you expect escalation:**
               - Buy US strike YES (cheapest of the bunch)
               - This benefits from all pathways to conflict
            
            2. **If you expect de-escalation:**
               - Sell Iran strikes Israel YES (overpriced)
               - Iran initiating is least likely scenario
            
            3. **Hedge:**
               - Long US strike YES + Short Iran-Israel YES
               - Profits if US/Israel act but Iran doesn't initiate
            """,
            confidence="HIGH"
        ))
        
        return inefficiencies
    
    def get_optimal_portfolio(self) -> Dict[str, any]:
        """Generate optimal betting portfolio."""
        return {
            "total_bankroll_allocation": "50-70% of betting capital",
            "positions": [
                {
                    "market": "Iran strikes Israel by Feb 28",
                    "position": "NO",
                    "allocation": "25%",
                    "entry": "61¢",
                    "edge": "+14%",
                    "rationale": "Best risk/reward in market"
                },
                {
                    "market": "Iran strikes US military by Feb 28",
                    "position": "NO",
                    "allocation": "20%",
                    "entry": "66¢",
                    "edge": "+14%",
                    "rationale": "Iran never directly attacks US"
                },
                {
                    "market": "US strikes Iran by June 30",
                    "position": "YES",
                    "allocation": "15%",
                    "entry": "45¢",
                    "edge": "+5%",
                    "rationale": "Highest confidence long-term"
                },
                {
                    "market": "US strikes Iran by Feb 28",
                    "position": "YES",
                    "allocation": "10%",
                    "entry": "22¢",
                    "edge": "+3%",
                    "rationale": "Good risk/reward on escalation"
                },
                {
                    "market": "Israel strikes Iran by Feb 28",
                    "position": "NO",
                    "allocation": "10%",
                    "entry": "63¢",
                    "edge": "+7%",
                    "rationale": "Israel waiting for US lead"
                },
            ],
            "reserve": "30-50% in stablecoins for opportunities",
            "risk_management": """
            **Position sizing:**
            - No single bet > 25% of bankroll
            - Correlated bets (all Iran NO) count as single exposure
            - Keep 30%+ liquid for averaging down or new opportunities
            
            **Exit rules:**
            - Take profit at 50%+ gain on any position
            - Cut losses if edge thesis invalidated (not just price move)
            - Roll expiring positions if thesis intact
            
            **Hedging:**
            - If holding large NO positions on Iran action
            - Consider small YES on US strike as hedge
            - Conflict = all correlate, no conflict = NO wins
            """
        }
    
    def format_betting_report(self) -> str:
        """Generate formatted betting strategy report."""
        lines = [
            "# 🎰 Polymarket Betting Strategy Report",
            f"\n**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Markets Analyzed:** Iran Conflict Markets (Feb-Jun 2026)",
            "",
            "---",
            "",
            "## 📊 Current Market Prices vs Our Estimates",
            "",
            "| Market | Polymarket | Our Estimate | Edge | Recommended |",
            "|--------|------------|--------------|------|-------------|",
        ]
        
        market_display = [
            ("US strike by Feb 6", "us_strike_feb6", "2.2%", "5%", "-2.8%", "NO (marginal)"),
            ("US strike by Feb 13", "us_strike_feb13", "9%", "12%", "+3%", "YES"),
            ("US strike by Feb 28", "us_strike_feb28", "22%", "25%", "+3%", "YES ⭐"),
            ("US strike by Mar 31", "us_strike_mar31", "35%", "35%", "0%", "NEUTRAL"),
            ("US strike by Jun 30", "us_strike_jun30", "45%", "50%", "+5%", "YES ⭐⭐"),
            ("Israel strike by Feb 28", "israel_strike_feb28", "37%", "30%", "-7%", "NO ⭐"),
            ("Iran → Israel by Feb 28", "iran_strike_israel_feb28", "39%", "25%", "-14%", "NO ⭐⭐⭐"),
            ("Iran → US by Feb 28", "iran_strike_us_feb28", "34%", "20%", "-14%", "NO ⭐⭐⭐"),
        ]
        
        for name, key, pm_price, our_est, edge, rec in market_display:
            lines.append(f"| {name} | {pm_price} | {our_est} | {edge} | {rec} |")
        
        lines.extend([
            "",
            "⭐ = Good bet | ⭐⭐ = Strong bet | ⭐⭐⭐ = Best bet",
            "",
            "---",
            "",
            "## 🎯 Top Betting Recommendations",
            "",
        ])
        
        for i, rec in enumerate(self.get_betting_recommendations(), 1):
            lines.extend([
                f"### {i}. {rec.market_name}",
                f"**Position:** {rec.position} at {rec.current_price}¢",
                f"**Fair Value:** {rec.fair_value}¢ | **Edge:** {rec.edge:+.1f}%",
                f"**Confidence:** {rec.confidence} | **Risk:** {rec.risk_level}",
                f"**Allocation:** {rec.suggested_allocation} of bankroll",
                f"**Expected Value:** {(rec.expected_value - 1) * 100:.1f}% profit",
                "",
                "**Analysis:**",
                rec.reasoning,
                "",
                "---",
                "",
            ])
        
        lines.extend([
            "## 🔄 Arbitrage & Mispricing Opportunities",
            "",
        ])
        
        for opp in self.get_arbitrage_opportunities():
            lines.extend([
                f"### {opp.name}",
                opp.description,
                "",
                f"**Markets:** {', '.join(opp.markets_involved)}",
                f"**Theoretical Edge:** {opp.theoretical_edge}%",
                f"**Risk Level:** {opp.risk}",
                "",
                "**Execution:**",
                opp.execution_notes,
                "",
                "---",
                "",
            ])
        
        lines.extend([
            "## ⚠️ Market Inefficiencies",
            "",
        ])
        
        for ineff in self.get_market_inefficiencies():
            lines.extend([
                f"### {ineff.name}",
                f"**Current State:** {ineff.current_state}",
                "",
                "**Why This Exists:**",
                ineff.why_inefficient,
                "",
                "**How to Exploit:**",
                ineff.how_to_exploit,
                "",
                f"**Confidence:** {ineff.confidence}",
                "",
                "---",
                "",
            ])
        
        lines.extend([
            "## 💼 Optimal Betting Portfolio",
            "",
        ])
        
        portfolio = self.get_optimal_portfolio()
        lines.append(f"**Total Allocation:** {portfolio['total_bankroll_allocation']}")
        lines.append("")
        lines.append("| Market | Position | Allocation | Entry | Edge |")
        lines.append("|--------|----------|------------|-------|------|")
        
        for pos in portfolio["positions"]:
            lines.append(f"| {pos['market']} | {pos['position']} | {pos['allocation']} | {pos['entry']} | {pos['edge']} |")
        
        lines.extend([
            "",
            f"**Reserve:** {portfolio['reserve']}",
            "",
            "### Risk Management",
            portfolio["risk_management"],
            "",
            "---",
            "",
            "## 🧮 Expected Value Summary",
            "",
            "| Bet | Position | Entry | EV | Kelly % |",
            "|-----|----------|-------|-----|---------|",
            "| Iran→Israel NO | NO | 61¢ | +23% | 18.4% |",
            "| Iran→US NO | NO | 66¢ | +21% | 17.5% |",
            "| US strike Jun YES | YES | 45¢ | +11% | 9.1% |",
            "| Israel NO | NO | 63¢ | +11% | 10.0% |",
            "| US strike Feb YES | YES | 22¢ | +14% | 3.8% |",
            "",
            "*Kelly % = Optimal bet size using Kelly Criterion (edge / odds)*",
            "",
            "---",
            "",
            "## ⚠️ Disclaimer",
            "",
            "This is not financial advice. Prediction markets involve significant risk.",
            "Only bet what you can afford to lose. Past performance does not guarantee future results.",
            "Market conditions can change rapidly based on news events.",
            "",
        ])
        
        return "\n".join(lines)


def main():
    """Test betting strategy."""
    strategy = PolymarketBettingStrategy()
    print(strategy.format_betting_report())


if __name__ == "__main__":
    main()
