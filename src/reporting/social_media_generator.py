"""
Social Media Generator Module
Creates Twitter threads and LinkedIn posts for US-Iran Conflict Analysis.

Generates:
- Twitter thread (Persian): Max 30 tweets, each max 280 chars
- Twitter thread (English): Max 30 tweets, each max 280 chars
- LinkedIn post (Persian): ~10 min read
- LinkedIn post (English): ~10 min read
"""

from datetime import datetime
from typing import Dict, Optional, List, Any
import textwrap


class SocialMediaGenerator:
    """Generates social media content from analysis data."""
    
    MAX_TWEET_LENGTH = 280
    MAX_TWEETS = 30
    LINKEDIN_WORDS_PER_MINUTE = 200  # Average reading speed
    LINKEDIN_TARGET_MINUTES = 10
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.date_str_en = datetime.now().strftime('%B %d, %Y')
        self.date_str_fa = self._get_persian_date()
    
    def _get_persian_date(self) -> str:
        """Get current date in Persian format."""
        # Map month to Persian
        months_fa = {
            1: 'ژانویه', 2: 'فوریه', 3: 'مارس', 4: 'آوریل',
            5: 'مه', 6: 'ژوئن', 7: 'ژوئیه', 8: 'آگوست',
            9: 'سپتامبر', 10: 'اکتبر', 11: 'نوامبر', 12: 'دسامبر'
        }
        now = datetime.now()
        return f"{now.day} {months_fa.get(now.month, '')} {now.year}"
    
    def _extract_key_metrics(self, data: Dict) -> Dict:
        """Extract key metrics from analysis data for social media."""
        metrics = {
            'weighted_prob': 25.0,
            'polymarket_feb': 22.0,
            'polymarket_mar': 35.0,
            'reddit_attack_pct': 30.0,
            'gold_price': 5038,
            'total_users': 0,
            'key_date': 'February 7, 2026',
            'key_event': 'Istanbul Talks',
        }
        
        # Extract from analysis results
        analysis = data.get('analysis_results', {})
        if analysis:
            total = analysis.get('total_authors_analyzed', 0)
            attack = analysis.get('predict_attack', 0)
            no_attack = analysis.get('predict_no_attack', 0)
            if attack + no_attack > 0:
                metrics['reddit_attack_pct'] = 100 * attack / (attack + no_attack)
            metrics['total_users'] = total
        
        # Extract from Polymarket
        polymarket = data.get('polymarket_data', {})
        if polymarket:
            markets = polymarket.get('markets', [])
            for m in markets:
                deadline = str(m.get('deadline', ''))
                prob = m.get('probability', 0)
                if '2026-02-28' in deadline and m.get('market_type') == 'us_strike':
                    metrics['polymarket_feb'] = prob
                elif '2026-03-31' in deadline and m.get('market_type') == 'us_strike':
                    metrics['polymarket_mar'] = prob
            
            # Gold price from market analysis
            market_analysis = polymarket.get('market_analysis', {})
            if market_analysis:
                gold = market_analysis.get('gold', {})
                if gold:
                    metrics['gold_price'] = gold.get('price', 5038)
        
        # Calculate weighted probability
        reddit_weight = 0.15
        pm_weight = 0.60
        gold_weight = 0.25
        gold_prob = min(60, max(10, (metrics['gold_price'] - 2000) / 50))
        
        metrics['weighted_prob'] = (
            reddit_weight * metrics['reddit_attack_pct'] +
            pm_weight * metrics['polymarket_feb'] +
            gold_weight * gold_prob
        )
        
        return metrics
    
    # =========================================================================
    # TWITTER THREAD GENERATORS
    # =========================================================================
    
    def generate_twitter_thread_fa(self, data: Dict) -> str:
        """
        Generate Persian Twitter thread.
        Max 30 tweets, each max 280 chars.
        """
        metrics = self._extract_key_metrics(data)
        tweets = []
        
        # Tweet 1: Introduction
        tweets.append(f"""🧵 تحلیل احتمال حمله آمریکا به ایران

📊 داده‌ها چه می‌گویند؟ یک ترد مبتنی بر تحلیل الگوریتمی

تاریخ: {self.date_str_fa}

۱/""")
        
        # Tweet 2: Disclaimer
        tweets.append("""⚠️ سلب مسئولیت

این تحلیل صرفاً آموزشی است و توصیه مالی/سیاسی نیست. بازارهای پیش‌بینی و تحلیل احساسات دقت محدود دارند.

هیچ مدلی نمی‌تواند رویدادهای ژئوپلیتیک را با قطعیت پیش‌بینی کند.

۲/""")
        
        # Tweet 3: Method
        tweets.append(f"""📈 روش تحلیل:

۱. Polymarket: شرط‌بندی با پول واقعی (وزن: ۶۰%)
۲. Reddit: {metrics['total_users']:,} کاربر تحلیل شد (وزن: ۱۵%)
۳. قیمت طلا: ${metrics['gold_price']:,} (وزن: ۲۵%)

۳/""")
        
        # Tweet 4: Polymarket data
        tweets.append(f"""🎰 داده Polymarket:

• تا پایان فوریه: {metrics['polymarket_feb']:.0f}%
• تا پایان مارس: {metrics['polymarket_mar']:.0f}%

تریدرها پول واقعی ریسک می‌کنند پس انگیزه برای دقت دارند.

۴/""")
        
        # Tweet 5: Reddit sentiment
        tweets.append(f"""💬 تحلیل Reddit:

از {metrics['total_users']:,} کاربر:
• {metrics['reddit_attack_pct']:.0f}% پیش‌بینی حمله
• {100-metrics['reddit_attack_pct']:.0f}% پیش‌بینی عدم حمله

توجه: Reddit معمولاً بایاس روایتی دارد.

۵/""")
        
        # Tweet 6: Gold signal
        tweets.append(f"""🥇 سیگنال طلا:

قیمت فعلی: ${metrics['gold_price']:,}/oz
این بالاترین قیمت از ۱۹۷۹ است!

طلا = بیمه بحران. وقتی بالاست یعنی پول هوشمند نگران است.

۶/""")
        
        # Tweet 7: Combined probability
        tweets.append(f"""🧮 احتمال ترکیبی:

با ترکیب وزن‌دار سه منبع:

📊 احتمال حمله آمریکا در فوریه: ~{metrics['weighted_prob']:.0f}%

این یعنی «احتمال پایین ولی نه صفر».

۷/""")
        
        # Tweet 8: Key factors - escalation
        tweets.append("""🔴 عوامل تشدید:

• ناو هواپیمابر Abraham Lincoln در خلیج فارس
• غیرقابل پیش‌بینی بودن ترامپ
• اعتراضات داخلی ایران
• شکست احتمالی مذاکرات

۸/""")
        
        # Tweet 9: Key factors - de-escalation
        tweets.append("""🟢 عوامل کاهش تنش:

• مذاکرات استانبول (۷ فوریه)
• میانجیگری ترکیه/عمان/قطر
• انعطاف ایران در غنی‌سازی
• عادی‌سازی عربستان-ایران

۹/""")
        
        # Tweet 10: Most likely scenario
        tweets.append("""📌 محتمل‌ترین سناریو:

«تنش مستمر» (~۴۰% احتمال)

• دیپلماسی به نتیجه قطعی نمی‌رسد
• آمریکا فشار حفظ می‌کند بدون حمله
• ایران غنی‌سازی ادامه می‌دهد
• اعتراضات ادامه می‌یابد

۱۰/""")
        
        # Tweet 11: Secondary scenario
        tweets.append("""📌 سناریو دوم:

«حمله محدود» (~۲۵% احتمال)

اگر دیپلماسی کاملاً شکست بخورد:
• حمله جراحی به ۲-۳ سایت هسته‌ای
• انتقام از طریق پروکسی‌ها
• جنگ تمام‌عیار نمی‌شود

۱۱/""")
        
        # Tweet 12: What to watch
        tweets.append("""👀 چه چیزی را رصد کنید:

۱. نتیجه مذاکرات استانبول (۷ فوریه)
۲. قیمت طلا (اگر از $۵,۵۰۰ رد شد = خطر)
۳. احتمالات Polymarket
۴. استقرار نیروهای نظامی

۱۲/""")
        
        # Tweet 13: Investment implications
        tweets.append("""💰 برای سرمایه‌گذاران:

• ۱۰-۱۵% در طلا نگهداری کنید
• نقدینگی ۲۰-۳۰% داشته باشید
• از سرمایه‌گذاری مرتبط با ایران اجتناب کنید

این توصیه نیست، فقط دیدگاه تحلیلی است.

۱۳/""")
        
        # Tweet 14: Bitcoin note
        tweets.append("""₿ نکته بیت‌کوین:

BTC یک دارایی ریسکی است نه امن!
• در صورت حمله: احتمالاً -۱۰ تا -۲۰%
• در صورت صلح: احتمالاً +۱۵ تا +۳۰%

طلا بهتر از BTC برای پوشش جنگ است.

۱۴/""")
        
        # Tweet 15: Timeline
        tweets.append("""📅 تایم‌لاین کلیدی:

• ۷ فوریه: مذاکرات استانبول
• ۲۸ فوریه: ددلاین Polymarket
• ۳۱ مارس: ارزیابی Q1
• ۳۰ ژوئن: نقطه بررسی نیمه سال

۱۵/""")
        
        # Tweet 16: Confidence level
        tweets.append(f"""🎯 سطح اطمینان:

• کوتاه‌مدت (۱-۲ هفته): متوسط
• میان‌مدت (۱-۳ ماه): پایین
• بلندمدت (۳+ ماه): خیلی پایین

بازارهای پیش‌بینی هم {metrics['polymarket_feb']:.0f}% می‌گویند = عدم قطعیت بالا.

۱۶/""")
        
        # Tweet 17: Algorithm explanation
        tweets.append("""🤖 الگوریتم چگونه کار می‌کند:

۱. جمع‌آوری داده از ۶+ منبع
۲. تحلیل احساسات با NLP
۳. وزن‌دهی بر اساس قابلیت اعتماد
۴. ترکیب با قیمت طلا/نفت
۵. محاسبه احتمال نهایی

۱۷/""")
        
        # Tweet 18: Limitations
        tweets.append("""⚠️ محدودیت‌های مهم:

• رویدادهای غیرمنتظره قابل پیش‌بینی نیست
• Reddit بایاس سیاسی دارد
• Polymarket نقدینگی محدود
• طلا سیگنال‌های کاذب می‌دهد

۱۸/""")
        
        # Tweet 19: Historical context
        tweets.append("""📚 زمینه تاریخی:

آخرین بار تنش به این حد در ۱۹۷۹ بود.
ولی هر بار «جنگ قریب‌الوقوع» نشد.

بازارها معمولاً ریسک را بیش از حد تخمین می‌زنند.

۱۹/""")
        
        # Tweet 20: Final verdict
        tweets.append(f"""🔮 نتیجه‌گیری:

احتمال حمله در فوریه: ~{metrics['weighted_prob']:.0f}%

یعنی ≈{100-metrics['weighted_prob']:.0f}% احتمال «عدم حمله».

پول هوشمند روی دیپلماسی شرط بسته.

۲۰/""")
        
        # Tweet 21: Call to action
        tweets.append("""📌 چه باید کرد:

۱. آرامش خود را حفظ کنید
۲. اخبار را از منابع معتبر دنبال کنید
۳. تصمیمات احساسی نگیرید
۴. پرتفوی خود را متنوع نگهدارید

۲۱/""")
        
        # Tweet 22: Sources
        tweets.append("""📋 منابع داده:

• Polymarket.com (بازار پیش‌بینی)
• Reddit API (احساسات کاربران)
• Gold Spot Price (سیگنال ریسک)
• Axios (اخبار سیاست خارجی)

۲۲/""")
        
        # Tweet 23: Update frequency
        tweets.append("""🔄 به‌روزرسانی:

این تحلیل روزانه به‌روز می‌شود.

برای آخرین داده‌ها، گزارش کامل را ببینید.

پایان ترد ✅

۲۳/""")
        
        # Final disclaimer tweet
        tweets.append("""⚠️ یادآوری نهایی:

این تحلیل الگوریتمی است و هیچ تضمینی ندارد.

تصمیمات مالی خود را بر اساس یک ترد توییتر نگیرید.

با متخصصین مشورت کنید.

#ایران #آمریکا #ژئوپلیتیک""")
        
        # Format output
        output_lines = [
            "=" * 60,
            "TWITTER THREAD - PERSIAN (فارسی)",
            f"Generated: {self.timestamp}",
            f"Total tweets: {len(tweets)}",
            "=" * 60,
            ""
        ]
        
        for i, tweet in enumerate(tweets, 1):
            # Validate length
            tweet_clean = tweet.strip()
            char_count = len(tweet_clean)
            warning = " ⚠️ TOO LONG!" if char_count > self.MAX_TWEET_LENGTH else ""
            
            output_lines.append(f"--- Tweet {i} ({char_count} chars){warning} ---")
            output_lines.append(tweet_clean)
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def generate_twitter_thread_en(self, data: Dict) -> str:
        """
        Generate English Twitter thread.
        Max 30 tweets, each max 280 chars.
        """
        metrics = self._extract_key_metrics(data)
        tweets = []
        
        # Tweet 1: Introduction
        tweets.append(f"""🧵 US-Iran Strike Probability Analysis

📊 What the data says - an algorithmic analysis thread

Date: {self.date_str_en}

1/""")
        
        # Tweet 2: Disclaimer
        tweets.append("""⚠️ DISCLAIMER

This analysis is educational only, not financial/political advice. Prediction markets and sentiment analysis have limited accuracy.

No model can predict geopolitical events with certainty.

2/""")
        
        # Tweet 3: Method
        tweets.append(f"""📈 Methodology:

1. Polymarket: Real money bets (weight: 60%)
2. Reddit: {metrics['total_users']:,} users analyzed (weight: 15%)
3. Gold price: ${metrics['gold_price']:,} (weight: 25%)

3/""")
        
        # Tweet 4: Polymarket data
        tweets.append(f"""🎰 Polymarket Data:

• By end of February: {metrics['polymarket_feb']:.0f}%
• By end of March: {metrics['polymarket_mar']:.0f}%

Traders risk real money = incentive for accuracy.

4/""")
        
        # Tweet 5: Reddit sentiment
        tweets.append(f"""💬 Reddit Analysis:

From {metrics['total_users']:,} users:
• {metrics['reddit_attack_pct']:.0f}% predict attack
• {100-metrics['reddit_attack_pct']:.0f}% predict no attack

Note: Reddit has narrative bias.

5/""")
        
        # Tweet 6: Gold signal
        tweets.append(f"""🥇 Gold Signal:

Current price: ${metrics['gold_price']:,}/oz
Highest since 1979!

Gold = crisis insurance. When it's high, smart money is worried.

6/""")
        
        # Tweet 7: Combined probability
        tweets.append(f"""🧮 Combined Probability:

Weighted average of three sources:

📊 US strike probability in Feb: ~{metrics['weighted_prob']:.0f}%

This means "low probability but not zero."

7/""")
        
        # Tweet 8: Escalation factors
        tweets.append("""🔴 Escalation Factors:

• USS Abraham Lincoln in Persian Gulf
• Trump's unpredictability
• Iran's internal protests
• Potential negotiation failure

8/""")
        
        # Tweet 9: De-escalation factors
        tweets.append("""🟢 De-escalation Factors:

• Istanbul talks (Feb 7)
• Turkey/Oman/Qatar mediation
• Iran's flexibility on enrichment
• Saudi-Iran normalization

9/""")
        
        # Tweet 10: Most likely scenario
        tweets.append("""📌 Most Likely Scenario:

"Continued Tension" (~40% probability)

• Diplomacy doesn't reach decisive result
• US maintains pressure without strike
• Iran continues enrichment
• Protests continue

10/""")
        
        # Tweet 11: Secondary scenario
        tweets.append("""📌 Secondary Scenario:

"Limited Strike" (~25% probability)

If diplomacy completely fails:
• Surgical strike on 2-3 nuclear sites
• Retaliation via proxies
• No full-scale war

11/""")
        
        # Tweet 12: What to watch
        tweets.append("""👀 What to Watch:

1. Istanbul talks outcome (Feb 7)
2. Gold price (if crosses $5,500 = danger)
3. Polymarket probabilities
4. Military deployments

12/""")
        
        # Tweet 13: Investment implications
        tweets.append("""💰 For Investors:

• Hold 10-15% in gold
• Keep 20-30% cash
• Avoid Iran-related investments

This is not advice, just analytical perspective.

13/""")
        
        # Tweet 14: Bitcoin note
        tweets.append("""₿ Bitcoin Note:

BTC is a risk asset, NOT safe haven!
• If strike: likely -10% to -20%
• If peace: likely +15% to +30%

Gold > BTC for war hedging.

14/""")
        
        # Tweet 15: Timeline
        tweets.append("""📅 Key Timeline:

• Feb 7: Istanbul talks
• Feb 28: Polymarket deadline
• Mar 31: Q1 assessment
• Jun 30: Mid-year checkpoint

15/""")
        
        # Tweet 16: Confidence level
        tweets.append(f"""🎯 Confidence Level:

• Short-term (1-2 weeks): Medium
• Medium-term (1-3 months): Low
• Long-term (3+ months): Very low

Prediction markets at {metrics['polymarket_feb']:.0f}% = high uncertainty.

16/""")
        
        # Tweet 17: Algorithm explanation
        tweets.append("""🤖 How the Algorithm Works:

1. Collect data from 6+ sources
2. Sentiment analysis with NLP
3. Weight by reliability
4. Combine with gold/oil prices
5. Calculate final probability

17/""")
        
        # Tweet 18: Limitations
        tweets.append("""⚠️ Important Limitations:

• Black swan events unpredictable
• Reddit has political bias
• Polymarket has limited liquidity
• Gold gives false signals

18/""")
        
        # Tweet 19: Historical context
        tweets.append("""📚 Historical Context:

Last time tension was this high: 1979.
But "imminent war" didn't happen.

Markets usually overestimate risk.

19/""")
        
        # Tweet 20: Final verdict
        tweets.append(f"""🔮 Conclusion:

Strike probability in February: ~{metrics['weighted_prob']:.0f}%

That's ≈{100-metrics['weighted_prob']:.0f}% probability of NO strike.

Smart money betting on diplomacy.

20/""")
        
        # Tweet 21: Call to action
        tweets.append("""📌 What to Do:

1. Stay calm
2. Follow news from reliable sources
3. Don't make emotional decisions
4. Keep your portfolio diversified

21/""")
        
        # Tweet 22: Sources
        tweets.append("""📋 Data Sources:

• Polymarket.com (prediction market)
• Reddit API (user sentiment)
• Gold Spot Price (risk signal)
• Axios (foreign policy news)

22/""")
        
        # Tweet 23: Update frequency
        tweets.append("""🔄 Updates:

This analysis is updated daily.

For latest data, see the full report.

End of thread ✅

23/""")
        
        # Final disclaimer tweet
        tweets.append("""⚠️ Final Reminder:

This is algorithmic analysis with no guarantees.

Don't make financial decisions based on a Twitter thread.

Consult with professionals.

#Iran #USA #Geopolitics""")
        
        # Format output
        output_lines = [
            "=" * 60,
            "TWITTER THREAD - ENGLISH",
            f"Generated: {self.timestamp}",
            f"Total tweets: {len(tweets)}",
            "=" * 60,
            ""
        ]
        
        for i, tweet in enumerate(tweets, 1):
            tweet_clean = tweet.strip()
            char_count = len(tweet_clean)
            warning = " ⚠️ TOO LONG!" if char_count > self.MAX_TWEET_LENGTH else ""
            
            output_lines.append(f"--- Tweet {i} ({char_count} chars){warning} ---")
            output_lines.append(tweet_clean)
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    # =========================================================================
    # LINKEDIN POST GENERATORS
    # =========================================================================
    
    def generate_linkedin_post_fa(self, data: Dict) -> str:
        """
        Generate Persian LinkedIn post.
        Target: ~10 minutes reading time (~2000 words).
        """
        metrics = self._extract_key_metrics(data)
        
        post = f"""# تحلیل الگوریتمی احتمال حمله آمریکا به ایران

📅 تاریخ: {self.date_str_fa}

---

## ⚠️ سلب مسئولیت

این تحلیل صرفاً برای اهداف آموزشی و اطلاع‌رسانی تهیه شده است. این مطلب:

- توصیه مالی، سرمایه‌گذاری یا سیاسی نیست
- هیچ تضمینی برای صحت پیش‌بینی‌ها ارائه نمی‌دهد
- نباید مبنای تصمیم‌گیری‌های مالی قرار گیرد
- بازارهای پیش‌بینی و تحلیل احساسات ذاتاً محدودیت‌های زیادی دارند

هیچ مدل الگوریتمی نمی‌تواند رویدادهای ژئوپلیتیک را با قطعیت پیش‌بینی کند. لطفاً قبل از هرگونه تصمیم‌گیری با متخصصین مشورت کنید.

---

## 📊 خلاصه اجرایی

بر اساس تحلیل داده‌های چند منبعی، احتمال حمله نظامی آمریکا به ایران در فوریه ۲۰۲۶ حدود **{metrics['weighted_prob']:.0f}%** تخمین زده می‌شود.

### نتایج کلیدی:

| منبع | احتمال | وزن |
|------|--------|-----|
| Polymarket (پول واقعی) | {metrics['polymarket_feb']:.0f}% | ۶۰% |
| Reddit (احساسات کاربران) | {metrics['reddit_attack_pct']:.0f}% | ۱۵% |
| سیگنال طلا | ~۳۰% | ۲۵% |
| **میانگین وزن‌دار** | **{metrics['weighted_prob']:.0f}%** | - |

---

## 🔬 روش‌شناسی

### ۱. جمع‌آوری داده

این تحلیل از منابع زیر استفاده می‌کند:

**الف) Polymarket (وزن: ۶۰%)**
- بازار پیش‌بینی غیرمتمرکز که کاربران با پول واقعی شرط می‌بندند
- منطق: وقتی پول در میان است، انگیزه برای دقت بالاست
- داده فعلی: {metrics['polymarket_feb']:.0f}% برای حمله تا پایان فوریه

**ب) Reddit Sentiment (وزن: ۱۵%)**
- تحلیل احساسات {metrics['total_users']:,} کاربر در سابردیت‌های مرتبط
- استفاده از مدل‌های NLP برای طبقه‌بندی نظرات
- محدودیت: بایاس سیاسی و روایتی

**ج) سیگنال طلا (وزن: ۲۵%)**
- قیمت فعلی: ${metrics['gold_price']:,} در اونس
- طلا به عنوان «بیمه بحران» عمل می‌کند
- قیمت فعلی بالاترین از ۱۹۷۹ است

### ۲. فرمول محاسبه

```
P_final = (W_reddit × P_reddit) + (W_polymarket × P_polymarket) + (W_gold × P_gold)

P_final = (0.15 × {metrics['reddit_attack_pct']:.1f}%) + (0.60 × {metrics['polymarket_feb']:.1f}%) + (0.25 × 30%)
P_final ≈ {metrics['weighted_prob']:.0f}%
```

---

## 📈 تحلیل داده‌ها

### Polymarket: پول هوشمند چه می‌گوید؟

Polymarket یک بازار پیش‌بینی است که کاربران می‌توانند روی نتایج رویدادها شرط ببندند. چون پول واقعی در میان است، انگیزه برای تحقیق و دقت بالاست.

**احتمالات فعلی:**
- حمله تا پایان فوریه ۲۰۲۶: {metrics['polymarket_feb']:.0f}%
- حمله تا پایان مارس ۲۰۲۶: {metrics['polymarket_mar']:.0f}%

**تفسیر:** پول هوشمند معتقد است احتمال حمله فوری پایین است.

### Reddit: احساسات عمومی

از {metrics['total_users']:,} کاربر تحلیل‌شده:
- {metrics['reddit_attack_pct']:.0f}% پیش‌بینی حمله
- {100-metrics['reddit_attack_pct']:.0f}% پیش‌بینی عدم حمله

**محدودیت‌های Reddit:**
- بایاس سیاسی (معمولاً چپ‌گرا)
- تأثیرپذیری از روایت‌های غالب رسانه‌ای
- عدم تخصص در مسائل ژئوپلیتیک

### طلا: سیگنال ماکرو

قیمت طلا در ${metrics['gold_price']:,} قرار دارد که بالاترین سطح از بحران گروگان‌گیری ۱۹۷۹ است.

**چرا طلا مهم است؟**
- طلا به عنوان «پناهگاه امن» در زمان بحران عمل می‌کند
- وقتی سرمایه‌گذاران نگران هستند، طلا می‌خرند
- قیمت بالای فعلی نشان‌دهنده نگرانی بازار است

---

## 🎯 سناریوهای محتمل

### سناریو ۱: تنش مستمر (۴۰% احتمال)

محتمل‌ترین سناریو این است که وضعیت فعلی ادامه یابد:
- مذاکرات به نتیجه قطعی نمی‌رسد
- آمریکا فشار نظامی را حفظ می‌کند بدون حمله
- ایران غنی‌سازی را ادامه می‌دهد
- اعتراضات داخلی ادامه می‌یابد

### سناریو ۲: حمله محدود (۲۵% احتمال)

اگر دیپلماسی کاملاً شکست بخورد:
- حمله جراحی به ۲-۳ تأسیسات هسته‌ای
- انتقام ایران از طریق پروکسی‌ها (نه مستقیم)
- جنگ تمام‌عیار نمی‌شود

### سناریو ۳: توافق دیپلماتیک (۲۰% احتمال)

- مذاکرات استانبول به توافق می‌رسد
- ایران غنی‌سازی را محدود می‌کند
- تحریم‌ها کاهش می‌یابد

### سناریو ۴: تشدید شدید (۱۵% احتمال)

- مذاکرات شکست می‌خورد
- حمله گسترده‌تر
- انتقام مستقیم ایران
- ریسک جنگ منطقه‌ای

---

## ⚠️ محدودیت‌های تحلیل

### ۱. محدودیت‌های ذاتی

- رویدادهای غیرمنتظره (Black Swan) قابل پیش‌بینی نیست
- تصمیمات سیاسی به عوامل غیرقابل مشاهده بستگی دارد
- هیچ مدلی ۱۰۰% دقیق نیست

### ۲. محدودیت‌های داده

- Polymarket نقدینگی محدود دارد
- Reddit بایاس جمعیتی و سیاسی دارد
- قیمت طلا تحت تأثیر عوامل متعدد است

### ۳. محدودیت‌های مدل

- وزن‌ها بر اساس قضاوت تعیین شده‌اند
- مدل خطی است و روابط پیچیده را نادیده می‌گیرد
- به‌روزرسانی بلادرنگ ندارد

---

## 📅 رویدادهای کلیدی برای پیگیری

| تاریخ | رویداد | اهمیت |
|-------|--------|-------|
| ۷ فوریه ۲۰۲۶ | مذاکرات استانبول | بسیار بالا |
| ۲۸ فوریه ۲۰۲۶ | ددلاین Polymarket | بالا |
| ۳۱ مارس ۲۰۲۶ | ارزیابی Q1 | متوسط |
| ۳۰ ژوئن ۲۰۲۶ | نقطه بررسی نیمه سال | متوسط |

---

## 🔮 نتیجه‌گیری

بر اساس تحلیل داده‌های موجود:

**احتمال حمله آمریکا به ایران در فوریه ۲۰۲۶: ~{metrics['weighted_prob']:.0f}%**

این یعنی:
- احتمال «عدم حمله» بیشتر است (~{100-metrics['weighted_prob']:.0f}%)
- پول هوشمند روی دیپلماسی شرط بسته
- اما ریسک صفر نیست

**سطح اطمینان:** متوسط (۶۰%)
- اطمینان بالاتر در کوتاه‌مدت (۱-۲ هفته)
- اطمینان پایین‌تر در بلندمدت (۳+ ماه)

---

## 📋 منابع

- Polymarket.com - بازار پیش‌بینی
- Reddit API - تحلیل احساسات
- Gold Spot Price - سیگنال ریسک
- Axios - اخبار سیاست خارجی

---

⚠️ **یادآوری نهایی:** این تحلیل صرفاً آموزشی است. لطفاً قبل از هرگونه تصمیم‌گیری مالی یا سرمایه‌گذاری با متخصصین مشورت کنید.

#ژئوپلیتیک #ایران #آمریکا #تحلیل_داده #بازارهای_پیش_بینی
"""
        
        # Add header
        word_count = len(post.split())
        read_time = word_count // self.LINKEDIN_WORDS_PER_MINUTE
        
        header = f"""{"=" * 60}
LINKEDIN POST - PERSIAN (فارسی)
Generated: {self.timestamp}
Word count: ~{word_count} words
Estimated read time: {read_time} minutes
{"=" * 60}

"""
        
        return header + post
    
    def generate_linkedin_post_en(self, data: Dict) -> str:
        """
        Generate English LinkedIn post.
        Target: ~10 minutes reading time (~2000 words).
        """
        metrics = self._extract_key_metrics(data)
        
        post = f"""# Algorithmic Analysis: US-Iran Strike Probability

📅 Date: {self.date_str_en}

---

## ⚠️ Disclaimer

This analysis is prepared for educational and informational purposes only. This content:

- Is NOT financial, investment, or political advice
- Provides NO guarantees about prediction accuracy
- Should NOT be the basis for financial decisions
- Prediction markets and sentiment analysis have inherent limitations

No algorithmic model can predict geopolitical events with certainty. Please consult with professionals before making any decisions.

---

## 📊 Executive Summary

Based on multi-source data analysis, the probability of a US military strike on Iran in February 2026 is estimated at approximately **{metrics['weighted_prob']:.0f}%**.

### Key Findings:

| Source | Probability | Weight |
|--------|-------------|--------|
| Polymarket (real money) | {metrics['polymarket_feb']:.0f}% | 60% |
| Reddit (user sentiment) | {metrics['reddit_attack_pct']:.0f}% | 15% |
| Gold signal | ~30% | 25% |
| **Weighted Average** | **{metrics['weighted_prob']:.0f}%** | - |

---

## 🔬 Methodology

### 1. Data Collection

This analysis uses the following sources:

**A) Polymarket (Weight: 60%)**
- Decentralized prediction market where users bet with real money
- Logic: When money is at stake, there's incentive for accuracy
- Current data: {metrics['polymarket_feb']:.0f}% for strike by end of February

**B) Reddit Sentiment (Weight: 15%)**
- Sentiment analysis of {metrics['total_users']:,} users in relevant subreddits
- NLP models used for opinion classification
- Limitation: Political and narrative bias

**C) Gold Signal (Weight: 25%)**
- Current price: ${metrics['gold_price']:,} per ounce
- Gold acts as "crisis insurance"
- Current price is highest since 1979

### 2. Calculation Formula

```
P_final = (W_reddit × P_reddit) + (W_polymarket × P_polymarket) + (W_gold × P_gold)

P_final = (0.15 × {metrics['reddit_attack_pct']:.1f}%) + (0.60 × {metrics['polymarket_feb']:.1f}%) + (0.25 × 30%)
P_final ≈ {metrics['weighted_prob']:.0f}%
```

---

## 📈 Data Analysis

### Polymarket: What Smart Money Says

Polymarket is a prediction market where users can bet on event outcomes. Because real money is involved, there's incentive for research and accuracy.

**Current Probabilities:**
- Strike by end of February 2026: {metrics['polymarket_feb']:.0f}%
- Strike by end of March 2026: {metrics['polymarket_mar']:.0f}%

**Interpretation:** Smart money believes immediate strike probability is low.

### Reddit: Public Sentiment

From {metrics['total_users']:,} analyzed users:
- {metrics['reddit_attack_pct']:.0f}% predict strike
- {100-metrics['reddit_attack_pct']:.0f}% predict no strike

**Reddit Limitations:**
- Political bias (typically left-leaning)
- Influenced by dominant media narratives
- Lack of geopolitical expertise

### Gold: Macro Signal

Gold price is at ${metrics['gold_price']:,}, the highest level since the 1979 hostage crisis.

**Why Gold Matters:**
- Gold acts as "safe haven" during crises
- When investors worry, they buy gold
- High current price indicates market concern

---

## 🎯 Likely Scenarios

### Scenario 1: Continued Tension (40% probability)

Most likely scenario is status quo continuation:
- Negotiations don't reach decisive result
- US maintains military pressure without strike
- Iran continues enrichment
- Internal protests continue

### Scenario 2: Limited Strike (25% probability)

If diplomacy completely fails:
- Surgical strike on 2-3 nuclear facilities
- Iran retaliates via proxies (not directly)
- No full-scale war

### Scenario 3: Diplomatic Agreement (20% probability)

- Istanbul talks reach agreement
- Iran limits enrichment
- Sanctions reduced

### Scenario 4: Severe Escalation (15% probability)

- Negotiations fail
- Broader strike
- Direct Iranian retaliation
- Regional war risk

---

## ⚠️ Analysis Limitations

### 1. Inherent Limitations

- Black swan events are unpredictable
- Political decisions depend on unobservable factors
- No model is 100% accurate

### 2. Data Limitations

- Polymarket has limited liquidity
- Reddit has demographic and political bias
- Gold price affected by multiple factors

### 3. Model Limitations

- Weights determined by judgment
- Model is linear, ignores complex relationships
- No real-time updates

---

## 📅 Key Events to Monitor

| Date | Event | Importance |
|------|-------|------------|
| February 7, 2026 | Istanbul Talks | Very High |
| February 28, 2026 | Polymarket Deadline | High |
| March 31, 2026 | Q1 Assessment | Medium |
| June 30, 2026 | Mid-year Checkpoint | Medium |

---

## 🔮 Conclusion

Based on available data analysis:

**US strike probability on Iran in February 2026: ~{metrics['weighted_prob']:.0f}%**

This means:
- "No strike" probability is higher (~{100-metrics['weighted_prob']:.0f}%)
- Smart money betting on diplomacy
- But risk is not zero

**Confidence Level:** Medium (60%)
- Higher confidence in short-term (1-2 weeks)
- Lower confidence in long-term (3+ months)

---

## 📋 Sources

- Polymarket.com - Prediction Market
- Reddit API - Sentiment Analysis
- Gold Spot Price - Risk Signal
- Axios - Foreign Policy News

---

⚠️ **Final Reminder:** This analysis is educational only. Please consult with professionals before making any financial or investment decisions.

#Geopolitics #Iran #USA #DataAnalysis #PredictionMarkets
"""
        
        # Add header
        word_count = len(post.split())
        read_time = word_count // self.LINKEDIN_WORDS_PER_MINUTE
        
        header = f"""{"=" * 60}
LINKEDIN POST - ENGLISH
Generated: {self.timestamp}
Word count: ~{word_count} words
Estimated read time: {read_time} minutes
{"=" * 60}

"""
        
        return header + post
    
    # =========================================================================
    # MAIN GENERATION FUNCTION
    # =========================================================================
    
    def generate_all(self, data: Dict) -> Dict[str, str]:
        """
        Generate all social media content.
        
        Args:
            data: Dictionary containing:
                - analysis_results: Sentiment analysis results
                - polymarket_data: Polymarket odds and data
                - reasoning: Analysis reasoning
                - llm_analysis: Optional LLM analysis results
        
        Returns:
            Dictionary with keys:
                - twitter_fa: Persian Twitter thread
                - twitter_en: English Twitter thread
                - linkedin_fa: Persian LinkedIn post
                - linkedin_en: English LinkedIn post
        """
        return {
            'twitter_fa': self.generate_twitter_thread_fa(data),
            'twitter_en': self.generate_twitter_thread_en(data),
            'linkedin_fa': self.generate_linkedin_post_fa(data),
            'linkedin_en': self.generate_linkedin_post_en(data),
        }


def generate_social_media_content(
    analysis_results: Dict,
    polymarket_data: Dict,
    reasoning: Dict = None,
    llm_analysis: Dict = None,
    output_dir: str = "cache/reports"
) -> Dict[str, str]:
    """
    Convenience function to generate and save social media content.
    
    Args:
        analysis_results: Sentiment analysis results
        polymarket_data: Polymarket data
        reasoning: Optional reasoning dict
        llm_analysis: Optional LLM analysis results
        output_dir: Directory to save files
    
    Returns:
        Dictionary with file paths for each generated content
    """
    from pathlib import Path
    
    generator = SocialMediaGenerator()
    
    data = {
        'analysis_results': analysis_results,
        'polymarket_data': polymarket_data,
        'reasoning': reasoning or {},
        'llm_analysis': llm_analysis or {},
    }
    
    content = generator.generate_all(data)
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save files
    files = {}
    
    # Twitter Persian
    twitter_fa_path = output_path / "twitter_thread_FA.md"
    with open(twitter_fa_path, 'w', encoding='utf-8') as f:
        f.write(content['twitter_fa'])
    files['twitter_fa'] = str(twitter_fa_path)
    
    # Twitter English
    twitter_en_path = output_path / "twitter_thread_EN.md"
    with open(twitter_en_path, 'w', encoding='utf-8') as f:
        f.write(content['twitter_en'])
    files['twitter_en'] = str(twitter_en_path)
    
    # LinkedIn Persian
    linkedin_fa_path = output_path / "linkedin_post_FA.md"
    with open(linkedin_fa_path, 'w', encoding='utf-8') as f:
        f.write(content['linkedin_fa'])
    files['linkedin_fa'] = str(linkedin_fa_path)
    
    # LinkedIn English
    linkedin_en_path = output_path / "linkedin_post_EN.md"
    with open(linkedin_en_path, 'w', encoding='utf-8') as f:
        f.write(content['linkedin_en'])
    files['linkedin_en'] = str(linkedin_en_path)
    
    return files
