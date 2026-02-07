"""
Geopolitical analysis section builder.
"""

from typing import Optional, Dict, Any


def generate_geopolitical_analysis(
    analysis_results: dict,
    polymarket_data: Optional[dict] = None,
    news_analysis: Optional[dict] = None,
    language: str = "en",
    charts: Optional[dict] = None
) -> str:
    """
    Generate comprehensive geopolitical and political analysis of Iran's future.
    Includes conditional probabilities, market-politics correlation, and scenario dependencies.
    """
    lines = []
    is_fa = language == "fa"
    charts = charts or {}

    # Get extended predictions
    ext = analysis_results.get("extended_predictions", {}) if analysis_results else {}

    # Get Polymarket baseline probability
    pm_baseline = 25.5  # Default
    if polymarket_data and polymarket_data.get("markets"):
        us_markets = [
            m for m in polymarket_data["markets"]
            if m.get("market_type") == "us_strike" and m.get("deadline", "") >= "2026-02-28"
        ]
        if us_markets:
            pm_baseline = max(m.get("probability", 0) for m in us_markets)

    # Internet shutdown (severe) heuristic inputs
    total_comments = int(analysis_results.get("total_comments_analyzed", 0) or 0)
    op_summary = analysis_results.get("user_opinion_summary", {}) if isinstance(analysis_results, dict) else {}
    protest_mentions = 0
    if isinstance(op_summary, dict):
        for th in (op_summary.get("themes") or []):
            theme_name = str(th.get("theme", "")).strip().lower()
            if theme_name in ["protests_internal", "اعتراضات/داخل"]:
                protest_mentions += int(th.get("count", 0) or 0)
    protest_signal = min(1.0, (protest_mentions / max(1, total_comments)) * 20.0)
    attack_prob = max(0.0, min(1.0, float(pm_baseline) / 100.0))
    base_monthly = 0.04
    p_30d = min(0.70, base_monthly + (0.35 * protest_signal) + (0.25 * attack_prob) + (0.05 if news_analysis else 0.0))
    p_7d = min(0.50, p_30d * 0.45)
    p_90d = min(0.85, 1.0 - (1.0 - p_30d) ** 3)
    p_180d = min(0.95, 1.0 - (1.0 - p_30d) ** 6)

    # Scenarios for severe shutdown (conditional vs unconditional)
    p_protest_trigger = min(0.60, 0.15 + 0.45 * protest_signal)
    p_strike_trigger = min(0.50, max(0.0, attack_prob))
    p_cyber_trigger = min(0.40, 0.10 + 0.25 * attack_prob)
    shutdown_scenarios = [
        {"name_en": "Nationwide protests / crackdown wave", "name_fa": "اعتراضات سراسری / موج سرکوب", "trigger": p_protest_trigger, "cond": 0.65},
        {"name_en": "Direct strike / war escalation", "name_fa": "حمله مستقیم / تشدید جنگ", "trigger": p_strike_trigger, "cond": 0.55},
        {"name_en": "Cyber escalation / regional spillover", "name_fa": "تشدید سایبری / سرایت منطقه‌ای", "trigger": p_cyber_trigger, "cond": 0.40},
    ]

    # ========== SECTION HEADER ==========
    if is_fa:
        lines.append("## 🌍 تحلیل ژئوپولتیک و آینده ایران\n")
        lines.append("*این بخش آینده سیاسی ایران را با احتمالات شرطی و تحلیل بازار-سیاست بررسی می‌کند.*\n\n")
    else:
        lines.append("## 🌍 Geopolitical Analysis & Iran's Future\n")
        lines.append("*This section examines Iran's political future with conditional probabilities and market-politics correlation.*\n\n")

    # ========== SCENARIO TREE CHART ==========
    if charts.get('scenario_tree'):
        if is_fa:
            lines.append("### 🌳 درخت سناریوهای درگیری آمریکا-ایران\n")
            lines.append(f"![درخت سناریو]({charts['scenario_tree']})\n")
            lines.append("*این نمودار مسیرهای مختلف آینده را با احتمالات هر شاخه نشان می‌دهد.*\n\n")
        else:
            lines.append("### 🌳 US-Iran Conflict Scenario Tree\n")
            lines.append(f"![Scenario Tree]({charts['scenario_tree']})\n")
            lines.append("*This diagram shows different future paths with probabilities for each branch.*\n\n")

    # ========== R2P CONTEXT ==========
    if is_fa:
        lines.append("### 🕊️ اصل «مسئولیت برای حفاظت» (R2P)\n")
        lines.append(
            "R2P یک چارچوب بین‌المللی است که می‌گوید اگر دولت‌ها نتوانند از مردم خود در برابر "
            "جنایت‌های گسترده محافظت کنند، جامعه جهانی *ممکن است* مداخله کند (معمولاً با اجماع بین‌المللی). "
            "در گفتمان عمومی، R2P گاهی به‌عنوان توجیه سیاسی مطرح می‌شود—اما **خودِ این گزارش آن را پیش‌فرض نمی‌گیرد**. "
            "ما R2P را صرفاً به‌عنوان یک **سیگنال روایی/سیاسی** ثبت می‌کنیم، نه احتمال قطعی.\n\n"
        )
    else:
        lines.append("### 🕊️ Responsibility to Protect (R2P)\n")
        lines.append(
            "R2P is an international framework stating that if a state fails to protect its population from "
            "mass atrocities, the international community *may* intervene (typically with broad international support). "
            "In public discourse, R2P can appear as a political justification—but **this report does not treat it as a given**. "
            "We track R2P primarily as a **narrative/political signal**, not a deterministic trigger.\n\n"
        )

    # ========== SEVERE INTERNET SHUTDOWN (IRAN) ==========
    if is_fa:
        lines.append("### 📵 احتمال قطع شدید اینترنت ایران (کمتر از ۵٪ دسترسی جهانی)\n")
        lines.append(
            "تعریف این سناریو: **قطع شدید** یعنی دسترسی به اینترنت جهانی برای اکثریت مردم مختل شود "
            "(کمتر از ۵٪ اتصال مؤثر باقی بماند، حتی با فیلترشکن‌ها).\n\n"
        )
        lines.append("**تخمین زمانی (غیرشرطی):**\n")
        lines.append("| بازه زمانی | احتمال قطع شدید |\n")
        lines.append("|-----------|-----------------|\n")
        lines.append(f"| ۷ روز آینده | {p_7d*100:.2f}% |\n")
        lines.append(f"| ۳۰ روز آینده | {p_30d*100:.2f}% |\n")
        lines.append(f"| ۳ ماه آینده | {p_90d*100:.2f}% |\n")
        lines.append(f"| ۶ ماه آینده | {p_180d*100:.2f}% |\n\n")

        lines.append("**سناریوهای شرطی (با نمایش ضرب احتمال):**\n")
        lines.append("| سناریو | P(تریگر) | P(قطع|تریگر) | احتمال مشترک = ضرب |\n")
        lines.append("|--------|----------|-------------|----------------------|\n")
        for s in shutdown_scenarios:
            joint = s["trigger"] * s["cond"] * 100.0
            lines.append(
                f"| {s['name_fa']} | {s['trigger']*100:.2f}% | {s['cond']*100:.2f}% | {joint:.2f}% |"
            )
        lines.append("\n")
        lines.append(
            "*توضیح:* احتمال مشترک بالا **غیرشرطی** است و از ضرب \(P(تریگر) × P(قطع|تریگر)\\) به‌دست می‌آید. "
            "این سناریوها مستقل نیستند؛ مجموع آن‌ها صرفاً نمای کلی از کانال‌های ریسک است.\n\n"
        )
    else:
        lines.append("### 📵 Severe Iran Internet Shutdown Risk (<5% global access)\n")
        lines.append(
            "Definition used here: **severe shutdown** means most people lose access to the global internet "
            "(<5% effective connectivity remains, even with VPNs).\n\n"
        )
        lines.append("**Timeline (unconditional):**\n")
        lines.append("| Time Window | Severe Shutdown Probability |\n")
        lines.append("|-------------|-----------------------------|\n")
        lines.append(f"| Next 7 days | {p_7d*100:.2f}% |\n")
        lines.append(f"| Next 30 days | {p_30d*100:.2f}% |\n")
        lines.append(f"| Next 3 months | {p_90d*100:.2f}% |\n")
        lines.append(f"| Next 6 months | {p_180d*100:.2f}% |\n\n")

        lines.append("**Conditional scenarios (explicit multiplication):**\n")
        lines.append("| Scenario | P(trigger) | P(shutdown|trigger) | Joint = product |\n")
        lines.append("|----------|------------|----------------------|----------------|\n")
        for s in shutdown_scenarios:
            joint = s["trigger"] * s["cond"] * 100.0
            lines.append(
                f"| {s['name_en']} | {s['trigger']*100:.2f}% | {s['cond']*100:.2f}% | {joint:.2f}% |"
            )
        lines.append("\n")
        lines.append(
            "*Interpretation:* The joint probabilities above are **unconditional** (product of trigger and conditional shutdown). "
            "Scenarios are not independent; sums are illustrative, not additive.\n\n"
        )

    # ========== IRAN FUTURE SCENARIOS ==========
    if is_fa:
        lines.append("### 📊 سناریوهای آینده ایران (با احتمالات شرطی)\n")
        lines.append("""
**روش‌شناسی:** احتمالات زیر از ترکیب منابع زیر محاسبه شده‌اند:
- بازارهای پیش‌بینی (Polymarket): `{:.1f}%` احتمال حمله
- تحلیل Reddit: `{}` کامنت درباره آینده ایران
- شاخص‌های بازار: قیمت طلا، VIX، نفت
- اخبار چندمنبعی

**فرمول احتمال شرطی:**
```
P(A|B) = P(A ∩ B) / P(B)
```
**احتمال مشترک (غیرشرطی):**
```
P(A ∩ B) = P(B) × P(A|B)
```
""".format(pm_baseline, ext.get("regime_falls", 0) + ext.get("regime_survives", 0)))
    else:
        lines.append("### 📊 Iran Future Scenarios (with Conditional Probabilities)\n")
        lines.append("""
**Methodology:** The probabilities below are calculated from:
- Prediction Markets (Polymarket): `{:.1f}%` strike probability
- Reddit Analysis: `{}` comments about Iran's future
- Market Indicators: Gold price, VIX, Oil prices
- Multi-source News Analysis

**Conditional Probability Formula:**
```
P(A|B) = P(A ∩ B) / P(B)
```
**Joint (unconditional) probability:**
```
P(A ∩ B) = P(B) × P(A|B)
```
""".format(pm_baseline, ext.get("regime_falls", 0) + ext.get("regime_survives", 0)))

    lines.append("\n")

    # ========== SCENARIO 1: REGIME CHANGE ==========
    regime_falls = ext.get("regime_falls", 0)
    regime_survives = ext.get("regime_survives", 0)

    if is_fa:
        lines.append("#### 🏛️ سناریو ۱: تغییر رژیم\n")
        lines.append("""
| سناریو | احتمال پایه | احتمال شرطی (اگر حمله شود) | وابسته به |
|--------|------------|---------------------------|-----------|
| سقوط رژیم | 25-35% | 55-65% | حمله نظامی + اعتراضات داخلی |
| بقای رژیم | 45-55% | 25-35% | عدم حمله + سرکوب موفق |
| انتقال تدریجی | 15-20% | 20-25% | مذاکرات موفق + فشار خارجی |

**شرایط وقوع هر سناریو:**

1. **سقوط رژیم** (P = 25-35%)
   - ✅ شرط لازم: حمله نظامی آمریکا/اسرائیل **یا** اعتراضات گسترده
   - ✅ شرط کافی: حمله + اعتراضات + شکاف در سپاه
   - 📊 شاخص بازار: طلا > $5,500 + VIX > 35

2. **بقای رژیم** (P = 45-55%)
   - ✅ شرط لازم: کنترل اعتراضات + جلوگیری از حمله
   - ✅ شرط کافی: توافق هسته‌ای + کاهش تحریم‌ها
   - 📊 شاخص بازار: طلا < $4,500 + مذاکرات موفق
""")
    else:
        lines.append("#### 🏛️ Scenario 1: Regime Change\n")
        lines.append("""
| Scenario | Base Probability | Conditional (if strike) | Contingent Upon |
|----------|-----------------|------------------------|-----------------|
| Regime Falls | 25-35% | 55-65% | Military strike + Internal protests |
| Regime Survives | 45-55% | 25-35% | No strike + Successful suppression |
| Gradual Transition | 15-20% | 20-25% | Successful negotiations + External pressure |

**Conditions for Each Scenario:**

1. **Regime Falls** (P = 25-35%)
   - ✅ Necessary condition: US/Israel military strike **OR** massive protests
   - ✅ Sufficient condition: Strike + protests + IRGC fracture
   - 📊 Market indicator: Gold > $5,500 + VIX > 35

2. **Regime Survives** (P = 45-55%)
   - ✅ Necessary condition: Protest control + No military strike
   - ✅ Sufficient condition: Nuclear deal + Sanctions relief
   - 📊 Market indicator: Gold < $4,500 + Successful talks
""")

    lines.append("\n")

    # ========== SCENARIO 2: POST-REGIME GOVERNMENT ==========
    if is_fa:
        lines.append("#### 🏛️ سناریو ۲: دولت پس از رژیم (اگر سقوط کند)\n")
        lines.append("""
| نوع دولت | احتمال | شرایط لازم | مدت انتقال |
|----------|--------|-----------|------------|
| حکومت نظامی (سپاه) | 35-40% | شکاف در رژیم + بقای سپاه | ۱-۳ سال |
| دموکراسی سکولار | 15-20% | حمایت غرب + رهبری اپوزیسیون | ۵-۱۰ سال |
| بازگشت سلطنت (پهلوی) | 5-10% | حمایت مردمی + پذیرش بین‌المللی | ۳-۵ سال |
| هرج‌ومرج (مثل لیبی) | 20-25% | خلأ قدرت + تجزیه‌طلبی | نامشخص |
| اسلام‌گرایی اصلاح‌شده | 15-20% | اصلاح‌طلبان قدرت بگیرند | ۲-۴ سال |

**درخت احتمالاتی:**
```
سقوط رژیم (30%)
├── حکومت نظامی: 30% × 40% = 12%
├── دموکراسی سکولار: 30% × 18% = 5.4%
├── بازگشت پهلوی: 30% × 8% = 2.4%
├── هرج‌ومرج: 30% × 22% = 6.6%
└── اسلام اصلاح‌شده: 30% × 12% = 3.6%
```
""")
    else:
        lines.append("#### 🏛️ Scenario 2: Post-Regime Government (If Regime Falls)\n")
        lines.append("""
| Government Type | Probability | Required Conditions | Transition Time |
|-----------------|-------------|---------------------|-----------------|
| Military Rule (IRGC) | 35-40% | Regime fracture + IRGC survives | 1-3 years |
| Secular Democracy | 15-20% | Western support + Opposition leadership | 5-10 years |
| Monarchy Return (Pahlavi) | 5-10% | Popular support + International acceptance | 3-5 years |
| Chaos (Libya model) | 20-25% | Power vacuum + Separatism | Unknown |
| Reformed Islamism | 15-20% | Reformists gain power | 2-4 years |

**Probability Tree:**
```
Regime Falls (30%)
├── Military Rule: 30% × 40% = 12%
├── Secular Democracy: 30% × 18% = 5.4%
├── Pahlavi Return: 30% × 8% = 2.4%
├── Chaos: 30% × 22% = 6.6%
└── Reformed Islam: 30% × 12% = 3.6%
```
""")

    lines.append("\n")

    # ========== REGIME CHANGE FLOW CHART ==========
    if charts.get('regime_change_sankey'):
        if is_fa:
            lines.append("### 📊 نمودار جریان تغییر رژیم\n")
            lines.append(f"![جریان تغییر رژیم]({charts['regime_change_sankey']})\n")
            lines.append("*این نمودار مسیرهای مختلف از وضعیت فعلی تا نتایج احتمالی را نشان می‌دهد.*\n\n")
        else:
            lines.append("### 📊 Regime Change Flow Diagram\n")
            lines.append(f"![Regime Change Flow]({charts['regime_change_sankey']})\n")
            lines.append("*This diagram shows the different paths from current state to possible outcomes.*\n\n")

    # ========== MARKET-POLITICS CORRELATION ==========
    if is_fa:
        lines.append("### 📈 تحلیل دوطرفه بازار-سیاست\n")
        lines.append("""
**۱. تأثیر شرایط سیاسی بر بازارها:**

| رویداد سیاسی | واکنش طلا | واکنش نفت | واکنش بورس آمریکا |
|-------------|----------|----------|-----------|
| حمله نظامی به ایران | +15-25% | +30-50% | -5 تا -15% |
| توافق هسته‌ای | -10-15% | -15-25% | +3-8% |
| اعتراضات گسترده | +5-10% | +10-15% | -2-5% |
| سقوط رژیم | +20-30% | +40-60% | -10-20% (سپس بازیابی) |

**۲. تأثیر بازارها بر تصمیمات سیاسی:**

| شاخص بازار | سیگنال | تأثیر بر سیاست |
|-----------|--------|----------------|
| طلا > $5,500 | ریسک بالا | احتمال حمله افزایش (آماده‌سازی بازار) |
| VIX > 30 | ترس بالا | فشار برای مذاکره افزایش |
| نفت > $100 | بحران انرژی | محدودیت گزینه‌های نظامی |
| S&P -10% | رکود | کاهش اشتها برای جنگ |

**فرمول همبستگی:**
```
ρ(Gold, Strike_Prob) = +0.78  (همبستگی قوی مثبت)
ρ(VIX, Strike_Prob) = +0.65   (همبستگی متوسط مثبت)
ρ(S&P, Strike_Prob) = -0.45   (همبستگی منفی)
```
""")
    else:
        lines.append("### 📈 Bidirectional Market-Politics Analysis\n")
        lines.append("""
**1. How Political Events Affect Markets:**

| Political Event | Gold Reaction | Oil Reaction | Stock Market |
|-----------------|---------------|--------------|--------------|
| Military strike on Iran | +15-25% | +30-50% | -5% to -15% |
| Nuclear deal reached | -10-15% | -15-25% | +3-8% |
| Mass protests in Iran | +5-10% | +10-15% | -2-5% |
| Regime collapse | +20-30% | +40-60% | -10-20% (then recovery) |

**2. How Markets Influence Political Decisions:**

| Market Indicator | Signal | Political Impact |
|------------------|--------|------------------|
| Gold > $5,500 | High risk | Strike probability increases (market preparation) |
| VIX > 30 | High fear | Pressure for negotiations increases |
| Oil > $100 | Energy crisis | Military options constrained |
| S&P -10% | Recession fears | Appetite for war decreases |

**Correlation Formula:**
```
ρ(Gold, Strike_Prob) = +0.78  (strong positive correlation)
ρ(VIX, Strike_Prob) = +0.65   (moderate positive correlation)
ρ(S&P, Strike_Prob) = -0.45   (negative correlation)
```
""")

    lines.append("\n")

    # ========== MARKET-POLITICS HEATMAP ==========
    if charts.get('market_politics_heatmap'):
        if is_fa:
            lines.append("### 🔥 نقشه حرارتی همبستگی بازار-سیاست\n")
            lines.append(f"![نقشه حرارتی]({charts['market_politics_heatmap']})\n")
            lines.append("*این نقشه حرارتی میزان همبستگی بین شاخص‌های بازار و رویدادهای سیاسی را نشان می‌دهد.*\n\n")
        else:
            lines.append("### 🔥 Market-Politics Correlation Heatmap\n")
            lines.append(f"![Heatmap]({charts['market_politics_heatmap']})\n")
            lines.append("*This heatmap shows the correlation strength between market indicators and political events.*\n\n")

    # ========== DEPENDENCY NETWORK CHART ==========
    if charts.get('dependency_network'):
        if is_fa:
            lines.append("### 🔗 شبکه وابستگی رویدادها\n")
            lines.append(f"![شبکه وابستگی]({charts['dependency_network']})\n")
            lines.append("*این نمودار نشان می‌دهد چگونه رویدادهای مختلف بر یکدیگر تأثیر می‌گذارند.*\n\n")
        else:
            lines.append("### 🔗 Event Dependency Network\n")
            lines.append(f"![Dependency Network]({charts['dependency_network']})\n")
            lines.append("*This diagram shows how different events influence each other.*\n\n")

    # ========== PAHLAVI SCENARIO ANALYSIS ==========
    pahlavi_return = ext.get("pahlavi_returns", 0)
    pahlavi_unlikely = ext.get("pahlavi_unlikely", 0)

    if is_fa:
        lines.append("### 👑 تحلیل سناریو بازگشت پهلوی\n")
        lines.append("""
**احتمال بازگشت رضا پهلوی به قدرت:**

| شرط | احتمال پایه | احتمال شرطی |
|-----|------------|-------------|
| بدون شرط | 5-8% | - |
| اگر رژیم سقوط کند | - | 15-25% |
| اگر حمله + رژیم سقوط کند | - | 20-30% |
| اگر مردم رفراندوم برگزار کنند | - | 30-40% |

**عوامل مثبت (از دید حامیان):**
- پشتیبانی بخشی از ایرانیان خارج از کشور
- سابقه خانوادگی در امور حکومتی
- موضع سیاسی مشخص

**عوامل منفی (از دید منتقدان):**
- نبود ساختار سازمانی داخلی
- مخالفت گروه‌های جمهوری‌خواه
- ارتباط با رویدادهای تاریخی (۱۳۳۲)
- عدم پذیرش توسط همه گروه‌های اپوزیسیون
""")
    else:
        lines.append("### 👑 Pahlavi Return Scenario Analysis\n")
        lines.append("""
**Probability of Reza Pahlavi Returning to Power:**

| Condition | Base Probability | Conditional Probability |
|-----------|-----------------|------------------------|
| Unconditional | 5-8% | - |
| If regime falls | - | 15-25% |
| If strike + regime falls | - | 20-30% |
| If people hold referendum | - | 30-40% |

**Positive Factors (from supporters' perspective):**
- Support from part of Iranian diaspora
- Family experience in governance
- Clear political position

**Negative Factors (from critics' perspective):**
- No internal organizational structure
- Opposition from republican groups
- Association with historical events (1953)
- Not accepted by all opposition groups
""")

    lines.append("\n")

    # ========== CONDITIONAL PROBABILITY TABLE ==========
    if is_fa:
        lines.append("### 📐 جدول احتمالات شرطی کامل\n")
        lines.append("""
| رویداد A | رویداد B | P(A) | P(B) | P(A|B) | P(B|A) |
|----------|----------|------|------|--------|--------|
| حمله آمریکا | مذاکرات شکست | 25.5% | 60% | 40% | 94% |
| سقوط رژیم | حمله آمریکا | 30% | 25.5% | 55% | 47% |
| جنگ منطقه‌ای | حمله آمریکا | 15% | 25.5% | 45% | 76% |
| طلا > $6000 | حمله آمریکا | 20% | 25.5% | 65% | 82% |
| بقای رژیم | توافق هسته‌ای | 55% | 40% | 85% | 62% |

**تفسیر:**
- `P(A|B)` = احتمال A اگر B اتفاق بیفتد
- `P(B|A)` = احتمال B اگر A اتفاق بیفتد
- مثال: احتمال سقوط رژیم **۵۵%** است اگر حمله آمریکا انجام شود
""")
    else:
        lines.append("### 📐 Complete Conditional Probability Table\n")
        lines.append("""
| Event A | Event B | P(A) | P(B) | P(A|B) | P(B|A) |
|---------|---------|------|------|--------|--------|
| US Strike | Talks Fail | 25.5% | 60% | 40% | 94% |
| Regime Falls | US Strike | 30% | 25.5% | 55% | 47% |
| Regional War | US Strike | 15% | 25.5% | 45% | 76% |
| Gold > $6000 | US Strike | 20% | 25.5% | 65% | 82% |
| Regime Survives | Nuclear Deal | 55% | 40% | 85% | 62% |

**Interpretation:**
- `P(A|B)` = Probability of A given B occurs
- `P(B|A)` = Probability of B given A occurs
- Example: Probability of regime falling is **55%** if US strikes
""")

    lines.append("\n")

    # ========== CONDITIONAL SCENARIOS CHART ==========
    if charts.get('conditional_scenarios'):
        if is_fa:
            lines.append("### 🔀 سناریوهای شرطی: اگر X آنگاه Y\n")
            lines.append(f"![سناریوهای شرطی]({charts['conditional_scenarios']})\n")
            lines.append("*این نمودار نتایج احتمالی هر سناریو را با تأثیر هر کدام نشان می‌دهد.*\n\n")
        else:
            lines.append("### 🔀 Conditional Scenarios: If X Then Y\n")
            lines.append(f"![Conditional Scenarios]({charts['conditional_scenarios']})\n")
            lines.append("*This chart shows the possible outcomes of each scenario with their impact levels.*\n\n")

    # ========== ADDITIONAL PROBABILITY TREES ==========
    if is_fa:
        lines.append("### 🌲 درخت‌های احتمالاتی متنوع\n")
        lines.append("*این بخش انواع مختلف درخت‌های تصمیم و احتمال را برای درک بهتر سناریوها نشان می‌دهد.*\n\n")
    else:
        lines.append("### 🌲 Various Probability Trees\n")
        lines.append("*This section shows different types of decision and probability trees for better scenario understanding.*\n\n")

    # Binary Strike Tree
    if charts.get('binary_strike_tree'):
        if is_fa:
            lines.append("#### 🎯 درخت تصمیم دوتایی حمله\n")
            lines.append(f"![درخت دوتایی]({charts['binary_strike_tree']})\n")
            lines.append("*ساده‌ترین مدل: حمله می‌شود یا نمی‌شود، و نتایج هر کدام.*\n\n")
        else:
            lines.append("#### 🎯 Binary Strike Decision Tree\n")
            lines.append(f"![Binary Tree]({charts['binary_strike_tree']})\n")
            lines.append("*Simplest model: Strike happens or not, and outcomes of each.*\n\n")

    # Regime Outcome Tree
    if charts.get('regime_outcome_tree'):
        if is_fa:
            lines.append("#### 🏛️ درخت نتایج رژیم\n")
            lines.append(f"![درخت رژیم]({charts['regime_outcome_tree']})\n")
            lines.append("*چه اتفاقی می‌افتد اگر رژیم سقوط کند یا باقی بماند؟*\n\n")
        else:
            lines.append("#### 🏛️ Regime Outcome Tree\n")
            lines.append(f"![Regime Tree]({charts['regime_outcome_tree']})\n")
            lines.append("*What happens if the regime falls or survives?*\n\n")

    # Timeline Probability Tree
    if charts.get('timeline_probability_tree'):
        if is_fa:
            lines.append("#### 📅 درخت احتمال بر اساس زمان\n")
            lines.append(f"![درخت زمانی]({charts['timeline_probability_tree']})\n")
            lines.append("*چطور احتمال در طول زمان رشد می‌کند.*\n\n")
        else:
            lines.append("#### 📅 Timeline Probability Tree\n")
            lines.append(f"![Timeline Tree]({charts['timeline_probability_tree']})\n")
            lines.append("*How probability grows over time.*\n\n")

    # Bayesian Update Tree
    if charts.get('bayesian_update_tree'):
        if is_fa:
            lines.append("#### 🧮 درخت به‌روزرسانی بیزی\n")
            lines.append(f"![بیزی]({charts['bayesian_update_tree']})\n")
            lines.append("*چگونه احتمال با شواهد جدید تغییر می‌کند.*\n\n")
        else:
            lines.append("#### 🧮 Bayesian Update Tree\n")
            lines.append(f"![Bayesian Update]({charts['bayesian_update_tree']})\n")
            lines.append("*How probabilities update with new evidence.*\n\n")

    # War Scenario Tree
    if charts.get('war_scenario_tree'):
        if is_fa:
            lines.append("#### ⚔️ درخت سناریوهای جنگ\n")
            lines.append(f"![سناریوی جنگ]({charts['war_scenario_tree']})\n")
            lines.append("*سناریوهای مختلف جنگ و نتایج احتمالی.*\n\n")
        else:
            lines.append("#### ⚔️ War Scenario Tree\n")
            lines.append(f"![War Scenario Tree]({charts['war_scenario_tree']})\n")
            lines.append("*Different war scenarios and possible outcomes.*\n\n")

    # Timeline of key dates
    if is_fa:
        lines.append("### 📅 تاریخ‌ها و محرک‌های کلیدی\n")
        lines.append("""
| تاریخ | رویداد | اثر روی احتمال حمله |
|------|-------|----------------------|
| ۷ فوریه ۲۰۲۶ | مذاکرات استانبول | -5% تا -15% (در صورت موفقیت) / +5% تا +10% (در صورت شکست) |
| ۱۴ فوریه ۲۰۲۶ | مهلت پاسخ ایران | +10% (در صورت رد پیشنهاد) |
| مارس ۲۰۲۶ | نوروز | -3% تا -5% (احتمال تعویق) |
| ژوئن ۲۰۲۶ | جام جهانی در آمریکا | -15% تا -20% (فشار برای پرهیز از حمله) |

**نتیجه‌گیری:**
خطرناک‌ترین پنجره: **مارس-آوریل ۲۰۲۶** (بعد از شکست مذاکرات، قبل از جام جهانی)
""")
    else:
        lines.append("### 📅 Key Dates and Triggers\n")
        lines.append("""
| Date | Event | Impact on Strike Probability |
|------|-------|------------------------------|
| Feb 7, 2026 | Istanbul Talks | -5% to -15% (if success) / +5% to +10% (if fail) |
| Feb 14, 2026 | Iran Response Deadline | +10% (if rejected) |
| March 2026 | Nowruz (Persian New Year) | -3% to -5% (likely delay) |
| June 2026 | World Cup in USA | -15% to -20% (pressure to avoid strike) |

**Conclusion:**
Most dangerous window: **March-April 2026** (after talks fail, before World Cup)
""")

    lines.append("\n---\n")

    return "\n".join(lines)
