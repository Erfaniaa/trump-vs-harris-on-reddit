"""
LLM Analyzer - Uses Claude for deep reasoning and analysis.

This module is used sparingly (only for final analysis) to avoid
slowing down the pipeline and excessive API costs.

Enhanced with:
- User opinion summaries
- Scenario probability analysis
- Extended predictions (assassination, regime change, war duration, etc.)
- Daily/weekly/monthly timeline breakdowns
- Financial market analysis (gold, crypto)
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import market analyzer for financial data
try:
    from src.data.market_analyzer import MarketAnalyzer
    MARKET_ANALYZER_AVAILABLE = True
except ImportError:
    MARKET_ANALYZER_AVAILABLE = False


@dataclass
class LLMAnalysisResult:
    """Result from LLM analysis."""
    executive_summary: str
    key_findings: List[str]
    attack_probability_assessment: str
    likely_dates: List[Dict[str, Any]]
    scenarios_analysis: str
    reasoning: str
    uncertainties: List[str]
    comparison_with_polymarket: str
    final_verdict: str
    generated_at: str
    model_used: str
    
    # New fields for extended analysis
    user_opinion_summary: str = ""
    scenario_probabilities: Dict[str, Any] = field(default_factory=dict)
    extended_predictions: Dict[str, Any] = field(default_factory=dict)
    timeline_breakdown: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        # Backward-compatible aliases expected by report_generator.py
        # - "attack_probability" (string) is used in some report templates
        d.setdefault("attack_probability", d.get("attack_probability_assessment", ""))
        # - "timeline_predictions" is used in some report templates; map to likely_dates
        d.setdefault("timeline_predictions", d.get("likely_dates", []))
        return d


class LLMAnalyzer:
    """
    Uses Claude Opus 4.6 for sophisticated analysis and reasoning.
    
    Design principles:
    - Called only ONCE at the end of analysis (not per-comment)
    - Receives aggregated data, not raw comments
    - Generates comprehensive reasoning and date predictions
    """
    
    MODEL = "claude-opus-4-6"  # Claude Opus 4.6
    MAX_TOKENS = 4096
    SECTION_MAX_TOKENS = 2000
    FINAL_MAX_TOKENS = 2400
    USE_THINKING = True
    THINKING_BUDGET_TOKENS = 12000
    
    def __init__(self, api_key: str):
        """Initialize with Anthropic API key."""
        self.api_key = api_key
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print("   ✅ Claude API initialized")
        except ImportError:
            print("   ⚠️ anthropic package not installed. Run: pip install anthropic")
            self.client = None
        except Exception as e:
            print(f"   ⚠️ Could not initialize Claude API: {e}")
            self.client = None
    
    def _get_market_context(self) -> str:
        """Get financial market context for analysis."""
        if MARKET_ANALYZER_AVAILABLE:
            try:
                analyzer = MarketAnalyzer()
                return analyzer.get_market_insights_for_llm()
            except Exception as e:
                return f"[Market data unavailable: {e}]"
        return "[Market analyzer not available]"
    
    def _call_claude_json(self, prompt: str, max_tokens: int) -> Optional[Dict[str, Any]]:
        """Call Claude and parse a JSON object response."""
        if not self.client:
            return None
        try:
            base_kwargs = {
                "model": self.MODEL,
                "max_tokens": int(max_tokens),
                "messages": [{"role": "user", "content": prompt}],
            }
            if self.USE_THINKING:
                try:
                    response = self.client.messages.create(
                        **base_kwargs,
                        thinking={"type": "enabled", "budget_tokens": int(self.THINKING_BUDGET_TOKENS)},
                    )
                except Exception:
                    response = self.client.messages.create(**base_kwargs)
            else:
                response = self.client.messages.create(**base_kwargs)
            response_text = response.content[0].text
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r"\{[\s\S]*\}", response_text)
                if json_match:
                    return json.loads(json_match.group())
                return None
        except Exception:
            return None

    def _compact_context_bundle(
        self,
        analysis_results: Dict,
        polymarket_data: Dict,
        gathering_stats: Dict,
        current_date: str,
    ) -> Dict[str, Any]:
        """
        Build a compact structured context object for multi-call analysis.
        Keep it small to reduce token usage and avoid truncation.
        """
        total_users = int(analysis_results.get("total_authors_analyzed", 0) or 0)
        total_comments = int(analysis_results.get("total_comments_analyzed", 0) or 0)
        predict_attack = int(analysis_results.get("predict_attack", 0) or 0)
        predict_no_attack = int(analysis_results.get("predict_no_attack", 0) or 0)
        neutral = int(analysis_results.get("neutral", 0) or max(0, total_users - predict_attack - predict_no_attack))
        total_opinionated = max(0, predict_attack + predict_no_attack)
        opinionated_pct = (100.0 * total_opinionated / total_users) if total_users > 0 else 0.0

        # Keep only top-level, high-signal aggregates
        scenario_stats = analysis_results.get("scenario_stats", {}) or {}
        timeline_stats = analysis_results.get("timeline_stats", {}) or {}
        ext = analysis_results.get("extended_predictions", {}) or {}

        # Polymarket markets list (already compact)
        pm_markets = polymarket_data.get("markets", []) or []
        pm_comments = polymarket_data.get("comments_summary", {}) or {}
        pm_traders = polymarket_data.get("high_win_rate_traders", {}) or {}

        # Market/news summaries (already computed elsewhere)
        market_analysis = polymarket_data.get("market_analysis", {}) or {}

        bundle = {
            "date": current_date,
            "reddit": {
                "total_users": total_users,
                "total_comments": total_comments,
                "predict_attack_users": predict_attack,
                "predict_no_attack_users": predict_no_attack,
                "neutral_users": neutral,
                "total_opinionated_users": total_opinionated,
                "opinionated_pct": round(opinionated_pct, 2),
                "avg_confidence": float(analysis_results.get("avg_confidence", 0) or 0),
                "high_conf_attack": int(analysis_results.get("high_confidence_attack", 0) or 0),
                "high_conf_no_attack": int(analysis_results.get("high_confidence_no_attack", 0) or 0),
                "scenario_stats": scenario_stats,
                "timeline_stats": timeline_stats,
                "extended_mentions": ext,
                "top_attack_comments": (analysis_results.get("top_attack_comments", []) or [])[:8],
                "top_no_attack_comments": (analysis_results.get("top_no_attack_comments", []) or [])[:8],
            },
            "polymarket": {
                "markets": pm_markets,
                "comments_summary": {
                    "total_comments": pm_comments.get("total_comments", 0),
                    "yes_count": pm_comments.get("yes_count", 0),
                    "no_count": pm_comments.get("no_count", 0),
                    "unclear_count": pm_comments.get("unclear_count", 0),
                    "yes_sentiment_pct": pm_comments.get("yes_sentiment", 0),
                    "no_sentiment_pct": pm_comments.get("no_sentiment", 0),
                    "source": pm_comments.get("source", ""),
                },
                "high_win_rate_traders": {
                    "method": pm_traders.get("method", ""),
                    "min_win_rate": pm_traders.get("min_win_rate", ""),
                    "min_sample_n": pm_traders.get("min_sample_n", ""),
                    "smart_money": pm_traders.get("smart_money", {}),
                    "traders": (pm_traders.get("traders", []) or [])[:8],
                    "source": pm_traders.get("source", ""),
                },
            },
            "markets": market_analysis,
            "gathering": {
                "time_filter": gathering_stats.get("time_filter", ""),
                "subreddits": gathering_stats.get("subreddits", []),
                "failed_subreddits": gathering_stats.get("failed_subreddits", []),
            },
        }
        return bundle

    def analyze_multi_call(
        self,
        analysis_results: Dict,
        polymarket_data: Dict,
        gathering_stats: Dict,
        sample_comments: Optional[List[Dict]] = None,
    ) -> Optional[LLMAnalysisResult]:
        """
        Multi-call LLM analysis: split the report into multiple focused API calls.
        This reduces truncation, improves structure, and makes consistency checks easier.
        """
        if not self.client:
            print("   ⚠️ Claude API not available, skipping LLM analysis")
            return None

        current_date = datetime.now().strftime("%Y-%m-%d")
        bundle = self._compact_context_bundle(
            analysis_results=analysis_results,
            polymarket_data=polymarket_data,
            gathering_stats=gathering_stats or {},
            current_date=current_date,
        )
        bundle_json = json.dumps(bundle, ensure_ascii=False)
        market_context = self._get_market_context()

        print("\n🧠 Generating deep analysis with Claude (multi-call, parallel)...")
        print("   (This may take 30-60 seconds with parallelization)")

        # Define prompts for parallel execution
        # 1) Executive summary + findings (short, crisp)
        p1 = f"""
You are writing a long-form analytical report. Today's date is {current_date}.
Use ONLY the provided JSON context (do not invent new facts).

CONTEXT_JSON:
{bundle_json}

Return JSON with:
{{
  "executive_summary": "2-4 sentences",
  "key_findings": ["5-9 bullet findings, each 1 sentence (include a brief note on R2P discourse and severe internet shutdown risk if relevant)"]
}}
"""

        # 2) Timeline windows (date ranges, not relative words)
        p2 = f"""
You are producing the report's timeline section. Today's date is {current_date}.
Use ONLY the provided JSON context + market context. Do not invent facts.
Do NOT use words like "today/this week" without also providing explicit date ranges.

CONTEXT_JSON:
{bundle_json}

MARKET_CONTEXT:
{market_context}

Return JSON with:
{{
  "attack_probability_assessment": "1-3 short paragraphs with base rate + Bayesian update language",
  "likely_dates": [
    {{"date_range": "YYYY-MM-DD to YYYY-MM-DD", "probability": "e.g. 12% (range: 8-18%)", "reasoning": "full sentence reasoning, not truncated"}},
    ...
  ],
  "timeline_breakdown": {{
    "YYYY-MM-DD to YYYY-MM-DD": "X% (range: A-B%)",
    "YYYY-MM-DD to YYYY-MM-DD": "..."
  }}
}}
"""

        # 3) Scenarios + extended predictions (explicitly separate 'mention share' vs probability)
        p3 = f"""
You are producing the report's scenario section. Today's date is {current_date}.
Use ONLY the provided JSON context. Do not invent facts.
Be explicit that Reddit "mentions" are NOT real-world probabilities.
Do NOT provide probabilities or forecasts about assassination, death, or physical harm to any named individual.
Include a brief note on R2P discourse and severe internet shutdown risk in Iran as narrative/contingent factors (not certainty).

CONTEXT_JSON:
{bundle_json}

Return JSON with:
{{
  "user_opinion_summary": "What users say (themes/arguments), 2-4 short paragraphs",
  "scenarios_analysis": "Narrative + which scenarios dominate, 2-4 paragraphs",
  "scenario_probabilities": {{
    "nuclear_facility_strike": "X% (range: A-B%)",
    "military_base_strike": "...",
    "limited_surgical_strike": "...",
    "full_scale_war": "...",
    "proxy_conflict_only": "...",
    "no_military_action": "..."
  }},
  "extended_predictions": {{
    "regime_change_probability_2026": "X% (range: A-B%)",
    "war_duration_if_occurs": "describe with ranges",
    "negotiation_success_probability": "X% (range: A-B%)",
    "future_government_most_likely": "one of: monarchy/secular democracy/reformed Islamic/military/chaos",
    "iran_most_resembles": "must specify if Syria: 'Syria-Civil War Era (2011-2024, Assad...)' OR 'Syria-Post Assad Era (2024+, HTS/Jolani...)'",
    "country_comparison_analysis": "structured explanation in short paragraphs",
    "pahlavi_power_probability": "X% (range: A-B%) - probability Reza Pahlavi comes to power if regime changes",
    "pahlavi_analysis": "2-3 sentences: Why Pahlavi might or might not come to power. Consider: exile support, internal support, Western backing, competing factions (IRGC, reformists, ethnic groups)",
    "leader_fate_scenarios": {{
      "survives_in_power": "X%",
      "forced_exile": "X%", 
      "internal_coup": "X%",
      "negotiated_transition": "X%"
    }},
    "war_type_if_occurs": {{
      "air_strikes_only": "X% - Limited to air/missile strikes on nuclear/military facilities",
      "air_plus_special_ops": "X% - Air strikes combined with special operations",
      "cyberwar_focused": "X% - Primarily cyber attacks on infrastructure",
      "full_ground_invasion": "X% - Large-scale ground forces (extremely unlikely)"
    }},
    "war_duration_phases": {{
      "initial_strike_phase": "X days (range: A-B days)",
      "active_conflict_phase": "X weeks (range: A-B weeks)", 
      "de_escalation_phase": "X weeks (range: A-B weeks)",
      "post_conflict_instability": "X months/years (range: A-B)"
    }},
    "safety_note": "1 sentence: we do not estimate individual harm/death outcomes"
  }}
}}
"""
        
        # Execute first 3 calls in parallel (they are independent)
        r1, r2, r3 = {}, {}, {}
        
        def _call_p1():
            return self._call_claude_json(p1, max_tokens=self.SECTION_MAX_TOKENS) or {}
        
        def _call_p2():
            return self._call_claude_json(p2, max_tokens=self.SECTION_MAX_TOKENS) or {}
        
        def _call_p3():
            return self._call_claude_json(p3, max_tokens=self.SECTION_MAX_TOKENS) or {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_1 = executor.submit(_call_p1)
            future_2 = executor.submit(_call_p2)
            future_3 = executor.submit(_call_p3)
            
            try:
                r1 = future_1.result()
            except Exception as e:
                print(f"   ⚠️ Executive summary call failed: {e}")
                r1 = {}
            
            try:
                r2 = future_2.result()
            except Exception as e:
                print(f"   ⚠️ Timeline call failed: {e}")
                r2 = {}
            
            try:
                r3 = future_3.result()
            except Exception as e:
                print(f"   ⚠️ Scenarios call failed: {e}")
                r3 = {}

        # 4) Reconciliation + uncertainties + final verdict + consistency check
        p4 = f"""
You are producing the report's reconciliation and final verdict.
Use ONLY the provided JSON context plus the draft outputs from previous sections.
Resolve contradictions explicitly (if any). Keep it concise but clear.

CONTEXT_JSON:
{bundle_json}

DRAFT_SECTION_1_JSON:
{json.dumps(r1, ensure_ascii=False)}

DRAFT_SECTION_2_JSON:
{json.dumps(r2, ensure_ascii=False)}

DRAFT_SECTION_3_JSON:
{json.dumps(r3, ensure_ascii=False)}

Return JSON with:
{{
  "reasoning": "multi-paragraph reasoning",
  "uncertainties": ["5-10 bullets"],
  "comparison_with_polymarket": "how Reddit vs Polymarket differs and why",
  "final_verdict": "1-3 sentences"
}}
"""
        r4 = self._call_claude_json(p4, max_tokens=self.FINAL_MAX_TOKENS) or {}

        # Merge
        merged: Dict[str, Any] = {}
        for part in (r1, r2, r3, r4):
            if isinstance(part, dict):
                merged.update(part)

        result = LLMAnalysisResult(
            executive_summary=merged.get("executive_summary", ""),
            key_findings=merged.get("key_findings", []) or [],
            attack_probability_assessment=merged.get("attack_probability_assessment", ""),
            likely_dates=merged.get("likely_dates", []) or [],
            scenarios_analysis=merged.get("scenarios_analysis", ""),
            reasoning=merged.get("reasoning", ""),
            uncertainties=merged.get("uncertainties", []) or [],
            comparison_with_polymarket=merged.get("comparison_with_polymarket", ""),
            final_verdict=merged.get("final_verdict", ""),
            generated_at=datetime.now().isoformat(),
            model_used=self.MODEL,
            user_opinion_summary=merged.get("user_opinion_summary", ""),
            scenario_probabilities=merged.get("scenario_probabilities", {}) or {},
            extended_predictions=merged.get("extended_predictions", {}) or {},
            timeline_breakdown=merged.get("timeline_breakdown", {}) or {},
        )

        print("   ✅ Deep analysis complete (multi-call)!")
        return result

    def _build_analysis_prompt(
        self,
        analysis_results: Dict,
        polymarket_data: Dict,
        gathering_stats: Dict,
        current_date: str,
        sample_comments: List[Dict]
    ) -> str:
        """Build the prompt for Claude analysis."""
        
        # Extract key metrics
        total_users = analysis_results.get('total_authors_analyzed', 0)
        predict_attack = analysis_results.get('predict_attack', 0)
        predict_no_attack = analysis_results.get('predict_no_attack', 0)
        neutral = analysis_results.get('neutral', 0)
        
        total_opinionated = predict_attack + predict_no_attack
        attack_pct = (100 * predict_attack / total_opinionated) if total_opinionated > 0 else 0
        no_attack_pct = (100 * predict_no_attack / total_opinionated) if total_opinionated > 0 else 0
        
        # Scenario stats
        scenario_stats = analysis_results.get('scenario_stats', {})
        timeline_stats = analysis_results.get('timeline_stats', {})
        subreddit_stats = analysis_results.get('subreddit_stats', {})
        
        # Extended predictions
        extended_predictions = analysis_results.get('extended_predictions', {})
        
        # Polymarket data
        pm_markets = polymarket_data.get('markets', [])
        
        # Sample comments for context
        attack_comments = analysis_results.get('top_attack_comments', [])[:10]
        no_attack_comments = analysis_results.get('top_no_attack_comments', [])[:10]
        
        prompt = f"""You are an expert geopolitical analyst specializing in US-Iran relations and Middle East conflicts. 
Today's date is {current_date}.

I have analyzed Reddit comments about the possibility of US military action against Iran. Here is the aggregated data:

## REDDIT SENTIMENT ANALYSIS RESULTS

**Sample Size:**
- Total users analyzed: {total_users}
- Total comments analyzed: {analysis_results.get('total_comments_analyzed', 0)}
- Data collection period: {gathering_stats.get('time_filter', 'month')}
- Subreddits analyzed: {len(subreddit_stats)}

**Prediction Breakdown:**
- Users predicting ATTACK: {predict_attack} ({attack_pct:.1f}%)
- Users predicting NO ATTACK: {predict_no_attack} ({no_attack_pct:.1f}%)
- Neutral/Unclear: {neutral}
- Average confidence score: {analysis_results.get('avg_confidence', 0):.2f}
- High confidence attack predictions: {analysis_results.get('high_confidence_attack', 0)}
- High confidence no-attack predictions: {analysis_results.get('high_confidence_no_attack', 0)}

**Scenarios Discussed:**
{json.dumps(scenario_stats, indent=2)}

**Timelines Mentioned (Granular):**
{json.dumps(timeline_stats, indent=2)}

**Subreddit Breakdown (top 10):**
{json.dumps(dict(list(sorted(subreddit_stats.items(), key=lambda x: x[1].get('count', 0), reverse=True))[:10]), indent=2)}

**Extended Predictions from Comments:**
{json.dumps(extended_predictions, indent=2)}

## POLYMARKET PREDICTION MARKET ODDS

Current prediction market probabilities (granular by date):
{json.dumps(pm_markets, indent=2)}

## SAMPLE HIGH-CONFIDENCE COMMENTS

**Pro-Attack Predictions:**
{json.dumps(attack_comments[:5], indent=2)}

**Anti-Attack Predictions:**
{json.dumps(no_attack_comments[:5], indent=2)}

## CURRENT GEOPOLITICAL CONTEXT

Use ONLY the information provided above (Reddit aggregates, Polymarket markets, and any optional multi-source news data that is explicitly included in the context bundle).
Do not insert specific deployments, quotes, casualty counts, explosions, meetings, or named-person events unless they appear in the provided JSON context.
If you reference news, cite only from the included news headlines list (title/source/date/url) and make uncertainty explicit.

{self._get_market_context()}

---

Based on this data, please provide a comprehensive analysis in JSON format with the following structure:

{{
    "executive_summary": "A 2-3 sentence summary of the overall findings",
    "key_findings": ["List of 5-7 key findings from the data"],
    "attack_probability_assessment": "Your assessment of the likelihood of US military action, with reasoning",
    "likely_dates": [
        {{
            "date_range": "e.g., February 3-6, 2026",
            "probability": "e.g., 5%",
            "reasoning": "Why this timeframe"
        }},
        {{
            "date_range": "February 7-13, 2026 (next week)",
            "probability": "e.g., 15%",
            "reasoning": "Why"
        }},
        {{
            "date_range": "February 14-28, 2026 (this month)",
            "probability": "e.g., 25%",
            "reasoning": "Why"
        }},
        {{
            "date_range": "March 2026",
            "probability": "e.g., 35%",
            "reasoning": "Why"
        }},
        {{
            "date_range": "Q2 2026 (April-June)",
            "probability": "e.g., 45%",
            "reasoning": "Why"
        }}
    ],
    "scenarios_analysis": "Analysis of which conflict scenarios are most likely based on the discussion",
    "user_opinion_summary": "Summary of what regular users/commenters think will happen, their main arguments and concerns",
    "scenario_probabilities": {{
        "nuclear_facility_strike": "X%",
        "military_base_strike": "X%",
        "limited_surgical_strike": "X%",
        "full_scale_war": "X%",
        "proxy_conflict_only": "X%",
        "no_military_action": "X%"
    }},
    "extended_predictions": {{
        "regime_change_probability_2026": "X%",
        "war_duration_if_occurs": "X days/weeks/months",
        "negotiation_success_probability": "X%",
        "future_government_most_likely": "monarchy/secular democracy/reformed Islamic/military/chaos",
        "iran_most_resembles": "Which country/scenario Iran's future most resembles. For Syria, specify which era: 'Syria-Civil War Era (2011-2024, Assad, prolonged proxy war, decade of destruction)' OR 'Syria-Post Assad Era (2024+, HTS/Jolani takeover, quick Islamist transition)'. Other options: Iraq/Libya/Afghanistan/Egypt/Tunisia/Russia/Yugoslavia/Venezuela/North Korea/South Korea/1979 Iran",
        "country_comparison_analysis": "Detailed analysis of why Iran's future resembles this country/scenario. IMPORTANT for Syria: clearly distinguish between (a) Assad-era civil war scenario (decade of conflict, multiple proxy powers, no decisive winner) vs (b) Post-Assad scenario (quick regime collapse, Islamist successor government like HTS). Include: 1) Most likely scenario, 2) Second most likely, 3) Why not others, 4) Key determining factors, 5) What would need to change for a different outcome",
        "pahlavi_power_probability": "X% - probability Reza Pahlavi comes to power if regime changes",
        "pahlavi_analysis": "Why Pahlavi might or might not succeed. Consider: Western support, internal legitimacy, IRGC resistance, competing factions",
        "leader_fate_scenarios": {{
            "survives_in_power": "X%",
            "forced_exile": "X%",
            "internal_coup": "X%",
            "negotiated_transition": "X%"
        }},
        "war_type_if_occurs": {{
            "air_strikes_only": "X%",
            "air_plus_special_ops": "X%",
            "cyberwar_focused": "X%",
            "full_ground_invasion": "X%"
        }},
        "war_duration_phases": {{
            "initial_strike_phase": "X days",
            "active_conflict_phase": "X weeks",
            "de_escalation_phase": "X weeks",
            "post_conflict_instability": "X months/years"
        }},
        "safety_note": "1 sentence: we do not estimate individual harm/death outcomes"
    }},
    "timeline_breakdown": {{
        "today_tomorrow": "X% probability of strike",
        "this_week": "X%",
        "next_week": "X%",
        "this_month": "X%",
        "next_month": "X%",
        "this_quarter": "X%",
        "this_year": "X%"
    }},
    "reasoning": "Detailed reasoning connecting Reddit sentiment, Polymarket odds, and geopolitical factors. Consider: Why might Reddit and Polymarket differ? What factors are users considering? What might they be missing?",
    "uncertainties": ["List of key uncertainties and caveats"],
    "comparison_with_polymarket": "Analysis of why Reddit sentiment differs from or aligns with Polymarket odds",
    "final_verdict": "Your final assessment in 1-2 sentences"
}}

**CRITICAL REASONING REQUIREMENTS:**

For EVERY probability estimate, you MUST provide explicit reasoning using this framework:

1. **Base Rate Analysis:**
   - What is the historical base rate for similar events?
   - How many times has the US struck Iran in the past? (Answer: 0 direct strikes before June 2025)
   - What was the outcome of similar situations?

2. **Evidence Weighting:**
   - STRONG EVIDENCE (weight 3x): Military deployments, official statements, verified intelligence
   - MEDIUM EVIDENCE (weight 2x): Polymarket odds, credible news reports, expert analysis
   - WEAK EVIDENCE (weight 1x): Reddit sentiment, social media, rumors, unnamed sources
   
3. **Bayesian Updating:**
   - Start with base rate
   - Update based on new evidence strength
   - Explicitly state: "Prior: X%, Evidence shift: +/-Y%, Posterior: Z%"

4. **Contradiction Resolution:**
   - When sources disagree, explain WHY and which source is more reliable
   - Reddit (53%) vs Polymarket (22%) → explain the gap
   - Gold signal ($5,038) vs Polymarket odds → explain disconnect

5. **Confidence Intervals:**
   - Provide ranges, not point estimates where uncertain
   - "25% (range: 18-32%)" is better than just "25%"

6. **Key Assumptions:**
   - List 3-5 key assumptions your estimates depend on
   - Note how estimates change if assumptions are wrong

**AVOID THESE REASONING ERRORS:**
- Anchoring on Reddit percentages (they're low-information)
- Ignoring base rates (US has never directly attacked Iran before June 2025)
- Overweighting recent news (availability bias)
- Treating all sources equally (Polymarket > Reddit for accuracy)
- Conflating "possible" with "probable"
- Ignoring conditional dependencies (Israel strikes → US likely follows)

**SOURCE RELIABILITY RANKING:**
1. Polymarket (money at stake, aggregates many views)
2. Gold/commodity markets (sophisticated traders)
3. Official statements (may be posturing but signal intent)
4. Expert analysts (Axios, Reuters, etc.)
5. Reddit sentiment (useful for detecting narratives, not probabilities)

Important considerations:
1. Reddit's demographic skews younger and more liberal
2. Polymarket participants have financial incentives for accuracy
3. Recent news events may disproportionately influence Reddit sentiment
4. Consider both the US political situation and Iran's domestic situation (protests, economic crisis)
5. Factor in the current date ({current_date}) when assessing timelines - be specific about days and weeks
6. Consider Israeli pressure, regional dynamics, and Trump's stated intentions
7. Consider the carrier deployment and military readiness signals
8. Consider that Iran is currently dealing with massive internal protests (6,000+ deaths)
9. Consider China-Russia-Iran trilateral alliance and potential responses
10. Include R2P (Responsibility to Protect) as a political/narrative signal, not a deterministic trigger
11. Include a short assessment of severe internet shutdown risk in Iran with clear conditional vs unconditional language
12. Include US stock market and oil price signals as macro indicators (note when they conflict with other signals)

Respond ONLY with valid JSON, no other text."""

        return prompt

    def analyze(
        self,
        analysis_results: Dict,
        polymarket_data: Dict,
        gathering_stats: Dict,
        sample_comments: List[Dict] = None
    ) -> Optional[LLMAnalysisResult]:
        """
        Perform deep analysis using Claude Opus 4.6.
        
        This is called ONCE at the end of the pipeline with aggregated data.
        
        Args:
            analysis_results: Aggregated results from ScenarioAnalyzer
            polymarket_data: Current Polymarket odds
            gathering_stats: Statistics about data collection
            sample_comments: Optional sample of raw comments
        
        Returns:
            LLMAnalysisResult with comprehensive analysis, or None if failed
        """
        if not self.client:
            print("   ⚠️ Claude API not available, skipping LLM analysis")
            return None
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # New default: multi-call analysis (more reliable, less truncation).
        # Keep the single-call prompt builder for future fallback, but prefer multi-call.
        try:
            return self.analyze_multi_call(
                analysis_results=analysis_results,
                polymarket_data=polymarket_data,
                gathering_stats=gathering_stats,
                sample_comments=sample_comments or [],
            )
        except Exception as e:
            print(f"   ❌ Multi-call LLM analysis failed: {e}")
            # Last-resort fallback to single-call behavior
            print("   ↩️ Falling back to single-call analysis...")
            prompt = self._build_analysis_prompt(
                analysis_results=analysis_results,
                polymarket_data=polymarket_data,
                gathering_stats=gathering_stats,
                current_date=current_date,
                sample_comments=sample_comments or []
            )
            result_data = self._call_claude_json(prompt, max_tokens=self.MAX_TOKENS)
            if not isinstance(result_data, dict):
                return None
            return LLMAnalysisResult(
                executive_summary=result_data.get('executive_summary', ''),
                key_findings=result_data.get('key_findings', []),
                attack_probability_assessment=result_data.get('attack_probability_assessment', ''),
                likely_dates=result_data.get('likely_dates', []),
                scenarios_analysis=result_data.get('scenarios_analysis', ''),
                reasoning=result_data.get('reasoning', ''),
                uncertainties=result_data.get('uncertainties', []),
                comparison_with_polymarket=result_data.get('comparison_with_polymarket', ''),
                final_verdict=result_data.get('final_verdict', ''),
                generated_at=datetime.now().isoformat(),
                model_used=self.MODEL,
                user_opinion_summary=result_data.get('user_opinion_summary', ''),
                scenario_probabilities=result_data.get('scenario_probabilities', {}),
                extended_predictions=result_data.get('extended_predictions', {}),
                timeline_breakdown=result_data.get('timeline_breakdown', {})
            )
    
    def generate_date_predictions(
        self,
        analysis_results: Dict,
        polymarket_data: Dict
    ) -> List[Dict]:
        """
        Generate specific date predictions for potential attack.
        
        Returns list of date ranges with probabilities and reasoning.
        """
        if not self.client:
            return self._fallback_date_predictions(polymarket_data)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""Based on current geopolitical analysis and prediction market data, 
provide specific date range predictions for potential US military action against Iran.

Today's date: {current_date}

Polymarket odds:
{json.dumps(polymarket_data.get('markets', []), indent=2)}

Provide 4-5 date ranges with probabilities in JSON format:
[
    {{
        "date_range": "Month Year or specific range",
        "probability": "X%",
        "reasoning": "Brief explanation",
        "key_triggers": ["Events that could trigger action in this period"]
    }}
]

Consider:
- US political calendar (elections, congressional sessions)
- Iran's nuclear program milestones
- Regional events (Israel, Gulf states)
- Historical patterns of US military action

Respond ONLY with valid JSON array."""

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    return json.loads(json_match.group())
                return self._fallback_date_predictions(polymarket_data)
                
        except Exception as e:
            print(f"   ⚠️ Date prediction failed: {e}")
            return self._fallback_date_predictions(polymarket_data)
    
    def _fallback_date_predictions(self, polymarket_data: Dict) -> List[Dict]:
        """Fallback date predictions based on Polymarket data."""
        markets = polymarket_data.get('markets', [])
        predictions = []
        
        for market in markets:
            name = market.get('name', '')
            prob = market.get('probability', 0)
            
            # Extract date from market name
            if 'February' in name:
                predictions.append({
                    "date_range": "February 2026",
                    "probability": f"{prob}%",
                    "reasoning": "Based on Polymarket odds",
                    "key_triggers": ["Near-term escalation", "Nuclear program developments"]
                })
            elif 'March' in name:
                predictions.append({
                    "date_range": "March 2026",
                    "probability": f"{prob}%", 
                    "reasoning": "Based on Polymarket odds",
                    "key_triggers": ["Diplomatic deadline", "Israeli pressure"]
                })
            elif 'June' in name:
                predictions.append({
                    "date_range": "Q2 2026 (April-June)",
                    "probability": f"{prob}%",
                    "reasoning": "Based on Polymarket odds",
                    "key_triggers": ["Spring military window", "Pre-summer action"]
                })
            elif 'December' in name:
                predictions.append({
                    "date_range": "2026 (Full Year)",
                    "probability": f"{prob}%",
                    "reasoning": "Cumulative probability by year end",
                    "key_triggers": ["Multiple potential trigger points"]
                })
        
        return predictions
    
    def _format_analysis_text(self, text: str) -> str:
        """
        Format long analysis text for better readability.
        Splits into bullet points based on numbered items, colons, and logical breaks.
        """
        if not text:
            return ""
        
        import re
        
        # First, handle "not X (reason)" patterns - make them bullet points
        # Also handle comma-separated "not X" items
        text = re.sub(r',\s*not\s+([A-Z][a-z]+)\s*\(([^)]+)\)', 
                      r'\n- **Not \1** (\2)', text)
        text = re.sub(r'\.\s*[Nn]ot\s+([A-Z][a-z]+)\s*\(([^)]+)\)', 
                      r'.\n- **Not \1** (\2)', text)
        
        # Handle "Less likely X because" patterns
        text = re.sub(r'(?<=[.!?])\s*[Ll]ess\s+likely\s+([^.]+)\.', 
                      r'\n\n**Less likely:** \1.\n', text)
        
        # Replace numbered items like "1)" with bullet points (but not within numbers like $5,038)
        text = re.sub(r'(?<![,$\d])(\d+)\)\s*', r'\n  - **\1.** ', text)
        
        # Split on key phrases that indicate new sections
        section_patterns = [
            (r'(?<=[.!?])\s*(Most likely[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(Second most likely[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(Key factors?[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(Key (assumption|disconnect|finding)[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(Why not[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(This reflects?[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(Evidence[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(Bayesian[^:]*?):\s*', r'\n\n**\1:**\n'),
            (r'(?<=[.!?])\s*(However|But |Although)([^.]+)\.', r'\n\n**\1\2.**\n'),
        ]
        
        for pattern, replacement in section_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Clean up any triple+ newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure proper spacing before bullet points
        text = re.sub(r'\n- ', r'\n\n- ', text)
        text = re.sub(r'\n\n\n- ', r'\n\n- ', text)
        
        return text.strip()
    
    def summarize_for_report(self, llm_result: LLMAnalysisResult) -> str:
        """Format LLM analysis for inclusion in report."""
        if not llm_result:
            return "LLM analysis not available."
        
        lines = []
        lines.append("## 🤖 AI-Powered Deep Analysis (Claude)\n")
        lines.append(f"*Generated: {llm_result.generated_at}*\n")
        
        lines.append("### Executive Summary\n")
        lines.append(llm_result.executive_summary)
        lines.append("\n")
        
        lines.append("### Key Findings\n")
        for finding in llm_result.key_findings:
            lines.append(f"- {finding}")
        lines.append("\n")
        
        lines.append("### Attack Probability Assessment\n")
        lines.append(llm_result.attack_probability_assessment)
        lines.append("\n")
        
        # Timeline breakdown (granular)
        if llm_result.timeline_breakdown:
            lines.append("### ⏰ Attack Probability by Timeline\n")
            lines.append("| Timeframe | Probability |")
            lines.append("|-----------|-------------|")
            for timeframe, prob in llm_result.timeline_breakdown.items():
                timeframe_display = timeframe.replace("_", " ").title()
                lines.append(f"| {timeframe_display} | {prob} |")
            lines.append("\n")
        
        if llm_result.likely_dates:
            lines.append("### 📅 Detailed Timeline Predictions\n")
            # Use bullet list format instead of table for full reasoning text
            for date_pred in llm_result.likely_dates:
                date_range = date_pred.get('date_range', 'N/A')
                prob = date_pred.get('probability', 'N/A')
                reason = date_pred.get('reasoning', 'N/A')
                lines.append(f"**{date_range}** — Probability: **{prob}**")
                lines.append(f"> {reason}")
                lines.append("")
            lines.append("\n")
        
        # User opinion summary
        if llm_result.user_opinion_summary:
            lines.append("### 👥 User Opinion Summary\n")
            lines.append(llm_result.user_opinion_summary)
            lines.append("\n")
        
        # Scenario probabilities
        if llm_result.scenario_probabilities:
            lines.append("### 🎯 Scenario Probabilities\n")
            lines.append("| Scenario | Probability |")
            lines.append("|----------|-------------|")
            for scenario, prob in llm_result.scenario_probabilities.items():
                scenario_display = scenario.replace("_", " ").title()
                lines.append(f"| {scenario_display} | {prob} |")
            lines.append("\n")
        
        lines.append("### Scenario Analysis\n")
        lines.append(llm_result.scenarios_analysis)
        lines.append("\n")
        
        # Extended predictions
        if llm_result.extended_predictions:
            lines.append("### 🔮 Extended Predictions\n")
            lines.append("| Prediction | Assessment |")
            lines.append("|------------|------------|")
            pred_labels = {
                "regime_change_probability_2026": "Regime Change in 2026",
                "war_duration_if_occurs": "War Duration (if occurs)",
                "negotiation_success_probability": "Negotiation Success",
                "future_government_most_likely": "Most Likely Future Government",
                "iran_most_resembles": "Iran's Future Most Resembles",
                "safety_note": "Safety Note"
            }
            for key, label in pred_labels.items():
                value = llm_result.extended_predictions.get(key, "N/A")
                lines.append(f"| {label} | {value} |")
            lines.append("\n")
            
            # Add country comparison section
            if llm_result.extended_predictions.get("country_comparison_analysis"):
                lines.append("### Country Comparison Analysis\n")
                lines.append(self._format_analysis_text(
                    llm_result.extended_predictions["country_comparison_analysis"]))
                lines.append("\n")
        
        lines.append("### Detailed Reasoning\n")
        lines.append(self._format_analysis_text(llm_result.reasoning))
        lines.append("\n")
        
        lines.append("### Reddit vs Polymarket Analysis\n")
        lines.append(self._format_analysis_text(llm_result.comparison_with_polymarket))
        lines.append("\n")
        
        lines.append("### Uncertainties & Caveats\n")
        for uncertainty in llm_result.uncertainties:
            lines.append(f"- {uncertainty}")
        lines.append("\n")
        
        lines.append("### 🎯 Final Verdict\n")
        lines.append(f"**{llm_result.final_verdict}**")
        lines.append("\n")
        
        return "\n".join(lines)
