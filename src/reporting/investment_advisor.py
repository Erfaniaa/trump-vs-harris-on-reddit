"""
Investment Advisor Module
Provides investment recommendations based on Iran-US conflict analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class AssetRecommendation:
    """Recommendation for a specific asset."""
    asset_name: str
    ticker: str
    action: str  # "BUY", "HOLD", "SELL", "SHORT", "AVOID"
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    target_price: Optional[str] = None
    entry_price: Optional[str] = None
    reasoning: str = ""
    risk_level: str = "MEDIUM"


@dataclass
class PortfolioAllocation:
    """Suggested portfolio allocation."""
    category: str
    percentage: float
    assets: List[str]
    reasoning: str


class InvestmentAdvisor:
    """Provides investment advice based on geopolitical analysis."""
    
    # Current market data (Feb 4, 2026)
    CURRENT_PRICES = {
        "gold": {"price": 5038, "unit": "USD/oz", "change_24h": 1.88, "change_yoy": 67},
        "bitcoin": {"price": 76500, "unit": "USD", "change_24h": -2.1, "change_yoy": -15},
        "oil_brent": {"price": 78.50, "unit": "USD/barrel", "change_24h": 1.2, "change_yoy": 5},
        "usd_index": {"price": 108.5, "unit": "DXY", "change_24h": 0.3, "change_yoy": 8},
        "eur_usd": {"price": 1.03, "unit": "EUR/USD", "change_24h": -0.2, "change_yoy": -7},
        "usd_cny": {"price": 7.32, "unit": "USD/CNY", "change_24h": 0.1, "change_yoy": 3},
    }
    
    def __init__(self, attack_probability: float = 0.35, timeline_months: int = 6):
        """
        Initialize advisor.
        
        Args:
            attack_probability: Probability of US-Iran military conflict (0-1)
            timeline_months: Expected timeline for potential conflict
        """
        self.attack_probability = attack_probability
        self.timeline_months = timeline_months
    
    def get_safe_haven_recommendations(self) -> List[AssetRecommendation]:
        """Get safe haven asset recommendations."""
        recommendations = []
        
        # Gold - Primary safe haven
        recommendations.append(AssetRecommendation(
            asset_name="Gold",
            ticker="GLD, IAU, or Physical Gold",
            action="BUY",
            confidence="HIGH",
            entry_price="$4,800-5,200/oz (current: $5,038)",
            target_price="$5,500-6,000/oz if conflict escalates",
            reasoning="""
            - Gold up 67% YoY, strongest gain since 1979
            - Central banks buying aggressively (China, Russia, emerging markets)
            - Historical correlation: +4% in one week during June 2025 Israel attack
            - If US strikes Iran, expect immediate 5-10% spike
            - Safe haven during both inflation AND deflation scenarios
            - Recommended allocation: 10-15% of portfolio
            """,
            risk_level="LOW"
        ))
        
        # Silver
        recommendations.append(AssetRecommendation(
            asset_name="Silver",
            ticker="SLV, PSLV, or Physical Silver",
            action="BUY",
            confidence="MEDIUM",
            entry_price="$28-32/oz",
            target_price="$40-50/oz in conflict scenario",
            reasoning="""
            - Silver rose 141% in 2025
            - Higher volatility than gold but more upside
            - Industrial demand from solar/electronics
            - More accessible for smaller investors
            - Recommended allocation: 3-5% of portfolio
            """,
            risk_level="MEDIUM"
        ))
        
        # Swiss Franc
        recommendations.append(AssetRecommendation(
            asset_name="Swiss Franc",
            ticker="FXF or CHF holdings",
            action="BUY",
            confidence="MEDIUM",
            entry_price="Current levels (0.88 USD/CHF)",
            target_price="0.80 USD/CHF in crisis",
            reasoning="""
            - Traditional safe haven currency
            - Swiss neutrality valuable during conflicts
            - Alternative to USD if dollar weakens
            - Recommended allocation: 5-10% of cash
            """,
            risk_level="LOW"
        ))
        
        return recommendations
    
    def get_energy_recommendations(self) -> List[AssetRecommendation]:
        """Get energy sector recommendations."""
        recommendations = []
        
        # Oil
        recommendations.append(AssetRecommendation(
            asset_name="Brent Crude Oil",
            ticker="BNO, USO",
            action="BUY",
            confidence="HIGH",
            entry_price="$75-80/barrel (current: $78.50)",
            target_price="$100-120/barrel if Strait of Hormuz disrupted",
            reasoning="""
            - 20% of global oil transits Strait of Hormuz
            - Iran can disrupt shipping even without full blockade
            - Any military action = immediate supply fears
            - IRGC has demonstrated naval capabilities
            - Recommended allocation: 5-8% of portfolio
            """,
            risk_level="HIGH"
        ))
        
        # Energy majors
        recommendations.append(AssetRecommendation(
            asset_name="Energy Majors",
            ticker="XOM, CVX, XLE (ETF)",
            action="BUY",
            confidence="HIGH",
            entry_price="XLE around $85-90",
            target_price="XLE $110+ in supply crisis",
            reasoning="""
            - ExxonMobil (XOM): $105-110, dividend yield ~3.5%
            - Chevron (CVX): $150-155, strong cash flow
            - Non-Iranian oil companies benefit from supply disruption
            - Strong balance sheets, can weather volatility
            - Recommended allocation: 5-7% of portfolio
            """,
            risk_level="MEDIUM"
        ))
        
        return recommendations
    
    def get_defense_recommendations(self) -> List[AssetRecommendation]:
        """Get defense sector recommendations."""
        recommendations = []
        
        recommendations.append(AssetRecommendation(
            asset_name="Defense ETF",
            ticker="ITA (iShares U.S. Aerospace & Defense)",
            action="BUY",
            confidence="HIGH",
            entry_price="$130-140 range",
            target_price="$160+ in extended conflict",
            reasoning="""
            - Defense spending increases regardless of conflict outcome
            - Bipartisan support for military spending
            - Long-term contracts provide revenue stability
            - Top holdings: RTX, LMT, GD, NOC
            - Recommended allocation: 5-7% of portfolio
            """,
            risk_level="LOW"
        ))
        
        recommendations.append(AssetRecommendation(
            asset_name="Raytheon Technologies",
            ticker="RTX",
            action="BUY",
            confidence="HIGH",
            entry_price="$115-120",
            target_price="$140+ in conflict",
            reasoning="""
            - Leader in air defense systems (Patriot, THAAD)
            - Tomahawk cruise missiles used in strikes
            - Strong order backlog
            - Dividend yield ~2.5%
            """,
            risk_level="MEDIUM"
        ))
        
        return recommendations
    
    def get_avoid_recommendations(self) -> List[AssetRecommendation]:
        """Get assets to avoid or short."""
        recommendations = []
        
        # Airlines
        recommendations.append(AssetRecommendation(
            asset_name="Airlines",
            ticker="JETS ETF, UAL, DAL, AAL",
            action="AVOID/SHORT",
            confidence="HIGH",
            reasoning="""
            - Oil price spikes crush margins
            - Middle East route disruptions
            - Insurance costs increase
            - Consumer demand drops during uncertainty
            - Consider shorting JETS ETF
            """,
            risk_level="HIGH"
        ))
        
        # Shipping
        recommendations.append(AssetRecommendation(
            asset_name="Container Shipping",
            ticker="ZIM, SBLK",
            action="AVOID",
            confidence="MEDIUM",
            reasoning="""
            - Suez/Hormuz disruption risks
            - Already impacted by Houthi attacks
            - High volatility, difficult to time
            - Better alternatives available
            """,
            risk_level="HIGH"
        ))
        
        # Emerging Markets exposed to Iran
        recommendations.append(AssetRecommendation(
            asset_name="Turkey/UAE Exposure",
            ticker="TUR ETF, UAE ETF",
            action="AVOID",
            confidence="MEDIUM",
            reasoning="""
            - Geographic proximity to conflict
            - Trade disruption risk
            - Currency volatility
            - Refugee/humanitarian crisis spillover
            """,
            risk_level="HIGH"
        ))
        
        # High-risk crypto
        recommendations.append(AssetRecommendation(
            asset_name="High-risk Cryptocurrencies",
            ticker="Altcoins, memecoins",
            action="AVOID",
            confidence="HIGH",
            reasoning="""
            - Bitcoin dropped to $76K (not safe haven in short term)
            - Risk-off sentiment hurts crypto
            - IRGC uses crypto for sanctions evasion - regulatory risk
            - Stick to BTC/ETH only if any, with small allocation
            """,
            risk_level="VERY HIGH"
        ))
        
        return recommendations
    
    def get_currency_recommendations(self) -> List[AssetRecommendation]:
        """Get currency recommendations."""
        recommendations = []
        
        recommendations.append(AssetRecommendation(
            asset_name="US Dollar Cash",
            ticker="USD",
            action="HOLD",
            confidence="MEDIUM",
            reasoning="""
            - Dollar benefits initially from flight to safety
            - But long-term: deficit concerns, de-dollarization
            - Keep 20-30% in USD cash for liquidity
            - Don't go all-in on dollar
            """,
            risk_level="LOW"
        ))
        
        recommendations.append(AssetRecommendation(
            asset_name="Euro",
            ticker="EUR",
            action="HOLD",
            confidence="LOW",
            reasoning="""
            - European economy weak
            - But less directly exposed to Iran conflict
            - Diversification value
            - Keep 10-15% in EUR
            """,
            risk_level="MEDIUM"
        ))
        
        recommendations.append(AssetRecommendation(
            asset_name="Chinese Yuan",
            ticker="CNY/CNH",
            action="AVOID",
            confidence="MEDIUM",
            reasoning="""
            - China-Iran alliance complicates things
            - Potential secondary sanctions risk
            - Yuan not freely convertible
            - Better alternatives exist
            """,
            risk_level="HIGH"
        ))
        
        return recommendations
    
    def get_us_stock_recommendations(self) -> List[AssetRecommendation]:
        """Get US stock market recommendations based on Iran conflict analysis."""
        recommendations = []
        
        # S&P 500 Index
        recommendations.append(AssetRecommendation(
            asset_name="S&P 500 Index",
            ticker="SPY, VOO, IVV",
            action="HOLD/UNDERWEIGHT",
            confidence="MEDIUM",
            entry_price="SPY $580-590 range (current: ~$589)",
            target_price="$560-570 if conflict escalates, $620+ if diplomacy succeeds",
            reasoning="""
            - S&P 500 at 5,892 with P/E of 22.8 (above historical avg of 18)
            - VIX at 24.5 indicates elevated fear
            - June 2025 strikes caused -4.4% drop, recovered in 2 weeks
            - Limited strike = 5-7% correction, full war = 10-15% drop
            - Defensive positioning recommended until clarity
            - Consider selling 10-20% to raise cash for opportunities
            """,
            risk_level="MEDIUM"
        ))
        
        # NASDAQ/Tech
        recommendations.append(AssetRecommendation(
            asset_name="NASDAQ/Technology",
            ticker="QQQ, XLK, AAPL, MSFT, GOOGL",
            action="UNDERWEIGHT",
            confidence="HIGH",
            entry_price="QQQ below $420 would be attractive",
            target_price="Wait for 10%+ correction to add",
            reasoning="""
            - Tech hit hardest in risk-off environment
            - NASDAQ -4.2% week, -6.8% month
            - High valuations (P/E 28.5) vulnerable to de-rating
            - Supply chain concerns if conflict spreads
            - Rate sensitivity if Fed delays cuts
            - Reduce to 60-70% of normal tech allocation
            """,
            risk_level="HIGH"
        ))
        
        # Defensive Sectors - Healthcare
        recommendations.append(AssetRecommendation(
            asset_name="Healthcare Sector",
            ticker="XLV, JNJ, UNH, PFE, MRK",
            action="OVERWEIGHT",
            confidence="HIGH",
            entry_price="XLV $135-140 range",
            target_price="Stable; outperformance through relative strength",
            reasoning="""
            - Defensive characteristics during uncertainty
            - Stable demand regardless of geopolitics
            - Strong balance sheets and dividends
            - Less correlated with oil prices
            - Recommended: 15% of equity allocation
            - Top picks: UNH, JNJ, MRK for stability
            """,
            risk_level="LOW"
        ))
        
        # Utilities
        recommendations.append(AssetRecommendation(
            asset_name="Utilities Sector",
            ticker="XLU, NEE, DUK, SO",
            action="OVERWEIGHT",
            confidence="HIGH",
            entry_price="XLU $68-72 range",
            target_price="Stable income, 3%+ dividend yield",
            reasoning="""
            - Classic defensive sector
            - Regulated revenue = predictable
            - High dividend yields (3-4%)
            - Low beta, reduced volatility
            - Recommended: 8-10% of equity allocation
            - Best for risk-averse investors
            """,
            risk_level="LOW"
        ))
        
        # Consumer Staples
        recommendations.append(AssetRecommendation(
            asset_name="Consumer Staples",
            ticker="XLP, PG, KO, PEP, WMT",
            action="OVERWEIGHT",
            confidence="MEDIUM",
            entry_price="XLP $76-80 range",
            target_price="Defensive outperformance in downturn",
            reasoning="""
            - Essential goods demand is inelastic
            - Strong pricing power (inflation hedge)
            - Reliable dividends (2-3%)
            - Geographic diversification (global brands)
            - Recommended: 8-10% of equity allocation
            - Top picks: PG, KO, WMT
            """,
            risk_level="LOW"
        ))
        
        # Financials
        recommendations.append(AssetRecommendation(
            asset_name="Financial Sector",
            ticker="XLF, JPM, BAC, GS",
            action="NEUTRAL",
            confidence="MEDIUM",
            entry_price="XLF $42-44 range",
            target_price="Mixed outlook; rate and credit concerns",
            reasoning="""
            - Rate volatility creates uncertainty
            - Credit risk if economy weakens
            - Trading desks may benefit from volatility
            - Big banks well-capitalized
            - Neutral weight; favor JPM, MS over regional banks
            - Watch for credit spreads widening
            """,
            risk_level="MEDIUM"
        ))
        
        # Consumer Discretionary - AVOID
        recommendations.append(AssetRecommendation(
            asset_name="Consumer Discretionary",
            ticker="XLY, AMZN, TSLA, HD",
            action="UNDERWEIGHT",
            confidence="HIGH",
            entry_price="Wait for significant pullback",
            target_price="Avoid until conflict clarity",
            reasoning="""
            - Sensitive to consumer confidence
            - Oil price spike = reduced spending
            - Already -3.5% week, -5.8% month
            - Tesla particularly vulnerable (Musk-Iran diplomacy)
            - Travel, leisure stocks worst hit
            - Reduce to 50% of normal allocation
            """,
            risk_level="HIGH"
        ))
        
        # Small Cap - AVOID
        recommendations.append(AssetRecommendation(
            asset_name="Small Cap Stocks",
            ticker="IWM, VTWO",
            action="AVOID",
            confidence="HIGH",
            entry_price="Wait for VIX < 18 to add",
            target_price="Risk/reward unfavorable",
            reasoning="""
            - Small caps suffer most in risk-off
            - Less liquid, wider spreads
            - More domestic focused but supply chain risk
            - IWM underperforming large cap YTD
            - Reduce small cap to 5-8% maximum
            - Favor quality over speculation
            """,
            risk_level="HIGH"
        ))
        
        # Real Estate - CAUTION
        recommendations.append(AssetRecommendation(
            asset_name="Real Estate",
            ticker="VNQ, XLRE, AMT, SPG",
            action="UNDERWEIGHT",
            confidence="MEDIUM",
            entry_price="VNQ $85-90 for long-term",
            target_price="Rate sensitive; wait for clarity",
            reasoning="""
            - Interest rate sensitive
            - Commercial real estate concerns
            - Office/retail challenged
            - Data centers (AMT) and industrial more defensive
            - Reduce to 3-5% of portfolio
            - Prefer residential over commercial
            """,
            risk_level="MEDIUM"
        ))
        
        return recommendations
    
    def get_stock_sector_allocation(self) -> Dict[str, Dict]:
        """Get recommended stock sector allocation for conflict scenario."""
        return {
            "overweight": {
                "Energy (XLE)": {"target": 12, "current_typical": 5, "reasoning": "Direct conflict hedge"},
                "Defense (ITA)": {"target": 8, "current_typical": 2, "reasoning": "Military spending increase"},
                "Healthcare (XLV)": {"target": 15, "current_typical": 12, "reasoning": "Defensive stability"},
                "Utilities (XLU)": {"target": 8, "current_typical": 3, "reasoning": "Safe haven sector"},
                "Consumer Staples (XLP)": {"target": 10, "current_typical": 6, "reasoning": "Defensive demand"},
                "Materials (XLB)": {"target": 5, "current_typical": 3, "reasoning": "Commodity exposure"},
            },
            "neutral": {
                "Financials (XLF)": {"target": 10, "current_typical": 12, "reasoning": "Mixed outlook"},
                "Industrials (XLI)": {"target": 8, "current_typical": 9, "reasoning": "Defense offset by general weakness"},
            },
            "underweight": {
                "Technology (XLK)": {"target": 18, "current_typical": 30, "reasoning": "Risk-off selling, high valuations"},
                "Consumer Discretionary (XLY)": {"target": 4, "current_typical": 10, "reasoning": "Consumer confidence impact"},
                "Communication Services (XLC)": {"target": 5, "current_typical": 9, "reasoning": "Ad spending cuts"},
                "Real Estate (XLRE)": {"target": 2, "current_typical": 3, "reasoning": "Rate sensitivity"},
            },
            "total_equity_allocation": "60-70% of portfolio (vs 80% normal)",
            "cash_buffer": "20-30% in cash/short-term bonds",
            "rebalance_triggers": [
                "VIX > 35: Reduce equity to 50%",
                "VIX < 18: Increase equity to 75%",
                "S&P drops 10%: Deploy cash opportunistically",
                "Diplomatic breakthrough: Rotate to growth/tech"
            ]
        }
    
    def get_suggested_portfolio(self) -> List[PortfolioAllocation]:
        """Get suggested portfolio allocation for current environment."""
        return [
            PortfolioAllocation(
                category="Cash & Cash Equivalents",
                percentage=25.0,
                assets=["USD (60%)", "EUR (25%)", "CHF (15%)"],
                reasoning="High liquidity for opportunities and emergencies. Mixed currencies reduce single-currency risk."
            ),
            PortfolioAllocation(
                category="Precious Metals",
                percentage=15.0,
                assets=["Gold (80%)", "Silver (20%)"],
                reasoning="Primary safe haven. Gold for stability, silver for upside potential."
            ),
            PortfolioAllocation(
                category="Energy",
                percentage=12.0,
                assets=["XLE ETF", "XOM", "CVX", "Oil futures/BNO"],
                reasoning="Direct hedge against Middle East disruption. Strong cash flows."
            ),
            PortfolioAllocation(
                category="Defense & Aerospace",
                percentage=10.0,
                assets=["ITA ETF", "RTX", "LMT", "GD"],
                reasoning="Benefits regardless of conflict outcome. Long-term government contracts."
            ),
            PortfolioAllocation(
                category="US Stock Market (Defensive)",
                percentage=20.0,
                assets=["Healthcare (XLV)", "Utilities (XLU)", "Consumer Staples (XLP)"],
                reasoning="Defensive sectors with stable demand. Lower beta during volatility."
            ),
            PortfolioAllocation(
                category="International Developed",
                percentage=8.0,
                assets=["Japan (EWJ)", "Switzerland (EWL)", "Australia (EWA)"],
                reasoning="Geographic diversification. Less directly exposed to Middle East."
            ),
            PortfolioAllocation(
                category="Bonds & Fixed Income",
                percentage=10.0,
                assets=["Short-term Treasuries (SHY)", "TIPS", "Investment Grade Corporate"],
                reasoning="Capital preservation. Short duration reduces interest rate risk."
            ),
        ]

    def get_suggested_portfolio_no_us_stocks(self) -> List[PortfolioAllocation]:
        """Alternative allocation for readers without access to the US stock market."""
        return [
            PortfolioAllocation(
                category="Cash & FX",
                percentage=30.0,
                assets=["USD (55%)", "EUR (30%)", "CHF (15%)"],
                reasoning="High liquidity and diversification away from single-currency risk."
            ),
            PortfolioAllocation(
                category="Precious Metals",
                percentage=25.0,
                assets=["Gold (80%)", "Silver (20%)"],
                reasoning="Primary safe haven in geopolitical stress and inflation shocks."
            ),
            PortfolioAllocation(
                category="Energy & Commodities",
                percentage=12.0,
                assets=["Brent-linked exposure", "Energy/commodity ETCs where available"],
                reasoning="Direct hedge against Middle East supply risk without US equities."
            ),
            PortfolioAllocation(
                category="Crypto (High Risk)",
                percentage=10.0,
                assets=["BTC (70%)", "ETH (30%)"],
                reasoning="Optional risk basket; size small due to volatility."
            ),
            PortfolioAllocation(
                category="Non-US Equities",
                percentage=15.0,
                assets=["Europe/Asia ex-US funds", "Local accessible equity indices"],
                reasoning="Equity exposure without US stock market access."
            ),
            PortfolioAllocation(
                category="Fixed Income / Money Market",
                percentage=8.0,
                assets=["Short-duration funds", "Local high-quality bonds"],
                reasoning="Stability and drawdown control."
            ),
        ]
    
    def get_advice_for_iranians(self) -> Dict[str, str]:
        """Get specific advice for people in Iran."""
        return {
            "immediate_priorities": """
            1. **اینترنت و ارتباطات:**
               - VPN های مطمئن نصب کنید (قبل از قطعی)
               - شماره تماس اضطراری خارج از ایران داشته باشید
               - Starlink اگر دسترسی دارید (ماسک در حال مذاکره برای ایران)
            
            2. **نقدینگی:**
               - دلار نقد نگه دارید (بهتر از ریال)
               - طلای فیزیکی (سکه/شمش) - قابل حمل
               - مقداری یورو برای تنوع
            
            3. **دارایی‌های دیجیتال:**
               - بیت‌کوین در کیف‌پول شخصی (نه صرافی ایرانی)
               - Tether (USDT) برای نقدینگی فوری
               - کلیدهای خصوصی رو امن نگه دارید
            """,
            
            "asset_protection": """
            **محافظت از دارایی:**
            
            1. **طلا:**
               - سکه امامی/بهار آزادی - نقدشوندگی بالا
               - شمش کوچک (5-10 گرمی) - راحت‌تر برای فروش
               - طلای 18 عیار مصنوعات - کمتر توصیه می‌شه
            
            2. **ارز:**
               - دلار آمریکا (اولویت اول)
               - یورو (اولویت دوم)
               - درهم امارات (اگر به دبی دسترسی دارید)
            
            3. **کریپتو:**
               - BTC: 50% از سبد کریپتو
               - USDT: 40% برای نقدینگی
               - ETH: 10% برای تنوع
            
            4. **اجتناب کنید:**
               - سپرده بانکی ریالی (تورم می‌خوره)
               - املاک (غیرنقدشونده در بحران)
               - سهام بورس تهران (ریسک تعطیلی)
            """,
            
            "emergency_planning": """
            **برنامه‌ریزی اضطراری:**
            
            1. **مدارک:**
               - پاسپورت معتبر (حتماً تمدید کنید)
               - کپی مدارک در فضای ابری امن
               - مدارک تحصیلی/شغلی ترجمه شده
            
            2. **مسیرهای خروج:**
               - ترکیه (ساده‌ترین، بدون ویزا)
               - امارات (اگر ویزا دارید)
               - ارمنستان/گرجستان (گزینه‌های جایگزین)
            
            3. **شبکه ارتباطی:**
               - تماس با خویشاوندان خارج
               - گروه‌های تلگرامی اضطراری
               - شماره سفارتخانه‌ها (اگر شهروند دوم دارید)
            
            4. **ملزومات اضطراری:**
               - دارو و لوازم پزشکی (2-3 ماه)
               - آب و غذای بسته‌بندی
               - باتری و شارژر خورشیدی
            """,
            
            "what_not_to_do": """
            **کارهایی که نباید انجام دهید:**
            
            ❌ تمام پول را در یک جا نگذارید
            ❌ به صرافی‌های ایرانی اعتماد نکنید (ریسک مسدودی)
            ❌ طلا را در صندوق امانات بانک نگذارید
            ❌ دلار را در منزل انباشت نکنید (سرقت)
            ❌ در شبکه‌های اجتماعی اظهارنظر سیاسی نکنید
            ❌ به وعده‌های سود بالا اعتماد نکنید
            """,
            
            "timeline_advice": """
            **توصیه بر اساس تایم‌لاین:**
            
            📅 **فوری (این هفته):**
            - VPN نصب کنید
            - مقداری دلار نقد تهیه کنید
            
            📅 **کوتاه‌مدت (این ماه):**
            - طلا بخرید (حتی کم)
            - پاسپورت تمدید کنید
            
            📅 **میان‌مدت (1-3 ماه):**
            - برنامه خروج اضطراری داشته باشید
            - سبد دارایی متنوع کنید
            """
        }
    
    def get_detailed_gold_analysis(self) -> str:
        """Detailed gold analysis with mathematical formulas."""
        gold_price = self.CURRENT_PRICES["gold"]["price"]
        gold_yoy = self.CURRENT_PRICES["gold"]["change_yoy"]
        
        return f"""
### 📐 تحلیل ریاضی طلا / Mathematical Gold Analysis

**قیمت فعلی:** ${gold_price:,}/oz
**تغییر سالانه:** +{gold_yoy}%

#### فرمول تعیین قیمت هدف:

```
1. قیمت پایه (بدون بحران): $3,000/oz (میانگین 12 ماه قبل از تنش)

2. ضریب ریسک ژئوپلیتیکی (GRF):
   GRF = 1 + (P_conflict × Impact_Factor)
   
   Where:
   - P_conflict = {self.attack_probability:.0%} (احتمال درگیری)
   - Impact_Factor = 0.50 (تأثیر تاریخی جنگ بر طلا)
   
   GRF = 1 + ({self.attack_probability:.2f} × 0.50) = {1 + self.attack_probability * 0.50:.2f}

3. قیمت هدف در صورت درگیری:
   Target = Base × GRF × Conflict_Spike
   Target = $3,000 × {1 + self.attack_probability * 0.50:.2f} × 1.15
   Target = ${3000 * (1 + self.attack_probability * 0.50) * 1.15:,.0f}/oz

4. قیمت هدف بدون درگیری:
   Target = $3,000 × 1.10 (رشد طبیعی)
   Target = $3,300/oz
```

#### سطوح کلیدی خرید و فروش:

| سطح | قیمت | اقدام | دلیل |
|-----|------|-------|------|
| **حمایت قوی** | $4,500 | خرید سنگین | کف 3 ماهه، حمایت تکنیکال |
| **حمایت میان** | $4,800 | خرید | اصلاح سالم، خط روند صعودی |
| **قیمت فعلی** | ${gold_price:,} | نگه‌داری | منتظر اصلاح یا شکست |
| **مقاومت اول** | $5,200 | کاهش موقعیت | مقاومت روانی |
| **مقاومت دوم** | $5,500 | سیو سود جزئی | سقف تاریخی |
| **هدف بحران** | $6,000+ | سیو سود کامل | اوج هیجانی |

#### ریسک/بازده (Risk/Reward):

```
Entry: $5,038 (فعلی)
Stop Loss: $4,500 (-10.7%)
Target 1: $5,500 (+9.2%)
Target 2: $6,000 (+19.1%)

Risk/Reward Ratio (Target 1): 0.86 (نه چندان جذاب)
Risk/Reward Ratio (Target 2): 1.78 (قابل قبول)

توصیه: منتظر اصلاح به $4,800 باشید برای ورود بهتر
```
"""
    
    def get_detailed_btc_analysis(self) -> str:
        """Detailed Bitcoin analysis with mathematical formulas."""
        btc_price = self.CURRENT_PRICES["bitcoin"]["price"]
        btc_24h = self.CURRENT_PRICES["bitcoin"]["change_24h"]
        
        return f"""
### 📐 تحلیل ریاضی بیت‌کوین / Mathematical Bitcoin Analysis

**قیمت فعلی:** ${btc_price:,}
**تغییر 24 ساعته:** {btc_24h:+.1f}%

#### چرا بیت‌کوین Safe Haven نیست (در کوتاه‌مدت):

```
همبستگی بیت‌کوین با دارایی‌های ریسکی:

Correlation(BTC, NASDAQ) = 0.72 (همبستگی بالا)
Correlation(BTC, Gold) = 0.15 (همبستگی پایین)
Correlation(BTC, VIX) = -0.45 (منفی = ریسکی)

نتیجه: در بحران، BTC مثل سهام تکنولوژی آمریکا رفتار می‌کنه، نه طلا
```

#### سطوح کلیدی:

| سطح | قیمت | اقدام | دلیل |
|-----|------|-------|------|
| **حمایت بحرانی** | $60,000 | خرید سنگین (اگر می‌رسه) | کف چرخه، حمایت تاریخی |
| **حمایت قوی** | $68,000 | خرید | میانگین 200 روزه |
| **حمایت میان** | $72,000 | خرید جزئی | حمایت روانی |
| **قیمت فعلی** | ${btc_price:,} | نگه‌داری/فروش جزئی | عدم قطعیت |
| **مقاومت اول** | $82,000 | کاهش موقعیت | مقاومت قبلی |
| **مقاومت دوم** | $90,000 | سیو سود | نزدیک ATH |
| **ATH** | $109,000 | فروش کامل | هدف صعودی |

#### استراتژی پیشنهادی برای BTC:

```
سناریوی 1: جنگ (P = {self.attack_probability:.0%})
  - BTC احتمالاً به $60-68K می‌رسه (کاهش 15-25%)
  - فروش فعلی منطقی است
  - خرید مجدد در $65K

سناریوی 2: بدون جنگ (P = {1-self.attack_probability:.0%})
  - BTC ممکنه به $90K برسه
  - نگه‌داری منطقی است

ارزش انتظاری (Expected Value):
EV = P_war × Price_war + P_peace × Price_peace
EV = {self.attack_probability:.2f} × $65,000 + {1-self.attack_probability:.2f} × $90,000
EV = ${self.attack_probability * 65000 + (1-self.attack_probability) * 90000:,.0f}

مقایسه با قیمت فعلی: ${btc_price:,}
توصیه: {'فروش (EV < قیمت فعلی)' if self.attack_probability * 65000 + (1-self.attack_probability) * 90000 < btc_price else 'نگه‌داری (EV > قیمت فعلی)'}
```
"""
    
    def get_detailed_currency_analysis(self) -> str:
        """Detailed currency analysis."""
        return f"""
### 📐 تحلیل ارزها / Currency Analysis

#### 1. ریال ایران (IRR) ⚠️ فروش فوری

```
قیمت فعلی: ~850,000 تومان/دلار
کاهش ارزش از 2018: -95%
پیش‌بینی در صورت جنگ: 1,200,000+ تومان/دلار

فرمول کاهش ارزش:
Value_loss = (Initial - Current) / Initial
Value_loss = (42,000 - 850,000) / 42,000 = -1,926% (20 برابر کاهش)

توصیه: هر چقدر ریال دارید تبدیل به دلار/طلا کنید
```

#### 2. دلار آمریکا (USD) 📈 خرید/نگه‌داری

```
DXY (شاخص دلار): 108.5
تغییر سالانه: +8%

چرا دلار قوی می‌مونه:
- Flight to safety در بحران
- نرخ بهره بالا (5.25%)
- رکود اروپا/چین

چرا ممکنه ضعیف بشه:
- کسری بودجه عظیم آمریکا
- De-dollarization (چین/روسیه)
- تورم بالقوه

توصیه: 40-50% نقدینگی در USD نگه دارید
```

#### 3. یورو (EUR) 📊 نگه‌داری

```
EUR/USD: 1.03
کمترین از 2002

مشکلات:
- رکود آلمان
- بحران انرژی
- جنگ اوکراین

مزایا:
- کمتر درگیر ایران
- تنوع از USD

توصیه: 15-20% در EUR (برای تنوع)
```

#### 4. یوآن چین (CNY) ⚠️ اجتناب

```
USD/CNY: 7.32

خطرات:
- تحریم‌های ثانویه (اگر چین به ایران کمک کنه)
- غیرقابل تبدیل آزاد
- کنترل سرمایه دولتی
- شفافیت پایین

توصیه: اجتناب کنید مگر تجارت مستقیم با چین دارید
```

#### 5. فرانک سوئیس (CHF) 🛡️ Safe Haven

```
USD/CHF: 0.88

مزایا:
- بی‌طرفی تاریخی سوئیس
- ثبات اقتصادی
- Safe haven کلاسیک

معایب:
- بازده پایین (نرخ بهره منفی/صفر)

توصیه: 5-10% در CHF (بیمه پورتفولیو)
```

#### جدول خلاصه ارزها:

| ارز | اقدام | درصد پورتفولیو | قیمت خرید | قیمت فروش |
|-----|-------|----------------|-----------|-----------|
| IRR | ❌ فروش فوری | 0% | - | همین الان |
| USD | ✅ خرید | 40-50% | همیشه | >115 DXY |
| EUR | 📊 نگه‌داری | 15-20% | <1.00 | >1.15 |
| CHF | ✅ خرید | 5-10% | همیشه | >1.00 USD/CHF |
| CNY | ⚠️ اجتناب | 0-5% | - | - |
| GBP | 📊 نگه‌داری | 5-10% | <1.20 | >1.35 |
"""
    
    def get_short_recommendations(self) -> str:
        """Detailed short selling recommendations."""
        return """
### 📉 توصیه‌های شورت (Short) / What to Short

#### 1. شورت هواپیمایی (JETS ETF)

```
قیمت فعلی: ~$18
هدف شورت: $14 (-22%)
Stop Loss: $20 (+11%)
Risk/Reward: 2.0

چرا شورت؟
- قیمت نفت بالا = هزینه سوخت بالا
- مسیرهای خاورمیانه مختل
- بیمه گران‌تر
- کاهش تقاضا در بحران

نحوه اجرا:
- خرید PUT option (کم‌ریسک‌تر)
- فروش استقراضی (پرریسک)
- Inverse ETF اگر موجود
```

#### 2. شورت شرکت‌های کشتیرانی (ZIM, SBLK)

```
ZIM قیمت فعلی: ~$15
هدف شورت: $10 (-33%)

چرا شورت؟
- اختلال تنگه هرمز
- حملات حوثی‌ها ادامه دارد
- بیمه کشتی‌ها گران شده
- مسیرهای جایگزین پرهزینه
```

#### 3. شورت EM ETF های خاورمیانه

```
TUR (ترکیه): ریسک مرزی با ایران
UAE ETF: وابستگی تجاری به ایران

چرا شورت؟
- نزدیکی جغرافیایی
- فرار سرمایه
- بحران پناهندگی احتمالی
```

#### 4. شورت بانک‌های اروپایی (در صورت تشدید)

```
فقط اگر جنگ شروع شد:
- بانک‌های با اکسپوژر به نفت
- بانک‌های ترکیه

دلیل: بحران بدهی + ریسک اعتباری
```

#### ⚠️ هشدار شورت:

```
شورت فروشی پرریسک است:
- ضرر نامحدود (تئوری)
- هزینه استقراض
- Short squeeze risk

توصیه:
- از PUT options استفاده کنید (ضرر محدود)
- حداکثر 5-10% پورتفولیو
- Stop loss حتماً بگذارید
```
"""
    
    def get_short_positions_no_leverage(self) -> List[Dict[str, str]]:
        """Scenario-based short ideas without leverage."""
        return [
            {
                "position": "Airlines (JETS) / Travel",
                "horizon": "Short-term (2-8 weeks)",
                "conditions": "Oil > $95 and escalation headlines",
                "rationale": "Fuel cost surge + route disruption + demand shock",
                "risk": "HIGH",
                "confidence": "MEDIUM",
                "implementation": "Use 1x inverse ETF or reduce exposure (no leverage)",
            },
            {
                "position": "Shipping (ZIM, SBLK)",
                "horizon": "Short-term (1-3 months)",
                "conditions": "Hormuz risk + insurance premiums rising",
                "rationale": "Shipping costs rise, routes disrupted, margins compress",
                "risk": "HIGH",
                "confidence": "MEDIUM",
                "implementation": "1x inverse ETF (if available) or trim holdings",
            },
            {
                "position": "Middle East EM ETFs",
                "horizon": "Medium-term (3-6 months)",
                "conditions": "Regional spillover + capital outflows",
                "rationale": "Geo-risk repricing + liquidity stress",
                "risk": "MEDIUM",
                "confidence": "LOW-MEDIUM",
                "implementation": "Avoid/underweight or use 1x inverse if accessible",
            },
            {
                "position": "European banks (energy exposure)",
                "horizon": "Long-term (6-12 months)",
                "conditions": "Sustained oil shock + credit stress",
                "rationale": "Rising default risk and funding stress in downturn",
                "risk": "MEDIUM-HIGH",
                "confidence": "LOW",
                "implementation": "Avoid/underweight; no leverage short only",
            },
        ]
    
    def get_mathematical_portfolio_optimization(self) -> str:
        """Portfolio optimization with math."""
        return f"""
### 📐 بهینه‌سازی پورتفولیو / Portfolio Optimization

#### Modern Portfolio Theory (MPT):

```
هدف: حداکثر بازده با حداقل ریسک

فرمول Sharpe Ratio:
S = (R_p - R_f) / σ_p

Where:
- R_p = بازده پورتفولیو
- R_f = نرخ بدون ریسک (5% فعلی)
- σ_p = انحراف معیار پورتفولیو

Sharpe Ratio هدف: > 1.0 (خوب), > 2.0 (عالی)
```

#### تخصیص پیشنهادی با توجه به P(جنگ) = {self.attack_probability:.0%}:

```
فرمول تخصیص:

Safe_Haven_Allocation = Base_SH + (P_war × Adjustment)
Safe_Haven_Allocation = 15% + ({self.attack_probability:.2f} × 20%)
Safe_Haven_Allocation = {15 + self.attack_probability * 20:.0f}%

Risk_Asset_Allocation = 100% - Safe_Haven - Cash
Risk_Asset_Allocation = 100% - {15 + self.attack_probability * 20:.0f}% - 25%
Risk_Asset_Allocation = {100 - (15 + self.attack_probability * 20) - 25:.0f}%
```

#### پورتفولیو پیشنهادی نهایی:

| دسته | تخصیص | دارایی‌ها |
|------|-------|----------|
| **نقد و معادل** | 25% | USD (60%), EUR (25%), CHF (15%) |
| **طلا و نقره** | {15 + int(self.attack_probability * 20)}% | طلا (80%), نقره (20%) |
| **انرژی** | 12% | XLE, XOM, CVX, نفت |
| **دفاعی** | 10% | ITA, RTX, LMT |
| **سهام دفاعی آمریکا** | 20% | XLV, XLU, XLP |
| **بین‌المللی** | 8% | EWJ, EWL, EWA |
| **اوراق قرضه** | 10% | SHY, TIPS |

#### Expected Return محاسبه:

```
سناریوی جنگ (P = {self.attack_probability:.0%}):
  - طلا: +15%
  - انرژی: +25%
  - دفاعی: +20%
  - سهام عمومی آمریکا: -15%
  Return_war = 0.{15 + int(self.attack_probability * 20):02d}×15% + 0.12×25% + 0.10×20% + 0.20×(-15%) = {(15 + int(self.attack_probability * 20))*0.15 + 12*0.25 + 10*0.20 + 20*(-0.15):.1f}%

سناریوی صلح (P = {1-self.attack_probability:.0%}):
  - طلا: 0%
  - انرژی: +5%
  - دفاعی: +5%
  - سهام عمومی آمریکا: +12%
  Return_peace = {(15 + int(self.attack_probability * 20))*0 + 12*0.05 + 10*0.05 + 20*0.12:.1f}%

Expected Return:
ER = P_war × R_war + P_peace × R_peace
ER = {self.attack_probability:.2f} × {(15 + int(self.attack_probability * 20))*0.15 + 12*0.25 + 10*0.20 + 20*(-0.15):.1f}% + {1-self.attack_probability:.2f} × {(15 + int(self.attack_probability * 20))*0 + 12*0.05 + 10*0.05 + 20*0.12:.1f}%
ER ≈ {self.attack_probability * ((15 + int(self.attack_probability * 20))*0.15 + 12*0.25 + 10*0.20 + 20*(-0.15)) + (1-self.attack_probability) * ((15 + int(self.attack_probability * 20))*0 + 12*0.05 + 10*0.05 + 20*0.12):.1f}%
```

#### نتیجه: این پورتفولیو در هر دو سناریو بازده مثبت دارد (All-Weather)
"""

    def format_investment_report(self) -> str:
        """Generate formatted investment report."""
        lines = [
            "# 💰 Investment & Portfolio Recommendations",
            f"\n**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}",
            f"**Conflict Probability:** {self.attack_probability*100:.0f}% within {self.timeline_months} months",
            "",
            "---",
            "",
            "## 📊 Current Market Prices",
            "",
            "| Asset | Price | 24h Change | YoY Change |",
            "|-------|-------|------------|------------|",
        ]
        
        for asset, data in self.CURRENT_PRICES.items():
            lines.append(f"| {asset.replace('_', ' ').title()} | {data['price']} {data['unit']} | {data['change_24h']:+.1f}% | {data['change_yoy']:+.0f}% |")
        
        lines.extend([
            "",
            "---",
            "",
            "## Gold and Bitcoin Levels (Timing Guide)",
            "",
            "| Asset | Buy Zone | Sell/Trim Zone | Notes |",
            "|-------|----------|----------------|-------|",
        ])
        gold_price = float(self.CURRENT_PRICES.get("gold", {}).get("price", 0) or 0)
        btc_price = float(self.CURRENT_PRICES.get("bitcoin", {}).get("price", 0) or 0)
        lines.append(f"| Gold (XAU) | $4,600-4,900 | $5,400-5,800 | Current: ${gold_price:,.0f}/oz |")
        lines.append(f"| Bitcoin | $55,000-62,000 | $85,000-95,000 | Current: ${btc_price:,.0f}; **Estimated cycle bottom:** $58,000+/-4,000 |")

        lines.extend([
            "",
            "*Interpretation:* Buy zones are for scaling in during risk-off dips; sell/trim zones are for risk reduction during spikes.",
            "",
            "---",
            "",
            "## ✅ Recommended: Safe Haven Assets",
            "",
        ])
        
        for rec in self.get_safe_haven_recommendations():
            lines.extend([
                f"### {rec.asset_name} ({rec.ticker})",
                f"**Action:** {rec.action} | **Confidence:** {rec.confidence} | **Risk:** {rec.risk_level}",
                f"**Entry:** {rec.entry_price}",
                f"**Target:** {rec.target_price}",
                f"**Reasoning:**",
                rec.reasoning,
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "## ⚡ Recommended: Energy Sector",
            "",
            "_Note: The following US stock market / oil-linked instruments require access to US markets. "
            "If you do not have access, skip these sections and use the alternative portfolio below._",
            "",
        ])
        
        for rec in self.get_energy_recommendations():
            lines.extend([
                f"### {rec.asset_name} ({rec.ticker})",
                f"**Action:** {rec.action} | **Confidence:** {rec.confidence} | **Risk:** {rec.risk_level}",
                f"**Entry:** {rec.entry_price}",
                f"**Target:** {rec.target_price}",
                f"**Reasoning:**",
                rec.reasoning,
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "## 🛡️ Recommended: Defense Sector",
            "",
        ])
        
        for rec in self.get_defense_recommendations():
            lines.extend([
                f"### {rec.asset_name} ({rec.ticker})",
                f"**Action:** {rec.action} | **Confidence:** {rec.confidence} | **Risk:** {rec.risk_level}",
                f"**Entry:** {rec.entry_price}" if rec.entry_price else "",
                f"**Target:** {rec.target_price}" if rec.target_price else "",
                f"**Reasoning:**",
                rec.reasoning,
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "## 📈 US Stock Market Recommendations",
            "",
        ])
        
        for rec in self.get_us_stock_recommendations():
            lines.extend([
                f"### {rec.asset_name} ({rec.ticker})",
                f"**Action:** {rec.action} | **Confidence:** {rec.confidence} | **Risk:** {rec.risk_level}",
            ])
            if rec.entry_price:
                lines.append(f"**Entry:** {rec.entry_price}")
            if rec.target_price:
                lines.append(f"**Target:** {rec.target_price}")
            lines.extend([
                f"**Reasoning:**",
                rec.reasoning,
                "",
            ])
        
        # Add sector allocation table
        lines.extend([
            "### 📊 Sector Allocation Strategy",
            "",
            "| Sector | Target Weight | Normal Weight | Strategy |",
            "|--------|--------------|---------------|----------|",
        ])
        
        sector_alloc = self.get_stock_sector_allocation()
        for sector, data in sector_alloc.get("overweight", {}).items():
            lines.append(f"| {sector} | {data['target']}% | {data['current_typical']}% | OVERWEIGHT |")
        for sector, data in sector_alloc.get("neutral", {}).items():
            lines.append(f"| {sector} | {data['target']}% | {data['current_typical']}% | NEUTRAL |")
        for sector, data in sector_alloc.get("underweight", {}).items():
            lines.append(f"| {sector} | {data['target']}% | {data['current_typical']}% | UNDERWEIGHT |")
        
        lines.extend([
            "",
            f"**Total Equity Allocation:** {sector_alloc.get('total_equity_allocation', '60-70%')}",
            f"**Cash Buffer:** {sector_alloc.get('cash_buffer', '20-30%')}",
            "",
            "**Rebalance Triggers:**",
        ])
        for trigger in sector_alloc.get("rebalance_triggers", []):
            lines.append(f"- {trigger}")
        
        lines.extend([
            "",
            "---",
            "",
            "## ⚠️ Avoid or Short",
            "",
        ])
        
        for rec in self.get_avoid_recommendations():
            lines.extend([
                f"### {rec.asset_name} ({rec.ticker})",
                f"**Action:** {rec.action} | **Risk:** {rec.risk_level}",
                f"**Reasoning:**",
                rec.reasoning,
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "## 📉 Scenario-Based Shorts (No Leverage)",
            "",
            "| Position | Horizon | Conditions | Risk | Confidence |",
            "|----------|---------|------------|------|------------|",
        ])
        
        for short in self.get_short_positions_no_leverage():
            lines.append(
                f"| {short['position']} | {short['horizon']} | {short['conditions']} | {short['risk']} | {short['confidence']} |"
            )
        
        lines.extend([
            "",
            "**Implementation (no leverage):**",
            "- Prefer 1x inverse ETFs if available; otherwise reduce exposure instead of shorting",
            "- Use strict position sizing and stop-loss rules",
            "",
        ])
        
        lines.extend([
            "---",
            "",
            "## 📈 Suggested Portfolio Allocation",
            "",
            "| Category | Allocation | Assets |",
            "|----------|------------|--------|",
        ])
        
        for alloc in self.get_suggested_portfolio():
            assets_str = ", ".join(alloc.assets[:3])
            lines.append(f"| {alloc.category} | {alloc.percentage:.0f}% | {assets_str} |")

        lines.extend([
            "",
            "_This allocation assumes access to US stock market and oil-linked instruments._",
            "",
            "### Alternative Portfolio (No US Stock Market Access)",
            "",
            "| Category | Allocation | Assets |",
            "|----------|------------|--------|",
        ])
        for alloc in self.get_suggested_portfolio_no_us_stocks():
            assets_str = ", ".join(alloc.assets[:3])
            lines.append(f"| {alloc.category} | {alloc.percentage:.0f}% | {assets_str} |")
        
        # Add detailed mathematical analysis sections
        lines.extend([
            "",
            "---",
            "",
            "## 📐 Detailed Mathematical Analysis",
            "",
        ])
        
        # Gold analysis
        lines.append(self.get_detailed_gold_analysis())
        lines.append("\n---\n")
        
        # Bitcoin analysis
        lines.append(self.get_detailed_btc_analysis())
        lines.append("\n---\n")
        
        # Currency analysis
        lines.append(self.get_detailed_currency_analysis())
        lines.append("\n---\n")
        
        # Short recommendations
        lines.append(self.get_short_recommendations())
        lines.append("\n---\n")
        
        # Portfolio optimization
        lines.append(self.get_mathematical_portfolio_optimization())
        
        lines.extend([
            "",
            "---",
            "",
            "## 🇮🇷 Advice for People in Iran",
            "",
        ])
        
        advice = self.get_advice_for_iranians()
        for section, content in advice.items():
            lines.append(f"### {section.replace('_', ' ').title()}")
            lines.append(content)
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## ⚠️ Disclaimer",
            "",
            "This is not financial advice. Consult a licensed financial advisor before making investment decisions.",
            "Past performance does not guarantee future results. Geopolitical events are inherently unpredictable.",
            "",
        ])
        
        return "\n".join(lines)


def main():
    """Test investment advisor."""
    advisor = InvestmentAdvisor(attack_probability=0.35, timeline_months=6)
    print(advisor.format_investment_report())


if __name__ == "__main__":
    main()
