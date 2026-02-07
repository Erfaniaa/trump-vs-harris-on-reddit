"""
Reasoning Framework Module
Provides structured reasoning templates and probability calibration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class EvidenceItem:
    """A piece of evidence with weight and direction."""
    description: str
    source: str
    reliability: str  # HIGH, MEDIUM, LOW
    direction: str  # SUPPORTS_ATTACK, AGAINST_ATTACK, NEUTRAL
    weight: float  # 0-1 based on reliability
    
    def to_markdown(self) -> str:
        direction_emoji = {
            "SUPPORTS_ATTACK": "🔴",
            "AGAINST_ATTACK": "🟢",
            "NEUTRAL": "⚪"
        }
        return f"- {direction_emoji.get(self.direction, '⚪')} **{self.source}** ({self.reliability}): {self.description}"


@dataclass
class BayesianUpdate:
    """A Bayesian probability update."""
    prior: float
    evidence: str
    likelihood_ratio: float  # P(evidence|hypothesis) / P(evidence|~hypothesis)
    posterior: float
    explanation: str


@dataclass
class ProbabilityEstimate:
    """A calibrated probability estimate with full reasoning."""
    event: str
    point_estimate: float
    confidence_interval: Tuple[float, float]
    confidence_level: str
    
    # Reasoning components
    base_rate: float
    base_rate_reasoning: str
    
    evidence_for: List[EvidenceItem]
    evidence_against: List[EvidenceItem]
    
    bayesian_updates: List[BayesianUpdate]
    
    key_assumptions: List[str]
    sensitivity_analysis: Dict[str, float]  # assumption -> new estimate if wrong
    
    sources_consulted: List[str]
    source_agreement: str  # STRONG, MODERATE, WEAK
    
    final_reasoning: str


class ReasoningFramework:
    """Framework for structured probabilistic reasoning."""
    
    # Historical base rates for calibration
    BASE_RATES = {
        "us_strikes_iran": {
            "ever_before_2025": 0.0,  # Never happened
            "after_june_2025": 0.15,  # June 2025 strikes set precedent
            "monthly_during_crisis": 0.08,  # Rough estimate
            "reasoning": """
            Historical: US never directly struck Iran before June 2025.
            June 2025 strikes were response to Iran's attack on Israel.
            This creates a new baseline - precedent is now set.
            Monthly baseline during heightened crisis: ~8%
            """
        },
        "israel_strikes_iran": {
            "historical_annual": 0.15,  # Pre-2024
            "post_2024": 0.35,  # After April 2024 direct strikes
            "monthly_during_crisis": 0.12,
            "reasoning": """
            Israel struck Iran directly in April 2024 (first time).
            Struck again in June 2025 as part of 12-Day War.
            New baseline is much higher than historical.
            """
        },
        "iran_initiates_attack": {
            "historical": 0.02,  # Very rare
            "vs_israel_direct": 0.05,  # April 2024 was exception
            "vs_us_direct": 0.001,  # Essentially never
            "reasoning": """
            Iran almost never initiates direct attacks.
            April 2024 was first direct strike on Israel in 45 years.
            Iran has NEVER directly attacked US military assets.
            Iran prefers proxy warfare (Hezbollah, Houthis, militias).
            """
        },
        "regime_collapse": {
            "base_annual": 0.05,  # Low historically
            "during_protests_2022": 0.15,  # Mahsa Amini period
            "during_current_crisis": 0.25,  # 2026 crisis
            "reasoning": """
            Islamic Republic has survived 45+ years of crises.
            BUT current situation is unprecedented combination:
            - Massive protests (6,000+ killed in Jan 2026)
            - Economic collapse (Rial at historic lows)
            - External military pressure
            - Loss of regional allies (Hezbollah weakened)
            
            Protest timeline shows escalation:
            - 2017-18: Dey protests, 25+ killed
            - 2019 Nov: Bloody November, 1,500+ killed  
            - 2022 Sep: Mahsa Amini/Woman Life Freedom, 500+ killed
            - 2026 Jan: Current wave, 6,000+ killed
            
            Each wave is larger and regime response more brutal.
            """
        }
    }
    
    # Iran Protests Context
    IRAN_PROTESTS_CONTEXT = {
        "mahsa_amini_2022": {
            "date": "September 2022 (1401)",
            "trigger": "Death of Mahsa (Jina) Amini in morality police custody",
            "slogan": "Woman, Life, Freedom (Zan, Zendegi, Azadi)",
            "casualties": "500+ killed, 20,000+ arrested",
            "duration": "4+ months of sustained protests",
            "significance": """
            Largest protests since 1979 Revolution.
            First time women-led movement in Iran.
            Spread to all 31 provinces.
            United ethnic groups (Kurds, Baloch, Persians, Azeris).
            International solidarity movement.
            Regime responded with extreme violence.
            """
        },
        "bloody_november_2019": {
            "date": "November 2019 (Aban 1398)",
            "trigger": "Sudden 300% fuel price increase",
            "casualties": "1,500+ killed (Reuters estimate)",
            "duration": "1 week of intense protests",
            "significance": """
            Deadliest crackdown since 1979.
            Internet shutdown for 1 week.
            Showed regime willing to use extreme force.
            Economic grievances + political anger combined.
            """
        },
        "current_2026": {
            "date": "December 2025 - February 2026",
            "trigger": "Rial collapse + regional war fears + continued repression",
            "casualties": "6,000+ killed (estimated)",
            "duration": "Ongoing (2+ months)",
            "significance": """
            Most deadly protest wave in Islamic Republic history.
            Coincides with US/Israel military threats.
            Regime simultaneously fighting internal + external enemies.
            IRGC/Basij stretched between protest control and military defense.
            """
        }
    }
    
    # Iran Economic Context
    IRAN_ECONOMIC_CONTEXT = {
        "currency_collapse": {
            "2018_rate": "42,000 Rial per USD (official)",
            "2022_rate": "320,000 Rial per USD",
            "2024_rate": "550,000 Rial per USD",
            "2026_rate": "850,000+ Rial per USD (black market)",
            "significance": """
            Rial lost 95%+ of value since 2018.
            Middle class savings wiped out.
            Imports extremely expensive.
            Food/medicine shortages.
            Fuels emigration ("brain drain").
            """
        },
        "central_bank_governors": {
            "valiollah_seif": "2013-2018, sanctioned by US",
            "abdolnaser_hemmati": "2018-2021, tried to stabilize, failed",
            "ali_saleh_abadi": "2021-2022, brief tenure",
            "mohammadreza_farzin": "2022-present, crisis manager",
            "significance": """
            Frequent CBI governor changes indicate policy chaos.
            All governors face impossible task:
            - Sanctions prevent normal banking
            - Inflation spiraling
            - Multiple exchange rates create arbitrage
            - Government prints money to cover deficits
            """
        },
        "sanctions_impact": {
            "oil_exports_2018": "2.5 million barrels/day",
            "oil_exports_2020": "0.3 million barrels/day",
            "oil_exports_2024": "1.5 million barrels/day (China)",
            "significance": """
            Oil revenue is regime lifeline.
            Sanctions reduced exports 80%+ at lowest point.
            China is now main buyer at discount.
            "Shadow fleet" tankers evade sanctions.
            """
        }
    }
    
    # Source reliability rankings
    SOURCE_RELIABILITY = {
        "polymarket": {"reliability": 0.75, "reasoning": "Money at stake, aggregates views"},
        "gold_market": {"reliability": 0.70, "reasoning": "Sophisticated traders, long-term signal"},
        "official_statements": {"reliability": 0.50, "reasoning": "May be posturing, but signal intent"},
        "reuters_axios": {"reliability": 0.65, "reasoning": "Professional journalism, fact-checked"},
        "reddit_sentiment": {"reliability": 0.25, "reasoning": "Useful for narratives, poor for probabilities"},
        "twitter_x": {"reliability": 0.20, "reasoning": "Noise, bots, but sometimes early signals"},
        "expert_analysts": {"reliability": 0.60, "reasoning": "Knowledgeable but often wrong on timing"},
    }
    
    def __init__(self):
        self.estimates = {}
    
    def get_base_rate(self, event_type: str) -> Tuple[float, str]:
        """Get historical base rate for an event type."""
        if event_type in self.BASE_RATES:
            data = self.BASE_RATES[event_type]
            # Use the most relevant rate
            if "monthly_during_crisis" in data:
                return data["monthly_during_crisis"], data["reasoning"]
            return list(data.values())[0], data.get("reasoning", "")
        return 0.10, "No historical data available, using 10% default"
    
    def calculate_bayesian_update(
        self,
        prior: float,
        evidence: str,
        likelihood_given_true: float,
        likelihood_given_false: float
    ) -> BayesianUpdate:
        """
        Perform Bayesian update.
        
        P(H|E) = P(E|H) * P(H) / P(E)
        where P(E) = P(E|H) * P(H) + P(E|~H) * P(~H)
        """
        p_e = likelihood_given_true * prior + likelihood_given_false * (1 - prior)
        
        if p_e == 0:
            posterior = prior
        else:
            posterior = (likelihood_given_true * prior) / p_e
        
        lr = likelihood_given_true / likelihood_given_false if likelihood_given_false > 0 else float('inf')
        
        explanation = f"""
        Prior: {prior*100:.1f}%
        P(evidence | attack happens): {likelihood_given_true*100:.0f}%
        P(evidence | attack doesn't happen): {likelihood_given_false*100:.0f}%
        Likelihood ratio: {lr:.2f}
        Posterior: {posterior*100:.1f}%
        Shift: {(posterior-prior)*100:+.1f}%
        """
        
        return BayesianUpdate(
            prior=prior,
            evidence=evidence,
            likelihood_ratio=lr,
            posterior=posterior,
            explanation=explanation.strip()
        )
    
    def aggregate_sources(self, source_estimates: Dict[str, float]) -> Tuple[float, str]:
        """
        Aggregate estimates from multiple sources using reliability weighting.
        
        Args:
            source_estimates: Dict of source_name -> probability estimate
        
        Returns:
            (weighted_average, explanation)
        """
        total_weight = 0
        weighted_sum = 0
        
        explanation_parts = ["**Source Aggregation:**"]
        
        for source, estimate in source_estimates.items():
            if source in self.SOURCE_RELIABILITY:
                weight = self.SOURCE_RELIABILITY[source]["reliability"]
            else:
                weight = 0.30  # Default weight
            
            weighted_sum += estimate * weight
            total_weight += weight
            explanation_parts.append(f"- {source}: {estimate:.0f}% (weight: {weight:.2f})")
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
        else:
            weighted_avg = sum(source_estimates.values()) / len(source_estimates)
        
        explanation_parts.append(f"**Weighted Average: {weighted_avg:.1f}%**")
        
        return weighted_avg, "\n".join(explanation_parts)
    
    def assess_source_agreement(self, source_estimates: Dict[str, float]) -> Tuple[str, str]:
        """
        Assess how much sources agree with each other.
        
        Returns:
            (agreement_level, explanation)
        """
        if len(source_estimates) < 2:
            return "N/A", "Only one source available"
        
        values = list(source_estimates.values())
        spread = max(values) - min(values)
        avg = sum(values) / len(values)
        
        if spread <= 5:
            agreement = "STRONG"
            explanation = f"Sources agree within 5% (spread: {spread:.1f}%)"
        elif spread <= 15:
            agreement = "MODERATE"
            explanation = f"Sources moderately agree (spread: {spread:.1f}%)"
        else:
            agreement = "WEAK"
            highest = max(source_estimates, key=source_estimates.get)
            lowest = min(source_estimates, key=source_estimates.get)
            explanation = f"Sources disagree significantly. {highest} says {source_estimates[highest]:.0f}%, {lowest} says {source_estimates[lowest]:.0f}%"
        
        return agreement, explanation
    
    def create_probability_estimate(
        self,
        event: str,
        event_type: str,
        source_estimates: Dict[str, float],
        evidence_for: List[EvidenceItem],
        evidence_against: List[EvidenceItem],
        key_assumptions: List[str]
    ) -> ProbabilityEstimate:
        """Create a full probability estimate with reasoning."""
        
        # Get base rate
        base_rate, base_reasoning = self.get_base_rate(event_type)
        
        # Aggregate sources
        weighted_avg, agg_explanation = self.aggregate_sources(source_estimates)
        
        # Assess agreement
        agreement, agreement_explanation = self.assess_source_agreement(source_estimates)
        
        # Calculate Bayesian updates for key evidence
        bayesian_updates = []
        current_prob = base_rate
        
        # Update for military deployment evidence
        if any("carrier" in e.description.lower() or "military" in e.description.lower() 
               for e in evidence_for):
            update = self.calculate_bayesian_update(
                prior=current_prob,
                evidence="USS Abraham Lincoln carrier group deployed to Gulf",
                likelihood_given_true=0.90,  # Very likely if attack planned
                likelihood_given_false=0.30   # Sometimes deployed without attack
            )
            bayesian_updates.append(update)
            current_prob = update.posterior
        
        # Update for diplomatic talks evidence
        if any("talk" in e.description.lower() or "negotiat" in e.description.lower() 
               for e in evidence_against):
            update = self.calculate_bayesian_update(
                prior=current_prob,
                evidence="Istanbul diplomatic talks scheduled",
                likelihood_given_true=0.40,  # Might still attack after talks fail
                likelihood_given_false=0.70   # More likely if no attack planned
            )
            bayesian_updates.append(update)
            current_prob = update.posterior
        
        # Final estimate combines Bayesian posterior with source aggregation
        point_estimate = (current_prob * 100 + weighted_avg) / 2
        
        # Confidence interval based on source agreement
        if agreement == "STRONG":
            ci_width = 5
        elif agreement == "MODERATE":
            ci_width = 10
        else:
            ci_width = 15
        
        confidence_interval = (
            max(0, point_estimate - ci_width),
            min(100, point_estimate + ci_width)
        )
        
        # Sensitivity analysis
        sensitivity = {}
        for assumption in key_assumptions:
            # Rough heuristic: each assumption being wrong shifts estimate by 5-10%
            sensitivity[assumption] = point_estimate + ((-1) ** len(assumption) % 2) * 7
        
        # Final reasoning
        final_reasoning = f"""
## Reasoning for: {event}

### Base Rate Analysis
{base_reasoning}
Starting point: {base_rate*100:.1f}%

### Evidence Summary
**Supporting attack ({len(evidence_for)} items):**
{chr(10).join(e.to_markdown() for e in evidence_for)}

**Against attack ({len(evidence_against)} items):**
{chr(10).join(e.to_markdown() for e in evidence_against)}

### Source Aggregation
{agg_explanation}

{agreement_explanation}

### Bayesian Updates
{chr(10).join(u.explanation for u in bayesian_updates) if bayesian_updates else "No significant updates applied."}

### Key Assumptions
{chr(10).join(f"- {a}" for a in key_assumptions)}

### Final Estimate
**{point_estimate:.1f}%** (range: {confidence_interval[0]:.0f}%-{confidence_interval[1]:.0f}%)

Confidence: {agreement} (based on source agreement)
"""
        
        return ProbabilityEstimate(
            event=event,
            point_estimate=point_estimate,
            confidence_interval=confidence_interval,
            confidence_level=agreement,
            base_rate=base_rate,
            base_rate_reasoning=base_reasoning,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            bayesian_updates=bayesian_updates,
            key_assumptions=key_assumptions,
            sensitivity_analysis=sensitivity,
            sources_consulted=list(source_estimates.keys()),
            source_agreement=agreement,
            final_reasoning=final_reasoning
        )
    
    def generate_iran_conflict_estimates(self) -> Dict[str, ProbabilityEstimate]:
        """Generate comprehensive estimates for Iran conflict scenarios."""
        
        estimates = {}
        
        # Common evidence items
        carrier_evidence = EvidenceItem(
            description="USS Abraham Lincoln carrier strike group + 3 destroyers deployed to Gulf",
            source="Pentagon",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.8
        )
        
        gold_evidence = EvidenceItem(
            description="Gold at $5,038/oz (+67% YoY) - highest since 1979",
            source="Commodity markets",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.7
        )
        
        talks_evidence = EvidenceItem(
            description="Istanbul talks scheduled for Feb 7 (Witkoff + Araghchi)",
            source="Axios",
            reliability="HIGH",
            direction="AGAINST_ATTACK",
            weight=0.7
        )
        
        protests_evidence = EvidenceItem(
            description="6,000+ protesters killed in Jan 2026, worst since 1979",
            source="Human Rights Watch",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.6
        )
        
        mahsa_legacy_evidence = EvidenceItem(
            description="Woman Life Freedom movement (2022) weakened regime legitimacy; current protests are continuation",
            source="Historical analysis",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.5
        )
        
        currency_evidence = EvidenceItem(
            description="Rial at 850,000/USD (95% loss since 2018), economic collapse fueling protests",
            source="Exchange markets",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.5
        )
        
        regime_brutality_evidence = EvidenceItem(
            description="Escalating violence: 25 killed (2017) → 1,500 (2019) → 500 (2022) → 6,000+ (2026)",
            source="Historical pattern",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.6
        )
        
        china_russia_evidence = EvidenceItem(
            description="China-Russia-Iran trilateral alliance signed Jan 2026",
            source="Reuters",
            reliability="HIGH",
            direction="AGAINST_ATTACK",
            weight=0.5
        )
        
        musk_evidence = EvidenceItem(
            description="Elon Musk backchannel diplomacy with Iran UN ambassador",
            source="Axios",
            reliability="MEDIUM",
            direction="AGAINST_ATTACK",
            weight=0.4
        )
        
        # Regional actors evidence
        turkey_mediation_evidence = EvidenceItem(
            description="Turkey hosting Istanbul talks (Feb 7), Erdogan pushing diplomacy",
            source="Turkish government",
            reliability="HIGH",
            direction="AGAINST_ATTACK",
            weight=0.6
        )
        
        oman_backchannel_evidence = EvidenceItem(
            description="Oman facilitating backchannel communications (traditional mediator role)",
            source="Diplomatic sources",
            reliability="MEDIUM",
            direction="AGAINST_ATTACK",
            weight=0.4
        )
        
        saudi_normalization_evidence = EvidenceItem(
            description="Saudi-Iran normalization (2023) - MBS doesn't want regional war",
            source="Saudi policy",
            reliability="HIGH",
            direction="AGAINST_ATTACK",
            weight=0.5
        )
        
        uae_no_airspace_evidence = EvidenceItem(
            description="UAE won't provide airspace for Iran attack - prioritizes business stability",
            source="Regional analysis",
            reliability="MEDIUM",
            direction="AGAINST_ATTACK",
            weight=0.4
        )
        
        qatar_nervous_evidence = EvidenceItem(
            description="Qatar (US base host) nervous after June 2025 Iranian retaliation - pushing de-escalation",
            source="Qatar policy",
            reliability="HIGH",
            direction="AGAINST_ATTACK",
            weight=0.5
        )
        
        iraq_risk_evidence = EvidenceItem(
            description="Iraq as potential battleground - Iran proxies (PMF) vs US troops",
            source="Military analysis",
            reliability="HIGH",
            direction="SUPPORTS_ATTACK",
            weight=0.4
        )
        
        # US Strike by Feb 28
        estimates["us_strike_feb28"] = self.create_probability_estimate(
            event="US strikes Iran by February 28, 2026",
            event_type="us_strikes_iran",
            source_estimates={
                "polymarket": 22.0,
                "gold_market": 28.0,
                "reddit_sentiment": 53.0,
                "expert_analysts": 25.0,
            },
            evidence_for=[
                carrier_evidence, 
                gold_evidence, 
                protests_evidence,
                mahsa_legacy_evidence,
                currency_evidence,
                regime_brutality_evidence,
            ],
            evidence_against=[
                talks_evidence, 
                china_russia_evidence, 
                musk_evidence,
                turkey_mediation_evidence,
                oman_backchannel_evidence,
                saudi_normalization_evidence,
                uae_no_airspace_evidence,
                qatar_nervous_evidence,
            ],
            key_assumptions=[
                "Istanbul talks will fail (70% confidence)",
                "Trump prefers military action over more sanctions",
                "Israel won't act unilaterally before US decides",
                "Iran won't make major concession on nuclear program",
                "Protest movement continues despite crackdown",
                "Rial continues to collapse, fueling unrest",
                "Regional states won't provide bases/airspace (complicates logistics)",
                "Saudi-Iran normalization holds (reduces regional support for attack)",
            ]
        )
        
        # Regime collapse probability
        estimates["regime_collapse_2026"] = self.create_probability_estimate(
            event="Iranian regime collapses or major leadership change in 2026",
            event_type="regime_collapse",
            source_estimates={
                "polymarket": 0.0,  # No direct market
                "reddit_sentiment": 65.0,  # High optimism
                "expert_analysts": 20.0,  # Skeptical
            },
            evidence_for=[
                protests_evidence,
                mahsa_legacy_evidence,
                currency_evidence,
                regime_brutality_evidence,
                EvidenceItem(
                    description="Mousavi (reformist leader) says 'the game is over', calls for transition",
                    source="Mousavi statement",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.7
                ),
            ],
            evidence_against=[
                EvidenceItem(
                    description="Regime survived 45+ years of crises including Iran-Iraq war",
                    source="Historical analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.8
                ),
                EvidenceItem(
                    description="IRGC controls economy, has strong incentive to maintain power",
                    source="Structural analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.7
                ),
                china_russia_evidence,
            ],
            key_assumptions=[
                "Protests continue despite brutal crackdown",
                "Economic situation doesn't improve",
                "No major external military intervention",
                "IRGC remains unified (no splits)",
                "Khamenei (85) doesn't die naturally",
            ]
        )
        
        # Iran Leadership Succession Scenarios
        estimates["mojtaba_khamenei_succession"] = self.create_probability_estimate(
            event="Mojtaba Khamenei becomes Supreme Leader (if Khamenei dies/incapacitated)",
            event_type="regime_collapse",  # Using same base rate logic
            source_estimates={
                "expert_analysts": 35.0,
                "reddit_sentiment": 20.0,
            },
            evidence_for=[
                EvidenceItem(
                    description="Controls Beit Rahbari (Leader's office) and IRGC intelligence",
                    source="Iran analysts",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.6
                ),
                EvidenceItem(
                    description="Khamenei (85) can arrange succession through Assembly of Experts",
                    source="Constitutional analysis",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.5
                ),
            ],
            evidence_against=[
                EvidenceItem(
                    description="No religious credentials - not an Ayatollah, lacks clerical legitimacy",
                    source="Religious hierarchy",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.7
                ),
                EvidenceItem(
                    description="Hereditary succession contradicts revolutionary anti-monarchy ideology",
                    source="Ideological analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.6
                ),
                EvidenceItem(
                    description="Deeply unpopular - seen as corrupt by Iranian public",
                    source="Public sentiment",
                    reliability="MEDIUM",
                    direction="AGAINST_ATTACK",
                    weight=0.5
                ),
            ],
            key_assumptions=[
                "Khamenei dies or becomes incapacitated",
                "Assembly of Experts follows Khamenei's wishes",
                "IRGC supports Mojtaba",
                "No regime collapse before succession",
            ]
        )
        
        estimates["rouhani_return"] = self.create_probability_estimate(
            event="Hassan Rouhani or moderate faction returns to power",
            event_type="regime_collapse",
            source_estimates={
                "expert_analysts": 8.0,
                "reddit_sentiment": 15.0,
            },
            evidence_for=[
                EvidenceItem(
                    description="Has experience negotiating with West (JCPOA architect)",
                    source="Historical record",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.5
                ),
                EvidenceItem(
                    description="Could offer 'soft landing' deal that West might accept",
                    source="Diplomatic analysis",
                    reliability="MEDIUM",
                    direction="SUPPORTS_ATTACK",
                    weight=0.4
                ),
            ],
            evidence_against=[
                EvidenceItem(
                    description="Rouhani is politically marginalized, banned from Assembly of Experts",
                    source="Iran politics",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.8
                ),
                EvidenceItem(
                    description="Guardian Council systematically blocks reformist candidates",
                    source="Electoral history",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.8
                ),
                EvidenceItem(
                    description="Iranian public no longer trusts 'reformists' after repeated failures",
                    source="Public sentiment",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.7
                ),
                EvidenceItem(
                    description="IRGC won't allow return to JCPOA-style concessions",
                    source="IRGC position",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.9
                ),
            ],
            key_assumptions=[
                "Regime survives current crisis",
                "Guardian Council allows reformist candidates",
                "IRGC accepts political opening",
                "West willing to negotiate again",
            ]
        )
        
        estimates["regime_survives_policy_change"] = self.create_probability_estimate(
            event="Current regime survives with significant policy changes (not collapse)",
            event_type="regime_collapse",
            source_estimates={
                "expert_analysts": 30.0,
                "reddit_sentiment": 15.0,
            },
            evidence_for=[
                EvidenceItem(
                    description="Regime has survived 45 years including Iran-Iraq war",
                    source="Historical analysis",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.8
                ),
                EvidenceItem(
                    description="IRGC controls 30%+ of economy, has strong survival incentive",
                    source="Economic analysis",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.7
                ),
                EvidenceItem(
                    description="China-Russia-Iran alliance provides economic/diplomatic lifeline",
                    source="Geopolitics",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.6
                ),
                EvidenceItem(
                    description="No organized opposition with clear leadership inside Iran",
                    source="Opposition analysis",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.7
                ),
            ],
            evidence_against=[
                EvidenceItem(
                    description="Khamenei (85) is inflexible ideologue, won't allow real reform",
                    source="Leadership analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.7
                ),
                EvidenceItem(
                    description="Economic crisis is structural (sanctions + mismanagement), not policy-fixable",
                    source="Economic analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.6
                ),
                protests_evidence,
                currency_evidence,
            ],
            key_assumptions=[
                "No US/Israeli military intervention",
                "Khamenei doesn't die suddenly",
                "IRGC remains unified",
                "China continues buying oil",
                "Protests don't reach critical mass",
            ]
        )
        
        estimates["hardliner_consolidation"] = self.create_probability_estimate(
            event="Hardliners consolidate power, no reform (continuation of current trend)",
            event_type="regime_collapse",
            source_estimates={
                "expert_analysts": 40.0,
                "reddit_sentiment": 25.0,
            },
            evidence_for=[
                EvidenceItem(
                    description="Current trajectory under Raisi presidency",
                    source="Policy analysis",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.7
                ),
                EvidenceItem(
                    description="IRGC dominates all major institutions",
                    source="Institutional analysis",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.8
                ),
                EvidenceItem(
                    description="Guardian Council blocks all alternative candidates",
                    source="Electoral system",
                    reliability="HIGH",
                    direction="SUPPORTS_ATTACK",
                    weight=0.8
                ),
                EvidenceItem(
                    description="Crisis justifies 'security first' approach",
                    source="Regime narrative",
                    reliability="MEDIUM",
                    direction="SUPPORTS_ATTACK",
                    weight=0.5
                ),
            ],
            evidence_against=[
                EvidenceItem(
                    description="Hardline approach failing to solve any problems",
                    source="Outcome analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.6
                ),
                protests_evidence,
                currency_evidence,
            ],
            key_assumptions=[
                "Khamenei survives current crisis",
                "No US military intervention",
                "IRGC maintains internal unity",
                "Protests suppressed successfully",
            ]
        )
        
        # Iran strikes Israel by Feb 28
        estimates["iran_strike_israel_feb28"] = self.create_probability_estimate(
            event="Iran strikes Israel by February 28, 2026",
            event_type="iran_initiates_attack",
            source_estimates={
                "polymarket": 39.0,
                "expert_analysts": 20.0,
                "reddit_sentiment": 30.0,
            },
            evidence_for=[
                EvidenceItem(
                    description="IRGC rhetoric about 'destroying Zionist regime'",
                    source="IRGC statements",
                    reliability="MEDIUM",
                    direction="SUPPORTS_ATTACK",
                    weight=0.4
                ),
            ],
            evidence_against=[
                protests_evidence,
                EvidenceItem(
                    description="Iran historically retaliates, doesn't initiate",
                    source="Historical analysis",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.9
                ),
                EvidenceItem(
                    description="IRGC forces stretched thin with protest crackdown",
                    source="Intelligence reports",
                    reliability="HIGH",
                    direction="AGAINST_ATTACK",
                    weight=0.7
                ),
            ],
            key_assumptions=[
                "Regime prioritizes survival over ideology",
                "Iran won't initiate while facing domestic crisis",
                "Direct attack on Israel = guaranteed US response",
            ]
        )
        
        return estimates
    
    def format_iran_context_section(self) -> str:
        """Generate Iran domestic context section."""
        lines = [
            "## 🇮🇷 Iran Domestic Context",
            "",
            "### Protest History (Escalating Pattern)",
            "",
            "| Year | Event | Casualties | Trigger |",
            "|------|-------|------------|---------|",
            "| 2017-18 | Dey Protests | 25+ killed | Economic grievances |",
            "| 2019 Nov | Bloody November (Aban 98) | 1,500+ killed | 300% fuel price hike |",
            "| 2022 Sep | Mahsa Amini / Woman Life Freedom | 500+ killed | Morality police killing |",
            "| 2026 Jan | Current Wave | 6,000+ killed | Rial collapse + war fears |",
            "",
            "**Pattern:** Each wave is larger, regime response more brutal, but protests keep returning.",
            "",
            "### Woman, Life, Freedom Movement (2022)",
            "",
            "The Mahsa Amini protests were transformative:",
            "- **First women-led movement** in Iran's history",
            "- **Unified ethnic groups**: Kurds, Persians, Azeris, Baloch",
            "- **Slogan**: 'Zan, Zendegi, Azadi' (Woman, Life, Freedom)",
            "- **International impact**: Oscar-winning documentary, global solidarity",
            "- **Legacy**: Delegitimized regime, created protest culture",
            "",
            "### Hijab & Morality Police",
            "",
            "- Mandatory hijab since 1983",
            "- 'Gasht-e Ershad' enforces dress code",
            "- After Amini death: patrols reduced but surveillance increased",
            "- Facial recognition cameras tracking unveiled women",
            "- Fines, car confiscation, prison for violations",
            "- **Symbol**: Hijab = regime control vs. personal freedom",
            "",
            "### Currency Collapse",
            "",
            "| Year | Rial/USD | Change |",
            "|------|----------|--------|",
            "| 2018 | 42,000 | Baseline |",
            "| 2022 | 320,000 | -87% |",
            "| 2024 | 550,000 | -92% |",
            "| 2026 | 850,000+ | -95% |",
            "",
            "**Impact:**",
            "- Middle class savings destroyed",
            "- Food/medicine shortages",
            "- Massive emigration ('brain drain')",
            "- Regime prints money → hyperinflation spiral",
            "",
            "### Central Bank Governors",
            "",
            "| Name | Tenure | Notes |",
            "|------|--------|-------|",
            "| Valiollah Seif | 2013-2018 | Sanctioned by US |",
            "| Abdolnaser Hemmati | 2018-2021 | Tried reforms, failed |",
            "| Mohammadreza Farzin | 2022-present | Crisis manager |",
            "",
            "Frequent changes = policy chaos. All face impossible task under sanctions.",
            "",
            "### Why This Matters for Conflict Analysis",
            "",
            "1. **Regime is weaker than it appears**: Internal crisis + external threat = dangerous",
            "2. **IRGC stretched thin**: Must control protests AND prepare for war",
            "3. **Economic leverage**: Sanctions are working, regime is desperate",
            "4. **Population is anti-regime**: Any US intervention has some domestic support",
            "5. **But regime is brutal**: Will use extreme violence to survive",
            "",
            "---",
            "",
        ]
        return "\n".join(lines)
    
    def format_regional_actors_section(self) -> str:
        """Generate regional actors analysis section."""
        lines = [
            "## 🌍 Regional Actors Analysis",
            "",
            "### Impact Assessment",
            "",
            "| Country | Role | Relationship with Iran | Impact on Conflict |",
            "|---------|------|------------------------|-------------------|",
            "| 🇴🇲 Oman | Traditional mediator | Neutral, maintains ties | **DE-ESCALATORY** |",
            "| 🇹🇷 Turkey | NATO member, hosting talks | Complex - competitor but partner | **DE-ESCALATORY** |",
            "| 🇸🇦 Saudi Arabia | Former rival, normalizing | Historic enemy, recent thaw | **NEUTRAL** |",
            "| 🇪🇬 Egypt | Arab heavyweight | Cold, no relations since 1979 | **NEUTRAL** |",
            "| 🇦🇪 UAE | Business hub | Economic ties despite tension | **DE-ESCALATORY** |",
            "| 🇶🇦 Qatar | US base host | Maintains ties, shared gas | **STRONGLY DE-ESCALATORY** |",
            "| 🇮🇶 Iraq | Buffer state | Close, Iran-aligned | **ESCALATORY RISK** |",
            "",
            "### Detailed Analysis",
            "",
            "#### 🇴🇲 Oman - The Quiet Mediator",
            "- Mediated secret US-Iran talks leading to JCPOA (2013-2015)",
            "- Sultan Haitham continues neutral policy",
            "- Shares Strait of Hormuz with Iran",
            "- **Current role:** Likely facilitating backchannel communications",
            "- **Key value:** Trusted by both US and Iran",
            "",
            "#### 🇹🇷 Turkey - NATO's Swing State",
            "- **Hosting Istanbul talks (Feb 7, 2026)**",
            "- Major Iran trade partner despite sanctions",
            "- Erdogan critical of US/Israeli pressure on Iran",
            "- **Won't allow Turkish bases for Iran attack**",
            "- But as NATO member, can't fully oppose US",
            "- Both Turkey and Iran oppose Kurdish independence",
            "",
            "#### 🇸🇦 Saudi Arabia - From Rival to Cautious Neighbor",
            "- China-brokered normalization deal (March 2023)",
            "- Embassies reopened after 7 years of closure",
            "- MBS prioritizes Vision 2030 over regional conflicts",
            "- **No longer funding anti-Iran proxies openly**",
            "- Doesn't want war destabilizing oil markets",
            "- **Position:** Won't support attack but won't defend Iran",
            "",
            "#### 🇪🇬 Egypt - The Suez Factor",
            "- No diplomatic relations with Iran since 1979",
            "- Controls Suez Canal - critical for oil shipping",
            "- Part of negotiations with Turkey/Qatar",
            "- Sisi prioritizes stability over ideology",
            "- **Position:** Behind-scenes diplomacy support",
            "",
            "#### 🇦🇪 UAE - Business Over Politics",
            "- Dubai is major Iran trade hub (despite sanctions)",
            "- Large Iranian expat community (400,000+)",
            "- Abraham Accords aligned UAE with Israel",
            "- **BUT won't provide airspace for Iran attack**",
            "- Withdrew from Yemen coalition - war fatigue",
            "- **Position:** Prioritizes business stability",
            "",
            "#### 🇶🇦 Qatar - Caught in the Middle",
            "- **Al Udeid - largest US base in Middle East**",
            "- Shares world's largest gas field with Iran (South Pars)",
            "- June 2025: Iran retaliated against US by hitting Qatar base",
            "- **Extremely nervous about being target again**",
            "- Hosts Hamas leaders, maintains Iran ties",
            "- **Position:** Strongly pushing de-escalation",
            "",
            "#### 🇮🇶 Iraq - The Potential Battleground",
            "- Iran-aligned Shia-majority government",
            "- Popular Mobilization Forces (PMF/Hashd) are Iran proxies",
            "- US still has ~2,500 troops",
            "- Border with Iran is porous",
            "- **Would be transit route for any ground invasion**",
            "- **Position:** Trying to stay neutral, likely fails if war starts",
            "",
            "### Regional Summary",
            "",
            "**De-escalatory factors (6 countries):**",
            "- Turkey, Oman, Qatar actively pushing diplomacy",
            "- Saudi-Iran normalization removes major antagonist",
            "- UAE, Egypt prioritize stability",
            "- Most Gulf states explicitly oppose US attack on Iran",
            "",
            "**Escalatory factors (1 country):**",
            "- Iraq as potential proxy battleground",
            "- Iran militias in Iraq could attack US troops",
            "",
            "**Key finding:** Regional environment is more **de-escalatory** than 5 years ago.",
            "Saudi normalization and Turkish mediation significantly reduce support for military action.",
            "Only Israel actively supports US strikes on Iran.",
            "",
            "---",
            "",
        ]
        return "\n".join(lines)
    
    def format_full_reasoning_report(self) -> str:
        """Generate full reasoning report."""
        estimates = self.generate_iran_conflict_estimates()
        
        lines = [
            "# 🧠 Full Reasoning Analysis Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
            "## Methodology",
            "",
            "This analysis uses a structured reasoning framework combining:",
            "1. **Historical base rates** - What is the prior probability based on history?",
            "2. **Bayesian updating** - How does new evidence shift our estimates?",
            "3. **Source aggregation** - Weighting multiple sources by reliability",
            "4. **Sensitivity analysis** - How do estimates change if assumptions are wrong?",
            "",
            "### Source Reliability Rankings",
            "",
            "| Source | Reliability | Reasoning |",
            "|--------|-------------|-----------|",
        ]
        
        for source, data in self.SOURCE_RELIABILITY.items():
            lines.append(f"| {source} | {data['reliability']:.0%} | {data['reasoning']} |")
        
        lines.extend([
            "",
            "---",
            "",
        ])
        
        # Add Iran context section
        lines.append(self.format_iran_context_section())
        
        # Add regional actors section
        lines.append(self.format_regional_actors_section())
        
        lines.extend([
            "## Probability Estimates",
            "",
        ])
        
        for key, estimate in estimates.items():
            lines.append(estimate.final_reasoning)
            lines.append("\n---\n")
        
        return "\n".join(lines)


def main():
    """Test reasoning framework."""
    framework = ReasoningFramework()
    print(framework.format_full_reasoning_report())


if __name__ == "__main__":
    main()
