"""
Chart Generator Module
Generates visualizations for the US-Iran Conflict Prediction Report.
Uses matplotlib and seaborn for high-quality static charts.
"""

# Fix mpl_toolkits namespace package conflict (user site vs system)
# Must be done BEFORE any matplotlib import
# Note: We prioritize user site but DON'T remove system dist-packages entirely
# because some packages (like 'distro' needed by anthropic) are only there.
import sys
import warnings
_user_site = '/home/erfan/.local/lib/python3.10/site-packages'

# Prioritize user site packages
if _user_site in sys.path:
    sys.path.remove(_user_site)
sys.path.insert(0, _user_site)

# Suppress the Axes3D warning (we've fixed the path)
warnings.filterwarnings('ignore', message='.*Unable to import Axes3D.*')
# Suppress font-related warnings (we handle missing glyphs gracefully)
warnings.filterwarnings('ignore', message='.*Glyph.*missing from.*')
warnings.filterwarnings('ignore', message='.*Matplotlib currently does not support.*')

import os
import re
import textwrap
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import numpy as np
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime as _dt

# =============================================================================
# FONT CONFIGURATION - Support Arabic/Persian and Unicode symbols
# =============================================================================

def _configure_fonts():
    """Configure matplotlib fonts with Arabic/Persian support."""
    # Clear font cache to ensure fresh detection
    fm._load_fontmanager(try_read_cache=False)
    
    # Define font paths to check
    user_font_dir = Path.home() / '.local' / 'share' / 'fonts'
    system_font_dirs = [
        Path('/usr/share/fonts/truetype'),
        Path('/usr/share/fonts'),
    ]
    
    # Look for Vazirmatn (best Persian font)
    vazirmatn_path = None
    for pattern in ['Vazirmatn-Regular.ttf', '1Vazirmatn-Regular.ttf', 'Vazirmatn*.ttf']:
        matches = list(user_font_dir.glob(pattern))
        if matches:
            vazirmatn_path = str(matches[0])
            break
    
    # Add custom font paths
    if vazirmatn_path:
        fm.fontManager.addfont(vazirmatn_path)
    
    # Configure font families with fallbacks
    # Priority: Vazirmatn (Persian) -> DejaVu Sans (symbols) -> Liberation Sans -> sans-serif
    persian_fonts = ['Vazirmatn', 'DejaVu Sans', 'FreeSans', 'Liberation Sans', 'sans-serif']
    english_fonts = ['DejaVu Sans', 'Liberation Sans', 'FreeSans', 'sans-serif']
    
    # Set default font family
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = persian_fonts
    
    # Enable text rendering with proper Unicode support
    plt.rcParams['axes.unicode_minus'] = False  # Use proper minus sign
    
    return vazirmatn_path is not None

# Initialize fonts
_HAS_PERSIAN_FONT = _configure_fonts()

# Set style for all charts
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    try:
        plt.style.use('seaborn-whitegrid')
    except:
        plt.style.use('ggplot')  # Fallback
sns.set_palette("husl")

# Re-apply font settings after style (styles can override fonts)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Vazirmatn', 'DejaVu Sans', 'FreeSans', 'Liberation Sans', 'sans-serif']

# Custom color schemes
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Magenta
    'success': '#28A745',      # Green
    'danger': '#DC3545',       # Red
    'warning': '#FFC107',      # Yellow
    'info': '#17A2B8',         # Cyan
    'light': '#F8F9FA',        # Light gray
    'dark': '#343A40',         # Dark gray
    'gold': '#FFD700',         # Gold
    'bitcoin': '#F7931A',      # Bitcoin orange
    'polymarket': '#7B68EE',   # Purple
    'reddit': '#FF4500',       # Reddit orange
    'yes': '#28A745',          # Green for YES
    'no': '#DC3545',           # Red for NO
}

# Probability color gradient
PROB_COLORS = ['#28A745', '#7CB342', '#C0CA33', '#FDD835', '#FFB300', '#FB8C00', '#F4511E', '#DC3545']


# =============================================================================
# PERSIAN TEXT RENDERING HELPERS
# =============================================================================

# Try to import arabic-reshaper and python-bidi for proper RTL text rendering
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _HAS_BIDI = True
except ImportError:
    _HAS_BIDI = False

def render_persian_text(text: str) -> str:
    """
    Render Persian/Arabic text properly for matplotlib.
    Applies RTL reshaping if arabic-reshaper and python-bidi are available.
    """
    if not text:
        return text
    
    # Check if text contains Persian/Arabic characters
    has_arabic = any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or 
                     '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF'
                     for c in text)
    
    if not has_arabic:
        return text
    
    if _HAS_BIDI:
        # Reshape Arabic/Persian text for proper display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    else:
        # Without bidi support, just return the text
        # It may not display perfectly but will work
        return text

def sanitize_text_for_chart(text: str) -> str:
    """
    Sanitize text for chart display, replacing problematic Unicode symbols
    with ASCII equivalents when necessary.
    """
    if not text:
        return text
    
    # Replace common problematic symbols with ASCII alternatives
    replacements = {
        '⬇': 'v',      # DOWNWARDS BLACK ARROW
        '⬆': '^',      # UPWARDS BLACK ARROW  
        '⬅': '<',      # LEFTWARDS BLACK ARROW
        '➡': '>',      # RIGHTWARDS BLACK ARROW
        '▼': 'v',      # BLACK DOWN-POINTING TRIANGLE
        '▲': '^',      # BLACK UP-POINTING TRIANGLE
        '●': '*',      # BLACK CIRCLE
        '○': 'o',      # WHITE CIRCLE
        '✓': '+',      # CHECK MARK
        '✗': 'x',      # BALLOT X
        '★': '*',      # BLACK STAR
        '☆': '*',      # WHITE STAR
        '\uFE0F': '',  # VARIATION SELECTOR-16 (remove)
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize Arabic/Persian digits to ASCII
    digit_map = {
        "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
        "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
        "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
        "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    }
    for old, new in digit_map.items():
        text = text.replace(old, new)

    # Force ASCII-only for chart text (prevents Persian rendering issues)
    cleaned = "".join(ch if 32 <= ord(ch) <= 126 else " " for ch in text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def wrap_text_for_chart(text: str, width: int = 18) -> str:
    """Wrap long labels to improve readability in dense charts."""
    if not text:
        return text
    cleaned = sanitize_text_for_chart(str(text))
    return "\n".join(textwrap.wrap(cleaned, width=width)) if len(cleaned) > width else cleaned


class ChartGenerator:
    """Generates charts for the prediction report."""
    
    def __init__(self, output_dir: str = "cache/charts"):
        """Initialize chart generator with output directory."""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.generated_charts = []
        self.has_persian_font = _HAS_PERSIAN_FONT
        self.has_bidi = _HAS_BIDI
        
        # Configure matplotlib for better quality
        plt.rcParams['figure.dpi'] = 180
        plt.rcParams['savefig.dpi'] = 200
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.titlesize'] = 13
        plt.rcParams['axes.labelsize'] = 11
        
        # Ensure font settings are applied
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Vazirmatn', 'DejaVu Sans', 'FreeSans', 'Liberation Sans', 'sans-serif']
    
    def _save_chart(self, fig, name: str) -> str:
        """Save chart and return path relative for reports in cache/reports/."""
        filename = f"{name}_{self.timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        self.generated_charts.append(filepath)
        # Also copy into cache/reports/charts for Typora-friendly relative paths
        try:
            reports_charts_dir = Path(self.output_dir).parent / "reports" / "charts"
            reports_charts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(filepath, reports_charts_dir / filename)
        except Exception:
            pass

        # Return path relative to cache/reports/ directory (where reports are saved)
        # cache/reports/report_EN.md -> charts/foo.png
        return f"charts/{filename}"
    
    # =========================================================================
    # 1. PROBABILITY DISTRIBUTION CHARTS
    # =========================================================================
    
    def create_probability_gauge(self, probability: float, title: str = "Strike Probability") -> str:
        """
        Create a gauge/speedometer chart for probability.
        
        Args:
            probability: Value between 0-100
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(8, 5), subplot_kw={'projection': 'polar'})
        
        # Gauge settings
        theta_min, theta_max = np.pi, 0  # Left to right
        theta_range = theta_max - theta_min
        
        # Draw colored arc segments
        n_segments = 100
        for i in range(n_segments):
            theta_start = theta_min + (i / n_segments) * theta_range
            theta_end = theta_min + ((i + 1) / n_segments) * theta_range
            
            # Color based on position (green to red)
            color_idx = int(i / n_segments * (len(PROB_COLORS) - 1))
            color = PROB_COLORS[color_idx]
            
            ax.bar(
                (theta_start + theta_end) / 2,
                0.4,
                width=(theta_end - theta_start) * 1.1,
                bottom=0.6,
                color=color,
                alpha=0.8
            )
        
        # Draw needle
        needle_theta = theta_min + (probability / 100) * theta_range
        ax.annotate(
            '',
            xy=(needle_theta, 0.95),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle='->', color=COLORS['dark'], lw=3)
        )
        
        # Center circle
        circle = plt.Circle((0, 0), 0.15, transform=ax.transData._b, color=COLORS['dark'], zorder=10)
        ax.add_artist(circle)
        
        # Labels
        ax.set_ylim(0, 1.2)
        ax.set_theta_offset(np.pi)
        ax.set_theta_direction(-1)
        ax.set_thetagrids([])
        ax.set_rgrids([])
        ax.spines['polar'].set_visible(False)
        
        # Add percentage labels
        for pct in [0, 25, 50, 75, 100]:
            theta = theta_min + (pct / 100) * theta_range
            ax.text(theta, 1.1, f'{pct}%', ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Title and value
        ax.text(0, -0.3, f'{probability:.1f}%', ha='center', va='center', 
                fontsize=28, fontweight='bold', color=COLORS['dark'],
                transform=ax.transAxes)
        ax.text(0.5, 1.15, title, ha='center', va='center', 
                fontsize=14, fontweight='bold', transform=ax.transAxes)
        
        return self._save_chart(fig, "probability_gauge")
    
    def create_probability_comparison(self, probabilities: Dict[str, float], title: str = "Probability by Source") -> str:
        """
        Create horizontal bar chart comparing probabilities from different sources.
        
        Args:
            probabilities: Dict of {source_name: probability}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sources = list(probabilities.keys())
        values = list(probabilities.values())
        
        # Color based on value
        colors = [PROB_COLORS[min(int(v / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)] for v in values]
        
        # Create horizontal bars
        bars = ax.barh(sources, values, color=colors, edgecolor='white', linewidth=1)
        
        # Add value labels
        for bar, val in zip(bars, values):
            ax.text(val + 1, bar.get_y() + bar.get_height()/2, 
                   f'{val:.1f}%', va='center', ha='left', fontsize=11, fontweight='bold')
        
        ax.set_xlim(0, 100)
        ax.set_xlabel('Probability (%)', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.axvline(x=50, color=COLORS['dark'], linestyle='--', alpha=0.3, label='50% threshold')
        
        # Add legend
        ax.legend(loc='lower right')
        
        plt.tight_layout()
        return self._save_chart(fig, "probability_comparison")
    
    def create_probability_donut(self, yes_prob: float, title: str = "Attack Probability") -> str:
        """
        Create a donut chart showing YES vs NO probability.
        
        Args:
            yes_prob: Probability of YES (0-100)
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        
        no_prob = 100 - yes_prob
        sizes = [yes_prob, no_prob]
        colors = [COLORS['danger'], COLORS['success']]
        labels = ['YES (Strike)', 'NO (No Strike)']
        explode = (0.02, 0)
        
        # Create donut
        wedges, texts, autotexts = ax.pie(
            sizes, 
            explode=explode,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.75,
            wedgeprops=dict(width=0.5, edgecolor='white')
        )
        
        # Style
        plt.setp(autotexts, size=14, weight='bold', color='white')
        plt.setp(texts, size=12)
        
        # Center text
        ax.text(0, 0, f'{yes_prob:.1f}%\nYES', ha='center', va='center', 
                fontsize=24, fontweight='bold', color=COLORS['danger'])
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        return self._save_chart(fig, "probability_donut")
    
    # =========================================================================
    # 2. TIMELINE / DEADLINE CHARTS
    # =========================================================================
    
    def create_deadline_timeline(self, deadlines: List[Dict[str, Any]], title: str = "Market Deadlines") -> str:
        """
        Create a timeline visualization of prediction market deadlines.
        
        Args:
            deadlines: List of {date, label, probability, volume}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Sort by date
        deadlines = sorted(deadlines, key=lambda x: x.get('date', ''))
        
        # Timeline base
        y_base = 0.5
        ax.axhline(y=y_base, color=COLORS['dark'], linewidth=3, alpha=0.3)
        
        # Plot each deadline
        for i, dl in enumerate(deadlines):
            x = i
            prob = dl.get('probability', 50)
            label = dl.get('label', f'Deadline {i+1}')
            date = dl.get('date', '')
            volume = dl.get('volume', 0)
            
            # Marker size based on volume
            size = 200 + (volume / 1000000) * 100 if volume else 300
            
            # Color based on probability
            color_idx = min(int(prob / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)
            color = PROB_COLORS[color_idx]
            
            # Plot point
            ax.scatter(x, y_base, s=size, c=[color], zorder=5, edgecolors='white', linewidths=2)
            
            # Alternating labels above/below
            y_offset = 0.25 if i % 2 == 0 else -0.25
            va = 'bottom' if i % 2 == 0 else 'top'
            
            ax.annotate(
                f'{label}\n{prob:.0f}%\n{date}',
                xy=(x, y_base),
                xytext=(x, y_base + y_offset),
                ha='center', va=va,
                fontsize=9,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.9),
                arrowprops=dict(arrowstyle='-', color=color, lw=1)
            )
        
        ax.set_xlim(-0.5, len(deadlines) - 0.5)
        ax.set_ylim(0, 1)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.axis('off')
        
        # Legend for probability colors
        patches = [mpatches.Patch(color=PROB_COLORS[0], label='Low Risk'),
                   mpatches.Patch(color=PROB_COLORS[len(PROB_COLORS)//2], label='Medium Risk'),
                   mpatches.Patch(color=PROB_COLORS[-1], label='High Risk')]
        ax.legend(handles=patches, loc='upper right', fontsize=9)
        
        plt.tight_layout()
        return self._save_chart(fig, "deadline_timeline")
    
    # =========================================================================
    # 3. SENTIMENT ANALYSIS CHARTS
    # =========================================================================
    
    def create_sentiment_breakdown(self, sentiments: Dict[str, int], title: str = "Sentiment Distribution") -> str:
        """
        Create a stacked bar or pie chart for sentiment breakdown.
        
        Args:
            sentiments: Dict of {sentiment_type: count}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Prepare data
        labels = list(sentiments.keys())
        values = list(sentiments.values())
        total = sum(values)
        percentages = [v/total*100 if total > 0 else 0 for v in values]
        
        # Color mapping
        color_map = {
            'positive': COLORS['success'],
            'negative': COLORS['danger'],
            'neutral': COLORS['warning'],
            'bullish': COLORS['success'],
            'bearish': COLORS['danger'],
            'attack_likely': COLORS['danger'],
            'no_attack': COLORS['success'],
            'uncertain': COLORS['warning'],
        }
        colors = [color_map.get(l.lower(), COLORS['info']) for l in labels]
        
        # Pie chart
        wedges, texts, autotexts = ax1.pie(
            values, 
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.75
        )
        plt.setp(autotexts, size=11, weight='bold')
        ax1.set_title('Distribution', fontsize=12, fontweight='bold')
        
        # Bar chart
        bars = ax2.bar(labels, values, color=colors, edgecolor='white', linewidth=1)
        for bar, val, pct in zip(bars, values, percentages):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                    f'{val:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax2.set_ylabel('Count', fontsize=11)
        ax2.set_title('Absolute Numbers', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        return self._save_chart(fig, "sentiment_breakdown")
    
    def create_reddit_sentiment_chart(self, attack_likely: int, no_attack: int, uncertain: int,
                                      title: str = "Reddit User Predictions") -> str:
        """
        Create a visual representation of Reddit sentiment.
        
        Args:
            attack_likely: Users predicting attack
            no_attack: Users predicting no attack
            uncertain: Uncertain users
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        total = attack_likely + no_attack + uncertain
        categories = ['Attack Likely', 'No Attack', 'Uncertain']
        values = [attack_likely, no_attack, uncertain]
        colors = [COLORS['danger'], COLORS['success'], COLORS['warning']]
        
        # Horizontal stacked bar
        left = 0
        for cat, val, color in zip(categories, values, colors):
            pct = val / total * 100 if total > 0 else 0
            ax.barh(0, pct, left=left, color=color, height=0.5, label=f'{cat}: {val:,} ({pct:.1f}%)')
            
            # Label inside if wide enough
            if pct > 10:
                ax.text(left + pct/2, 0, f'{pct:.1f}%', ha='center', va='center', 
                       fontsize=12, fontweight='bold', color='white')
            left += pct
        
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel('Percentage of Users', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_yticks([])
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)
        
        plt.tight_layout()
        return self._save_chart(fig, "reddit_sentiment")
    
    # =========================================================================
    # 4. MARKET COMPARISON CHARTS
    # =========================================================================
    
    def create_market_comparison(self, gold_price: float, btc_price: float,
                                  gold_change: float = 0, btc_change: float = 0,
                                  title: str = "Safe Haven Assets Comparison") -> str:
        """
        Create a comparison chart of gold and bitcoin.
        
        Args:
            gold_price: Current gold price per oz
            btc_price: Current BTC price
            gold_change: 24h change percentage
            btc_change: 24h change percentage
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Price comparison (normalized)
        assets = ['Gold\n(per oz)', 'Bitcoin']
        prices = [gold_price, btc_price]
        colors = [COLORS['gold'], COLORS['bitcoin']]
        
        bars = ax1.bar(assets, prices, color=colors, edgecolor='white', linewidth=2)
        for bar, price in zip(bars, prices):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(prices)*0.02,
                    f'${price:,.0f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax1.set_ylabel('Price (USD)', fontsize=11)
        ax1.set_title('Current Prices', fontsize=12, fontweight='bold')
        ax1.set_yscale('log')  # Log scale due to large difference
        
        # 24h Change
        changes = [gold_change, btc_change]
        colors_change = [COLORS['success'] if c >= 0 else COLORS['danger'] for c in changes]
        
        bars2 = ax2.bar(assets, changes, color=colors_change, edgecolor='white', linewidth=2)
        for bar, change in zip(bars2, changes):
            y_pos = bar.get_height() + 0.1 if change >= 0 else bar.get_height() - 0.3
            ax2.text(bar.get_x() + bar.get_width()/2, y_pos,
                    f'{change:+.2f}%', ha='center', va='bottom' if change >= 0 else 'top',
                    fontsize=12, fontweight='bold')
        
        ax2.axhline(y=0, color=COLORS['dark'], linestyle='-', linewidth=1)
        ax2.set_ylabel('Change (%)', fontsize=11)
        ax2.set_title('24h Price Change', fontsize=12, fontweight='bold')
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        return self._save_chart(fig, "market_comparison")
    
    def create_crisis_correlation_chart(self, title: str = "Asset Behavior in Crisis") -> str:
        """
        Create a chart showing typical asset behavior during geopolitical crisis.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Typical behavior patterns (illustrative)
        phases = ['Normal', 'Tension\nRising', 'Crisis\nPeak', 'Immediate\nAftermath', 'Recovery']
        gold = [100, 105, 115, 112, 108]
        btc = [100, 95, 85, 88, 105]
        stocks = [100, 98, 80, 85, 95]
        oil = [100, 110, 140, 130, 115]
        
        x = np.arange(len(phases))
        
        ax.plot(x, gold, 'o-', color=COLORS['gold'], linewidth=3, markersize=10, label='Gold')
        ax.plot(x, btc, 's-', color=COLORS['bitcoin'], linewidth=3, markersize=10, label='Bitcoin')
        ax.plot(x, stocks, '^-', color=COLORS['primary'], linewidth=3, markersize=10, label='Stocks')
        ax.plot(x, oil, 'd-', color=COLORS['dark'], linewidth=3, markersize=10, label='Oil')
        
        ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Baseline')
        
        # Highlight crisis zone
        ax.axvspan(1.5, 3.5, alpha=0.2, color=COLORS['danger'], label='Crisis Period')
        
        ax.set_xticks(x)
        ax.set_xticklabels(phases, fontsize=10)
        ax.set_ylabel('Indexed Value (100 = Normal)', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.legend(loc='upper left', fontsize=10)
        ax.set_ylim(70, 150)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._save_chart(fig, "crisis_correlation")
    
    # =========================================================================
    # 5. PORTFOLIO ALLOCATION CHARTS
    # =========================================================================
    
    def create_portfolio_allocation(self, allocations: Dict[str, float], 
                                    title: str = "Recommended Portfolio Allocation") -> str:
        """
        Create a pie/donut chart for portfolio allocation.
        
        Args:
            allocations: Dict of {asset: percentage}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = list(allocations.keys())
        sizes = list(allocations.values())
        
        # Custom colors
        color_map = {
            'gold': COLORS['gold'],
            'bitcoin': COLORS['bitcoin'],
            'btc': COLORS['bitcoin'],
            'cash': COLORS['light'],
            'usd': COLORS['success'],
            'stocks': COLORS['primary'],
            'polymarket': COLORS['polymarket'],
            'bonds': COLORS['info'],
            'oil': COLORS['dark'],
        }
        colors = []
        for label in labels:
            label_lower = label.lower()
            matched = False
            for key, color in color_map.items():
                if key in label_lower:
                    colors.append(color)
                    matched = True
                    break
            if not matched:
                colors.append(COLORS['secondary'])
        
        # Create donut
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.75,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
        )
        
        plt.setp(autotexts, size=11, weight='bold')
        plt.setp(texts, size=10)
        
        # Center text
        ax.text(0, 0, 'Portfolio\nAllocation', ha='center', va='center',
                fontsize=14, fontweight='bold', color=COLORS['dark'])
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        return self._save_chart(fig, "portfolio_allocation")
    
    def create_scenario_portfolios(self, scenarios: Dict[str, Dict[str, float]],
                                   title: str = "Portfolio by Scenario") -> str:
        """
        Create a comparison chart of portfolios for different scenarios.
        
        Args:
            scenarios: Dict of {scenario_name: {asset: percentage}}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, axes = plt.subplots(1, len(scenarios), figsize=(5*len(scenarios), 5))
        
        if len(scenarios) == 1:
            axes = [axes]
        
        scenario_colors = {
            'attack': COLORS['danger'],
            'no attack': COLORS['success'],
            'diplomatic': COLORS['info'],
            'base': COLORS['warning'],
        }
        
        for ax, (scenario_name, allocation) in zip(axes, scenarios.items()):
            labels = list(allocation.keys())
            sizes = list(allocation.values())
            
            # Get scenario color
            sc_color = COLORS['secondary']
            for key, color in scenario_colors.items():
                if key in scenario_name.lower():
                    sc_color = color
                    break
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct='%1.0f%%',
                startangle=90,
                pctdistance=0.75,
                wedgeprops=dict(width=0.5, edgecolor='white')
            )
            
            plt.setp(autotexts, size=9, weight='bold')
            plt.setp(texts, size=8)
            ax.set_title(scenario_name, fontsize=11, fontweight='bold', color=sc_color)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        return self._save_chart(fig, "scenario_portfolios")
    
    # =========================================================================
    # 6. TOP TRADERS CHARTS
    # =========================================================================
    
    def create_top_traders_chart(self, traders: List[Dict[str, Any]],
                                  title: str = "Top Polymarket Traders") -> str:
        """
        Create a bar chart showing top traders' win rates and positions.
        
        Args:
            traders: List of trader dictionaries with username, win_rate, iran_position
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Extract data
        usernames = [t.get('username', f'Trader {i}') for i, t in enumerate(traders)]
        win_rates = [t.get('win_rate', 50) for t in traders]
        positions = [t.get('iran_position', 'NO') for t in traders]
        profits = [t.get('total_profit', '$0') for t in traders]
        
        # Colors based on position
        colors = [COLORS['danger'] if p.upper() == 'YES' else COLORS['success'] for p in positions]
        
        # Create bars
        bars = ax.bar(usernames, win_rates, color=colors, edgecolor='white', linewidth=2)
        
        # Add labels
        for bar, win_rate, position, profit in zip(bars, win_rates, positions, profits):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{win_rate}%\n{position}', ha='center', va='bottom',
                   fontsize=9, fontweight='bold')
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                   profit, ha='center', va='center',
                   fontsize=8, fontweight='bold', color='white', rotation=90)
        
        ax.set_ylim(0, 100)
        ax.set_ylabel('Win Rate (%)', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.tick_params(axis='x', rotation=45)
        ax.axhline(y=50, color=COLORS['dark'], linestyle='--', alpha=0.3, label='50% baseline')
        
        # Legend
        legend_elements = [
            mpatches.Patch(facecolor=COLORS['danger'], label='Position: YES (Strike)'),
            mpatches.Patch(facecolor=COLORS['success'], label='Position: NO (No Strike)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        plt.tight_layout()
        return self._save_chart(fig, "top_traders")
    
    def create_smart_money_indicator(self, yes_pct: float, no_pct: float, volume: str,
                                     title: str = "Smart Money Signal") -> str:
        """
        Create a visual indicator showing smart money consensus.
        
        Args:
            yes_pct: Percentage betting YES
            no_pct: Percentage betting NO
            volume: Total volume
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Create horizontal stacked bar
        ax.barh(0, yes_pct, color=COLORS['danger'], height=0.6, label=f'YES: {yes_pct:.1f}%')
        ax.barh(0, no_pct, left=yes_pct, color=COLORS['success'], height=0.6, label=f'NO: {no_pct:.1f}%')
        
        # Add center line
        ax.axvline(x=50, color=COLORS['dark'], linestyle='--', linewidth=2, alpha=0.5)
        
        # Labels
        if yes_pct > 10:
            ax.text(yes_pct/2, 0, f'YES\n{yes_pct:.1f}%', ha='center', va='center',
                   fontsize=14, fontweight='bold', color='white')
        if no_pct > 10:
            ax.text(yes_pct + no_pct/2, 0, f'NO\n{no_pct:.1f}%', ha='center', va='center',
                   fontsize=14, fontweight='bold', color='white')
        
        # Arrow indicating consensus
        consensus = "NO STRIKE" if no_pct > yes_pct else "STRIKE LIKELY"
        consensus_color = COLORS['success'] if no_pct > yes_pct else COLORS['danger']
        
        ax.text(50, -0.7, f'⬇️ Smart Money Consensus: {consensus}', ha='center', va='top',
               fontsize=12, fontweight='bold', color=consensus_color)
        ax.text(50, 0.7, f'Total Volume: {volume}', ha='center', va='bottom',
               fontsize=10, fontweight='bold', color=COLORS['dark'])
        
        ax.set_xlim(0, 100)
        ax.set_ylim(-1, 1)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_yticks([])
        ax.set_xlabel('Percentage (%)', fontsize=11)
        
        plt.tight_layout()
        return self._save_chart(fig, "smart_money")
    
    # =========================================================================
    # 7. KELLY CRITERION / BETTING STRATEGY CHARTS
    # =========================================================================
    
    def create_kelly_allocation(self, kelly_fractions: Dict[str, float],
                                title: str = "Kelly Criterion Allocation") -> str:
        """
        Create a chart showing Kelly criterion recommended allocations.
        
        Args:
            kelly_fractions: Dict of {market: kelly_fraction}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        markets = list(kelly_fractions.keys())
        fractions = [min(f, 100) for f in kelly_fractions.values()]  # Cap at 100%
        
        # Color gradient
        colors = [PROB_COLORS[min(int(f / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)] for f in fractions]
        
        bars = ax.bar(markets, fractions, color=colors, edgecolor='white', linewidth=2)
        
        for bar, frac in zip(bars, fractions):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{frac:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_ylabel('Recommended Allocation (%)', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.tick_params(axis='x', rotation=45)
        
        # Reference lines
        ax.axhline(y=25, color=COLORS['warning'], linestyle='--', alpha=0.5, label='Conservative (25%)')
        ax.axhline(y=50, color=COLORS['info'], linestyle='--', alpha=0.5, label='Moderate (50%)')
        ax.legend(loc='upper right', fontsize=9)
        
        plt.tight_layout()
        return self._save_chart(fig, "kelly_allocation")
    
    def create_ev_comparison(self, ev_data: Dict[str, Dict[str, float]],
                             title: str = "Expected Value by Market") -> str:
        """
        Create a chart comparing expected values for YES vs NO bets.
        
        Args:
            ev_data: Dict of {market: {yes_ev: float, no_ev: float}}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        markets = list(ev_data.keys())
        yes_evs = [ev_data[m].get('yes_ev', 0) for m in markets]
        no_evs = [ev_data[m].get('no_ev', 0) for m in markets]
        
        x = np.arange(len(markets))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, yes_evs, width, label='YES EV', color=COLORS['danger'], edgecolor='white')
        bars2 = ax.bar(x + width/2, no_evs, width, label='NO EV', color=COLORS['success'], edgecolor='white')
        
        # Add value labels
        for bars, evs in [(bars1, yes_evs), (bars2, no_evs)]:
            for bar, ev in zip(bars, evs):
                y_pos = bar.get_height() + 0.01 if ev >= 0 else bar.get_height() - 0.03
                ax.text(bar.get_x() + bar.get_width()/2, y_pos,
                       f'{ev:.2f}', ha='center', va='bottom' if ev >= 0 else 'top',
                       fontsize=9, fontweight='bold')
        
        ax.axhline(y=0, color=COLORS['dark'], linestyle='-', linewidth=1)
        ax.set_ylabel('Expected Value ($)', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(markets, rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=10)
        
        plt.tight_layout()
        return self._save_chart(fig, "ev_comparison")
    
    # =========================================================================
    # 8. NEWS ANALYSIS CHARTS
    # =========================================================================
    
    def create_news_sentiment_chart(self, positive: int, negative: int, neutral: int,
                                    title: str = "News Sentiment Analysis") -> str:
        """
        Create a chart showing news sentiment breakdown.
        
        Args:
            positive: Count of positive articles
            negative: Count of negative articles  
            neutral: Count of neutral articles
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        return self.create_sentiment_breakdown(
            {'Positive': positive, 'Negative': negative, 'Neutral': neutral},
            title
        )
    
    def create_news_sources_chart(self, sources: Dict[str, int],
                                   title: str = "News by Source") -> str:
        """
        Create a bar chart showing article count by news source.
        
        Args:
            sources: Dict of {source_name: article_count}
            title: Chart title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Sort by count
        sorted_sources = dict(sorted(sources.items(), key=lambda x: x[1], reverse=True))
        
        names = list(sorted_sources.keys())[:15]  # Top 15
        counts = list(sorted_sources.values())[:15]
        
        colors = plt.cm.viridis(np.linspace(0, 0.8, len(names)))
        
        bars = ax.barh(names, counts, color=colors, edgecolor='white', linewidth=1)
        
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + max(counts)*0.01, bar.get_y() + bar.get_height()/2,
                   f'{count}', va='center', ha='left', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Number of Articles', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.invert_yaxis()
        
        plt.tight_layout()
        return self._save_chart(fig, "news_sources")
    
    # =========================================================================
    # 9. SUMMARY DASHBOARD
    # =========================================================================
    
    def create_summary_dashboard(self, data: Dict[str, Any],
                                  title: str = "Analysis Summary Dashboard") -> str:
        """
        Create a comprehensive dashboard combining multiple visualizations.
        
        Args:
            data: Dictionary containing all analysis data
            title: Dashboard title
        
        Returns:
            Path to saved chart
        """
        fig = plt.figure(figsize=(16, 12))
        
        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Main probability gauge (top center, larger)
        ax1 = fig.add_subplot(gs[0, 1])
        prob = data.get('main_probability', 45)
        prob = float(prob) if isinstance(prob, (int, float)) else 45.0
        prob = max(0.0, min(100.0, prob))
        ax1.pie([max(0.0, 100-prob), prob], colors=[COLORS['success'], COLORS['danger']],
                startangle=90, wedgeprops=dict(width=0.3))
        ax1.text(0, 0, f'{prob:.0f}%', ha='center', va='center', fontsize=24, fontweight='bold')
        ax1.set_title('Strike Probability', fontsize=12, fontweight='bold')
        
        # 2. Source comparison (top left)
        ax2 = fig.add_subplot(gs[0, 0])
        sources = data.get('source_probabilities', {'Reddit': 40, 'Polymarket': 45, 'News': 42})
        ax2.barh(list(sources.keys()), list(sources.values()), color=COLORS['primary'])
        ax2.set_xlim(0, 100)
        ax2.set_title('By Source', fontsize=11, fontweight='bold')
        
        # 3. Sentiment (top right)
        ax3 = fig.add_subplot(gs[0, 2])
        sentiment = data.get('sentiment', {'Positive': 30, 'Negative': 45, 'Neutral': 25})
        sent_vals = [float(v) if isinstance(v, (int, float)) else 0.0 for v in sentiment.values()]
        sent_sum = sum(sent_vals)
        if sent_sum > 0:
            ax3.pie(
                sent_vals,
                labels=list(sentiment.keys()),
                colors=[COLORS['success'], COLORS['danger'], COLORS['warning']],
                autopct='%1.0f%%'
            )
        else:
            ax3.text(0.5, 0.5, "No sentiment data", ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Sentiment', fontsize=11, fontweight='bold')
        
        # 4. Timeline (middle, full width)
        ax4 = fig.add_subplot(gs[1, :])
        deadlines = data.get('deadlines', [
            {'label': 'Feb', 'prob': 45},
            {'label': 'Mar', 'prob': 50},
            {'label': 'Jun', 'prob': 55},
            {'label': 'Dec', 'prob': 60}
        ])
        x = range(len(deadlines))
        probs = [float(d.get('prob', d.get('probability', 0))) for d in deadlines]
        labels = [d['label'] for d in deadlines]
        ax4.plot(x, probs, 'o-', color=COLORS['primary'], linewidth=3, markersize=15)
        ax4.set_xticks(x)
        ax4.set_xticklabels(labels)
        ax4.set_ylabel('Probability (%)')
        ax4.set_title('Probability by Deadline', fontsize=11, fontweight='bold')
        ax4.set_ylim(0, 100)
        ax4.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        
        # 5. Portfolio (bottom left)
        ax5 = fig.add_subplot(gs[2, 0])
        portfolio = data.get('portfolio', {'Gold': 30, 'BTC': 20, 'Cash': 50})
        port_vals = [float(v) if isinstance(v, (int, float)) else 0.0 for v in portfolio.values()]
        port_sum = sum(port_vals)
        if port_sum > 0:
            ax5.pie(list(portfolio.values()), labels=list(portfolio.keys()),
                    colors=[COLORS['gold'], COLORS['bitcoin'], COLORS['light']],
                    autopct='%1.0f%%')
        else:
            ax5.text(0.5, 0.5, "No portfolio data", ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title('Portfolio', fontsize=11, fontweight='bold')
        
        # 6. Key metrics (bottom center)
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.axis('off')
        metrics = data.get('key_metrics', {
            'Total Users': '72,385',
            'PM Volume': '$159.9M',
            'Gold': '$2,850',
            'BTC': '$97,500'
        })
        y = 0.9
        for metric, value in metrics.items():
            ax6.text(0.1, y, f'{metric}:', fontsize=11, fontweight='bold', transform=ax6.transAxes)
            ax6.text(0.9, y, value, fontsize=11, ha='right', transform=ax6.transAxes)
            y -= 0.15
        ax6.set_title('Key Metrics', fontsize=11, fontweight='bold')
        
        # 7. Smart money (bottom right)
        ax7 = fig.add_subplot(gs[2, 2])
        smart = data.get('smart_money', {'YES': 35, 'NO': 65})
        yes_pct = float(smart.get('YES', 35)) if isinstance(smart, dict) else 35.0
        no_pct = float(smart.get('NO', 65)) if isinstance(smart, dict) else 65.0
        if yes_pct + no_pct <= 0:
            yes_pct, no_pct = 50.0, 50.0
        # Normalize to 100
        tot = yes_pct + no_pct
        yes_pct = yes_pct / tot * 100.0
        no_pct = 100.0 - yes_pct
        ax7.barh(['Position'], [yes_pct], color=COLORS['danger'], label='YES')
        ax7.barh(['Position'], [no_pct], left=[yes_pct], color=COLORS['success'], label='NO')
        ax7.set_xlim(0, 100)
        ax7.legend(loc='upper right')
        ax7.set_title('Smart Money', fontsize=11, fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        return self._save_chart(fig, "summary_dashboard")

    # =========================================================================
    # 10. REDDIT/SCENARIO/TIMELINE DIAGNOSTIC CHARTS
    # =========================================================================

    def create_opinionated_fraction_chart(self, opinionated: int, neutral: int,
                                          title: str = "Opinionated vs Neutral Users") -> str:
        """Donut chart: opinionated users vs neutral/unclear."""
        fig, ax = plt.subplots(figsize=(7, 7))
        o = max(0, int(opinionated or 0))
        n = max(0, int(neutral or 0))
        total = o + n
        if total <= 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            return self._save_chart(fig, "opinionated_fraction")

        sizes = [o, n]
        labels = [f"Opinionated ({o:,})", f"Neutral/Unclear ({n:,})"]
        colors = [COLORS["info"], COLORS["light"]]
        ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90,
               wedgeprops=dict(width=0.45, edgecolor="white"))
        ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
        return self._save_chart(fig, "opinionated_fraction")

    def create_stacked_breakdown_chart(self, rows: List[Tuple[str, int, int, int]],
                                       title: str = "Breakdown (Attack / No Attack / Neutral)",
                                       xlabel: str = "Count",
                                       max_rows: int = 15,
                                       filename: str = "stacked_breakdown") -> str:
        """
        Generic stacked horizontal bar chart.
        rows: list of (label, attack, no_attack, neutral)
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        if not rows:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            return self._save_chart(fig, filename)

        rows = rows[:max_rows]
        labels = [sanitize_text_for_chart(r[0]) for r in rows]
        attack = np.array([max(0, int(r[1] or 0)) for r in rows], dtype=float)
        no_attack = np.array([max(0, int(r[2] or 0)) for r in rows], dtype=float)
        neutral = np.array([max(0, int(r[3] or 0)) for r in rows], dtype=float)

        ax.barh(labels, attack, color=COLORS["danger"], alpha=0.85, label="Attack")
        ax.barh(labels, no_attack, left=attack, color=COLORS["success"], alpha=0.85, label="No attack")
        ax.barh(labels, neutral, left=attack + no_attack, color=COLORS["warning"], alpha=0.45, label="Neutral")

        ax.set_xlabel(sanitize_text_for_chart(xlabel))
        ax.set_title(sanitize_text_for_chart(title), fontsize=13, fontweight="bold", pad=12)
        ax.invert_yaxis()
        ax.legend(loc="lower right")
        ax.grid(True, axis="x", alpha=0.25)
        plt.tight_layout()
        return self._save_chart(fig, filename)

    def create_subreddit_activity_chart(self, subreddit_stats: Dict[str, Dict[str, Any]],
                                        title: str = "Top Subreddits (Comment Volume & Stance)",
                                        top_n: int = 15) -> str:
        """Stacked bar chart for top subreddits by comment volume."""
        rows: List[Tuple[str, int, int, int]] = []
        for sub, v in (subreddit_stats or {}).items():
            if not isinstance(v, dict):
                continue
            cnt = int(v.get("count", 0) or 0)
            atk = int(v.get("attack", 0) or 0)
            no = int(v.get("no_attack", 0) or 0)
            neu = int(v.get("neutral", max(0, cnt - atk - no)) or 0)
            rows.append((f"r/{sub}", atk, no, neu))
        # Sort by total
        rows = sorted(rows, key=lambda x: (x[1] + x[2] + x[3]), reverse=True)[:top_n]
        return self.create_stacked_breakdown_chart(
            rows,
            title=title,
            xlabel="Comments",
            max_rows=top_n,
            filename="subreddit_activity"
        )

    def create_scenario_stats_chart(self, scenario_stats: Dict[str, Dict[str, Any]],
                                    title: str = "Scenario Mentions (Attack / No Attack / Neutral)",
                                    top_n: int = 12) -> str:
        """Stacked chart for scenario mention buckets."""
        rows: List[Tuple[str, int, int, int]] = []
        for name, v in (scenario_stats or {}).items():
            if not isinstance(v, dict):
                continue
            cnt = int(v.get("count", 0) or 0)
            atk = int(v.get("attack", 0) or 0)
            no = int(v.get("no_attack", 0) or 0)
            neu = int(v.get("neutral", max(0, cnt - atk - no)) or 0)
            label = str(name).replace("_", " ").title()
            rows.append((label, atk, no, neu))
        rows = sorted(rows, key=lambda x: (x[1] + x[2] + x[3]), reverse=True)[:top_n]
        return self.create_stacked_breakdown_chart(
            rows,
            title=title,
            xlabel="Mentions",
            max_rows=top_n,
            filename="scenario_stats"
        )

    def create_timeline_stats_chart(self, timeline_stats: Dict[str, Dict[str, Any]],
                                    title: str = "Timeline Mentions (Attack / No Attack / Neutral)") -> str:
        """Stacked chart for timeline mention buckets."""
        order = [
            "tomorrow", "today", "this_week", "next_week", "this_month", "next_month",
            "this_quarter", "this_year", "long_term", "conditional"
        ]
        rows: List[Tuple[str, int, int, int]] = []
        for key in order:
            v = (timeline_stats or {}).get(key)
            if not isinstance(v, dict):
                continue
            cnt = int(v.get("count", 0) or 0)
            atk = int(v.get("attack", 0) or 0)
            no = int(v.get("no_attack", 0) or 0)
            neu = int(v.get("neutral", max(0, cnt - atk - no)) or 0)
            label = key.replace("_", " ").title()
            rows.append((label, atk, no, neu))
        # if any extra keys not in order
        if timeline_stats:
            for key, v in timeline_stats.items():
                if key in order or not isinstance(v, dict):
                    continue
                cnt = int(v.get("count", 0) or 0)
                atk = int(v.get("attack", 0) or 0)
                no = int(v.get("no_attack", 0) or 0)
                neu = int(v.get("neutral", max(0, cnt - atk - no)) or 0)
                label = str(key).replace("_", " ").title()
                rows.append((label, atk, no, neu))
        return self.create_stacked_breakdown_chart(
            rows,
            title=title,
            xlabel="Mentions",
            max_rows=15,
            filename="timeline_stats"
        )

    def create_extended_predictions_chart(self, ext: Dict[str, Any],
                                          title: str = "Extended Predictions (Mention Counts)") -> str:
        """Bar chart for selected extended prediction keys (counts)."""
        fig, ax = plt.subplots(figsize=(12, 6))
        if not isinstance(ext, dict) or not ext:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            return self._save_chart(fig, "extended_predictions")

        keys = [
            ("regime_falls", "Regime falls"),
            ("regime_survives", "Regime survives"),
            ("deal_likely", "Deal likely"),
            ("deal_unlikely", "Deal unlikely"),
            ("major_war", "Major war"),
            ("limited_conflict", "Limited conflict"),
            ("pahlavi_returns", "Pahlavi returns"),
            ("pahlavi_unlikely", "Pahlavi unlikely"),
        ]
        labels = []
        vals = []
        for k, lab in keys:
            try:
                v = int(ext.get(k, 0) or 0)
            except Exception:
                v = 0
            labels.append(lab)
            vals.append(v)

        ax.bar(labels, vals, color=COLORS["secondary"], alpha=0.85)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Count (mentions)")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(True, axis="y", alpha=0.25)
        plt.tight_layout()
        return self._save_chart(fig, "extended_predictions")

    # =========================================================================
    # 10. POLYMARKET TERM STRUCTURE / VOLUME / HAZARD
    # =========================================================================

    def create_polymarket_term_structure(self, points: List[Dict[str, Any]],
                                         title: str = "Polymarket Term Structure (Cumulative)") -> str:
        """
        Line chart of cumulative probability by deadline date.

        points: list of dicts with keys: date (YYYY-MM-DD), probability (0-100), volume_num (float, optional)
        """
        fig, ax = plt.subplots(figsize=(11, 5))

        def parse_date(s: str) -> Optional[_dt]:
            try:
                return _dt.strptime(str(s)[:10], "%Y-%m-%d")
            except Exception:
                return None

        rows = []
        for p in points or []:
            d = parse_date(p.get("date", ""))
            prob = p.get("probability", 0)
            try:
                prob_f = float(prob)
            except Exception:
                prob_f = 0.0
            vol = p.get("volume_num", 0.0)
            try:
                vol_f = float(vol)
            except Exception:
                vol_f = 0.0
            if d is not None:
                rows.append((d, max(0.0, min(100.0, prob_f)), max(0.0, vol_f)))

        rows.sort(key=lambda x: x[0])
        if not rows:
            ax.text(0.5, 0.5, "No Polymarket deadline points", ha="center", va="center", transform=ax.transAxes)
            return self._save_chart(fig, "pm_term_structure")

        dates = [r[0] for r in rows]
        probs = [r[1] for r in rows]
        vols = [r[2] for r in rows]

        ax.plot(dates, probs, marker="o", linewidth=2.5, color=COLORS["polymarket"])
        # Marker size by volume (log-ish)
        sizes = [80 + (np.log10(v + 1) * 35) for v in vols]
        ax.scatter(dates, probs, s=sizes, color=COLORS["polymarket"], alpha=0.35)

        ax.set_ylim(0, 100)
        ax.set_ylabel("Cumulative Probability (%)")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate(rotation=30, ha="right")

        return self._save_chart(fig, "pm_term_structure")

    def create_polymarket_volume_bars(self, points: List[Dict[str, Any]],
                                      title: str = "Polymarket Volume by Deadline") -> str:
        """Bar chart of volume (USD) by deadline date."""
        fig, ax = plt.subplots(figsize=(11, 5))

        def parse_date(s: str) -> Optional[_dt]:
            try:
                return _dt.strptime(str(s)[:10], "%Y-%m-%d")
            except Exception:
                return None

        rows = []
        for p in points or []:
            d = parse_date(p.get("date", ""))
            vol = p.get("volume_num", 0.0)
            try:
                vol_f = float(vol)
            except Exception:
                vol_f = 0.0
            if d is not None:
                rows.append((d, max(0.0, vol_f)))

        rows.sort(key=lambda x: x[0])
        if not rows:
            ax.text(0.5, 0.5, "No volume data", ha="center", va="center", transform=ax.transAxes)
            return self._save_chart(fig, "pm_volume")

        dates = [r[0] for r in rows]
        vols = [r[1] for r in rows]
        ax.bar(dates, vols, color=COLORS["polymarket"], alpha=0.7)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Volume (USD)")
        ax.grid(True, axis="y", alpha=0.25)
        fig.autofmt_xdate(rotation=30, ha="right")

        return self._save_chart(fig, "pm_volume")

    def create_incremental_probability(self, points: List[Dict[str, Any]],
                                       title: str = "Incremental (Non-cumulative) Probability by Window") -> str:
        """
        Convert cumulative deadline probabilities into incremental windows and plot bars.
        """
        fig, ax = plt.subplots(figsize=(11, 5))

        def parse_date(s: str) -> Optional[_dt]:
            try:
                return _dt.strptime(str(s)[:10], "%Y-%m-%d")
            except Exception:
                return None

        rows = []
        for p in points or []:
            d = parse_date(p.get("date", ""))
            prob = p.get("probability", 0)
            try:
                prob_f = float(prob)
            except Exception:
                prob_f = 0.0
            if d is not None:
                rows.append((d, max(0.0, min(100.0, prob_f))))
        rows.sort(key=lambda x: x[0])

        if len(rows) < 2:
            ax.text(0.5, 0.5, "Not enough points", ha="center", va="center", transform=ax.transAxes)
            return self._save_chart(fig, "pm_incremental")

        inc = []
        prev = 0.0
        for d, p in rows:
            inc_p = max(0.0, p - prev)
            inc.append((d, inc_p))
            prev = p

        dates = [d for d, _ in inc]
        vals = [v for _, v in inc]
        ax.bar(dates, vals, color=COLORS["info"], alpha=0.8)
        ax.set_ylim(0, max(5.0, max(vals) * 1.25))
        ax.set_ylabel("Incremental Probability (%)")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.grid(True, axis="y", alpha=0.25)
        fig.autofmt_xdate(rotation=30, ha="right")

        return self._save_chart(fig, "pm_incremental")

    # =========================================================================
    # 11. CONDITIONAL PROBABILITY GRAPHS
    # =========================================================================

    def create_scenario_tree(
        self,
        root_event: str,
        branches: List[Dict[str, Any]],
        title: str = "Scenario Decision Tree",
        title_fa: str = "Scenario Decision Tree"
    ) -> str:
        """
        Create a scenario decision tree showing conditional probabilities.
        
        Args:
            root_event: The starting event/condition
            branches: List of dicts with keys:
                - name: Branch name
                - probability: P(branch)
                - children: Optional list of sub-branches with same structure
            title: English title
            title_fa: Persian title (for bilingual reports)
        
        Example:
            branches = [
                {
                    "name": "Diplomatic Solution",
                    "probability": 35,
                    "children": [
                        {"name": "Full Deal", "probability": 40},
                        {"name": "Partial Deal", "probability": 60}
                    ]
                },
                {
                    "name": "Military Action",
                    "probability": 45,
                    "children": [
                        {"name": "Limited Strike", "probability": 70},
                        {"name": "Full Invasion", "probability": 30}
                    ]
                }
            ]
        
        Returns:
            Path to saved chart
        """
        n_branches = max(1, len(branches or []))
        fig_w = max(20, 7 + n_branches * 3.5)
        fig_h = max(12, 5 + n_branches * 2.5)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_xlim(-0.5, 4.5)
        ax.set_ylim(-0.5, 1.5)
        ax.axis('off')
        
        # Root node
        root_x, root_y = 0, 0.5
        root_box = dict(boxstyle='round,pad=0.4', facecolor=COLORS['primary'], edgecolor='white', linewidth=2)
        ax.text(root_x, root_y, wrap_text_for_chart(root_event, width=16), ha='center', va='center', fontsize=12, fontweight='bold',
                color='white', bbox=root_box, zorder=10)
        
        # First level branches
        if n_branches == 0:
            ax.text(2, 0.5, "No branches defined", ha='center', va='center', fontsize=12)
            return self._save_chart(fig, "scenario_tree")
        
        branch_y_positions = np.linspace(0.1, 0.9, n_branches)
        level1_x = 1.5
        
        for i, branch in enumerate(branches):
            branch_y = branch_y_positions[i]
            prob = branch.get('probability', 50)
            name = branch.get('name', f'Branch {i+1}')
            children = branch.get('children', [])
            
            # Color based on probability
            color_idx = min(int(prob / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)
            branch_color = PROB_COLORS[color_idx]
            
            # Draw edge from root to branch
            ax.annotate(
                '',
                xy=(level1_x - 0.3, branch_y),
                xytext=(root_x + 0.35, root_y),
                arrowprops=dict(arrowstyle='->', color=branch_color, lw=2.5, 
                               connectionstyle="arc3,rad=0.1")
            )
            
            # Edge label (probability)
            mid_x = (root_x + level1_x) / 2 + 0.1
            mid_y = (root_y + branch_y) / 2
            ax.text(mid_x, mid_y, f'{prob}%', fontsize=9, fontweight='bold',
                   color=branch_color, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=branch_color, alpha=0.9))
            
            # Branch node
            branch_box = dict(boxstyle='round,pad=0.3', facecolor=branch_color, edgecolor='white', linewidth=1.5)
            ax.text(level1_x, branch_y, wrap_text_for_chart(name, width=16), ha='center', va='center', fontsize=11, fontweight='bold',
                   color='white', bbox=branch_box, zorder=10)
            
            # Second level (children)
            if children:
                n_children = len(children)
                if n_children == 1:
                    child_y_positions = [branch_y]
                else:
                    child_spread = min(0.15, 0.6 / n_branches)
                    child_y_positions = np.linspace(branch_y - child_spread, branch_y + child_spread, n_children)
                
                level2_x = 2.8
                
                for j, child in enumerate(children):
                    child_y = child_y_positions[j]
                    child_prob = child.get('probability', 50)
                    child_name = child.get('name', f'Sub {j+1}')
                    
                    # Conditional probability: P(child | branch)
                    joint_prob = (prob / 100) * (child_prob / 100) * 100
                    
                    child_color_idx = min(int(child_prob / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)
                    child_color = PROB_COLORS[child_color_idx]
                    
                    # Edge
                    ax.annotate(
                        '',
                        xy=(level2_x - 0.35, child_y),
                        xytext=(level1_x + 0.35, branch_y),
                        arrowprops=dict(arrowstyle='->', color=child_color, lw=2,
                                       connectionstyle="arc3,rad=0.05")
                    )
                    
                    # Edge label
                    edge_mid_x = (level1_x + level2_x) / 2 + 0.1
                    edge_mid_y = (branch_y + child_y) / 2
                    ax.text(edge_mid_x, edge_mid_y, f'{child_prob}%', fontsize=8, fontweight='bold',
                           color=child_color, ha='center', va='center',
                           bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor=child_color, alpha=0.85))
                    
                    # Child node
                    child_box = dict(boxstyle='round,pad=0.25', facecolor=child_color, edgecolor='white', linewidth=1)
                    ax.text(level2_x, child_y, f'{wrap_text_for_chart(child_name, width=16)}\n[Joint: {joint_prob:.1f}%]', 
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color='white', bbox=child_box, zorder=10)
                    
                    # Third level grandchildren (if any)
                    grandchildren = child.get('children', [])
                    if grandchildren:
                        level3_x = 4.0
                        n_gc = len(grandchildren)
                        gc_spread = min(0.08, 0.3 / n_branches)
                        gc_y_positions = np.linspace(child_y - gc_spread, child_y + gc_spread, n_gc) if n_gc > 1 else [child_y]
                        
                        for k, gc in enumerate(grandchildren):
                            gc_y = gc_y_positions[k]
                            gc_prob = gc.get('probability', 50)
                            gc_name = gc.get('name', f'Outcome {k+1}')
                            
                            # Joint probability: P(gc | child, branch) * P(child | branch) * P(branch)
                            gc_joint = joint_prob * (gc_prob / 100)
                            
                            gc_color_idx = min(int(gc_prob / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)
                            gc_color = PROB_COLORS[gc_color_idx]
                            
                            ax.annotate(
                                '',
                                xy=(level3_x - 0.3, gc_y),
                                xytext=(level2_x + 0.35, child_y),
                                arrowprops=dict(arrowstyle='->', color=gc_color, lw=1.5,
                                               connectionstyle="arc3,rad=0.02")
                            )
                            
                            gc_box = dict(boxstyle='round,pad=0.2', facecolor=gc_color, edgecolor='white', linewidth=1)
                            ax.text(level3_x, gc_y, f'{wrap_text_for_chart(gc_name, width=16)}\n[{gc_joint:.1f}%]',
                                   ha='center', va='center', fontsize=9, fontweight='bold',
                                   color='white', bbox=gc_box, zorder=10)
        
        # Title (bilingual) - render Persian text properly
        fig.suptitle(f'{sanitize_text_for_chart(title)}', fontsize=14, fontweight='bold', y=0.98)
        
        # Legend
        ax.text(0.02, 0.02, 'Numbers on edges = P(event | parent)\nNumbers in [brackets] = Joint probability from root',
               transform=ax.transAxes, fontsize=8, va='bottom', ha='left',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        plt.tight_layout()
        return self._save_chart(fig, "scenario_tree")

    def create_conditional_flow_chart(
        self,
        conditions: List[Dict[str, Any]],
        title: str = "Conditional Probability Flow",
        title_fa: str = "Conditional Probability Flow"
    ) -> str:
        """
        Create a flowchart showing "if X then Y" relationships with probabilities.
        
        Args:
            conditions: List of dicts with keys:
                - condition: The IF condition (e.g., "Negotiations Fail")
                - outcomes: List of {outcome, probability, impact}
            title: English title
            title_fa: Persian title
        
        Example:
            conditions = [
                {
                    "condition": "Negotiations Fail",
                    "condition_prob": 40,
                    "outcomes": [
                        {"outcome": "Limited Strike", "probability": 60, "impact": "high"},
                        {"outcome": "Sanctions Only", "probability": 40, "impact": "medium"}
                    ]
                }
            ]
        
        Returns:
            Path to saved chart
        """
        n_conditions = len(conditions)
        fig_height = max(7, 2.8 * n_conditions)
        fig, ax = plt.subplots(figsize=(16, fig_height))
        ax.set_xlim(-0.5, 4)
        ax.set_ylim(-0.2, n_conditions + 0.2)
        ax.axis('off')
        
        impact_colors = {
            'high': COLORS['danger'],
            'medium': COLORS['warning'],
            'low': COLORS['success'],
            'critical': '#8B0000',  # Dark red
            'uncertain': COLORS['info']
        }
        
        for i, cond in enumerate(conditions):
            y_base = n_conditions - i - 0.5
            
            condition_text = wrap_text_for_chart(cond.get('condition', f'Condition {i+1}'), width=16)
            condition_prob = cond.get('condition_prob', 50)
            outcomes = cond.get('outcomes', [])
            
            # Condition box (IF)
            cond_color = PROB_COLORS[min(int(condition_prob / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)]
            cond_box = dict(boxstyle='round,pad=0.4', facecolor=cond_color, edgecolor='white', linewidth=2)
            ax.text(0.3, y_base, f'IF:\n{condition_text}\n({condition_prob}%)', 
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color='white', bbox=cond_box, zorder=10)
            
            # Arrow to outcomes
            ax.annotate('', xy=(1.2, y_base), xytext=(0.7, y_base),
                       arrowprops=dict(arrowstyle='->', color=COLORS['dark'], lw=2))
            ax.text(0.95, y_base + 0.15, 'THEN', fontsize=9, fontweight='bold', ha='center')
            
            # Outcomes
            n_outcomes = len(outcomes)
            if n_outcomes > 0:
                outcome_y_positions = np.linspace(y_base - 0.25, y_base + 0.25, n_outcomes) if n_outcomes > 1 else [y_base]
                
                for j, outcome in enumerate(outcomes):
                    out_y = outcome_y_positions[j]
                    out_text = wrap_text_for_chart(outcome.get('outcome', f'Outcome {j+1}'), width=16)
                    out_prob = outcome.get('probability', 50)
                    out_impact = outcome.get('impact', 'medium').lower()
                    
                    # Joint probability
                    joint = (condition_prob / 100) * (out_prob / 100) * 100
                    
                    out_color = impact_colors.get(out_impact, COLORS['info'])
                    
                    # Draw arrow from IF to outcome
                    ax.annotate('', xy=(1.8, out_y), xytext=(1.3, y_base),
                               arrowprops=dict(arrowstyle='->', color=out_color, lw=1.5,
                                              connectionstyle='arc3,rad=0.1'))
                    
                    # Probability label on edge
                    ax.text(1.55, (y_base + out_y) / 2, f'{out_prob}%', fontsize=8,
                           color=out_color, fontweight='bold', ha='center')
                    
                    # Outcome box
                    out_box = dict(boxstyle='round,pad=0.3', facecolor=out_color, edgecolor='white', linewidth=1.5)
                    ax.text(2.5, out_y, f'{out_text}\nP={joint:.1f}%\nImpact: {out_impact.upper()}',
                           ha='center', va='center', fontsize=9, fontweight='bold',
                           color='white', bbox=out_box, zorder=10)
        
        # Title - render Persian text properly
        fig.suptitle(f'{sanitize_text_for_chart(title)}', fontsize=13, fontweight='bold', y=0.98)
        
        # Legend for impact colors
        legend_y = 0.05
        for impact, color in [('Critical', '#8B0000'), ('High', COLORS['danger']), 
                              ('Medium', COLORS['warning']), ('Low', COLORS['success'])]:
            ax.add_patch(mpatches.Rectangle((3.2, legend_y), 0.15, 0.08, facecolor=color, edgecolor='white'))
            ax.text(3.4, legend_y + 0.04, impact, fontsize=8, va='center')
            legend_y += 0.12
        
        plt.tight_layout()
        return self._save_chart(fig, "conditional_flow")

    def create_bayesian_network_chart(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Tuple[str, str, float]],
        title: str = "Bayesian Belief Network",
        title_fa: str = "Bayesian Belief Network"
    ) -> str:
        """
        Create a Bayesian network visualization showing probabilistic dependencies.
        
        Args:
            nodes: List of dicts with keys:
                - id: Unique node ID
                - label: Display label
                - probability: Prior/marginal probability
                - category: Category for coloring (optional)
            edges: List of tuples (from_id, to_id, conditional_prob)
            title: English title
            title_fa: Persian title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.axis('off')
        
        # Build node position layout (simple layered layout)
        node_dict = {n['id']: n for n in nodes}
        
        # Find nodes with no incoming edges (roots)
        incoming = {n['id']: [] for n in nodes}
        outgoing = {n['id']: [] for n in nodes}
        for from_id, to_id, prob in edges:
            if to_id in incoming:
                incoming[to_id].append(from_id)
            if from_id in outgoing:
                outgoing[from_id].append(to_id)
        
        # Layer assignment
        layers = {}
        remaining = set(node_dict.keys())
        current_layer = 0
        
        while remaining:
            # Nodes whose parents are all assigned
            layer_nodes = [n for n in remaining 
                          if all(p not in remaining for p in incoming.get(n, []))]
            if not layer_nodes:
                # Cycle or isolated - assign remaining to current layer
                layer_nodes = list(remaining)
            
            for n in layer_nodes:
                layers[n] = current_layer
                remaining.discard(n)
            current_layer += 1
        
        max_layer = max(layers.values()) if layers else 0
        
        # Count nodes per layer for y positioning
        layer_counts = {}
        for node_id, layer in layers.items():
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
        layer_current = {l: 0 for l in range(max_layer + 1)}
        
        # Assign positions
        positions = {}
        for node_id, layer in sorted(layers.items(), key=lambda x: (x[1], x[0])):
            count = layer_counts[layer]
            idx = layer_current[layer]
            layer_current[layer] += 1
            
            x = layer / max(max_layer, 1)
            y = (idx + 0.5) / max(count, 1)
            positions[node_id] = (x * 3 + 0.5, y * 0.8 + 0.1)
        
        ax.set_xlim(0, 4)
        ax.set_ylim(0, 1)
        
        # Category colors
        category_colors = {
            'trigger': COLORS['danger'],
            'escalation': COLORS['warning'],
            'outcome': COLORS['success'],
            'diplomatic': COLORS['info'],
            'military': COLORS['danger'],
            'economic': COLORS['gold'],
            'default': COLORS['primary']
        }
        
        # Draw edges first (behind nodes)
        for from_id, to_id, prob in edges:
            if from_id in positions and to_id in positions:
                x1, y1 = positions[from_id]
                x2, y2 = positions[to_id]
                
                prob_color_idx = min(int(prob / 100 * len(PROB_COLORS)), len(PROB_COLORS)-1)
                edge_color = PROB_COLORS[prob_color_idx]
                
                ax.annotate(
                    '',
                    xy=(x2 - 0.15, y2),
                    xytext=(x1 + 0.15, y1),
                    arrowprops=dict(arrowstyle='->', color=edge_color, lw=2,
                                   connectionstyle='arc3,rad=0.1', alpha=0.8)
                )
                
                # Edge probability label
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2 + 0.03
                ax.text(mid_x, mid_y, f'{prob:.0f}%', fontsize=8, fontweight='bold',
                       color=edge_color, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.85))
        
        # Draw nodes
        for node in nodes:
            node_id = node['id']
            if node_id not in positions:
                continue
            
            x, y = positions[node_id]
            label = node.get('label', node_id)
            prob = node.get('probability', 50)
            category = node.get('category', 'default').lower()
            
            node_color = category_colors.get(category, COLORS['primary'])
            
            node_box = dict(boxstyle='round,pad=0.4', facecolor=node_color, 
                           edgecolor='white', linewidth=2, alpha=0.95)
            ax.text(x, y, f'{label}\nP={prob:.0f}%', ha='center', va='center',
                   fontsize=9, fontweight='bold', color='white', bbox=node_box, zorder=10)
        
        # Title - render Persian text properly
        fig.suptitle(f'{sanitize_text_for_chart(title)}', fontsize=13, fontweight='bold', y=0.98)
        
        # Legend
        legend_items = []
        for cat, color in [('Trigger', COLORS['danger']), ('Diplomatic', COLORS['info']),
                           ('Military', COLORS['danger']), ('Economic', COLORS['gold']),
                           ('Outcome', COLORS['success'])]:
            legend_items.append(mpatches.Patch(facecolor=color, label=cat, edgecolor='white'))
        ax.legend(handles=legend_items, loc='lower right', fontsize=8, ncol=2)
        
        plt.tight_layout()
        return self._save_chart(fig, "bayesian_network")

    def create_event_dependency_graph(
        self,
        events: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
        title: str = "Event Dependency Network",
        title_fa: str = "Event Dependency Network"
    ) -> str:
        """
        Create a network graph showing how events depend on each other.
        
        Args:
            events: List of dicts with keys:
                - id: Unique event ID
                - name: Event name
                - probability: Current probability estimate
                - type: 'cause', 'effect', 'both'
            dependencies: List of dicts with keys:
                - cause: Cause event ID
                - effect: Effect event ID
                - strength: Dependency strength (0-1)
                - direction: 'positive' or 'negative' (increases or decreases prob)
            title: English title
            title_fa: Persian title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(20, 15))
        ax.axis('off')
        
        # Simple circular layout
        n = len(events)
        if n == 0:
            ax.text(0.5, 0.5, "No events to display", ha='center', va='center', transform=ax.transAxes)
            return self._save_chart(fig, "event_dependency")
        
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        radius = 0.35
        center_x, center_y = 0.5, 0.5
        
        event_dict = {e['id']: e for e in events}
        positions = {}
        
        for i, event in enumerate(events):
            x = center_x + radius * np.cos(angles[i])
            y = center_y + radius * np.sin(angles[i])
            positions[event['id']] = (x, y)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        type_colors = {
            'cause': COLORS['danger'],
            'effect': COLORS['success'],
            'both': COLORS['warning'],
            'external': COLORS['info'],
            'internal': COLORS['primary']
        }
        
        # Draw dependencies (edges)
        for dep in dependencies:
            cause_id = dep.get('cause')
            effect_id = dep.get('effect')
            strength = dep.get('strength', 0.5)
            direction = dep.get('direction', 'positive')
            
            if cause_id in positions and effect_id in positions:
                x1, y1 = positions[cause_id]
                x2, y2 = positions[effect_id]
                
                # Edge color based on direction
                if direction == 'positive':
                    edge_color = COLORS['danger']  # Increases probability
                else:
                    edge_color = COLORS['success']  # Decreases probability
                
                # Edge width based on strength
                edge_width = 1 + strength * 3
                
                ax.annotate(
                    '',
                    xy=(x2, y2),
                    xytext=(x1, y1),
                    arrowprops=dict(
                        arrowstyle='-|>',
                        color=edge_color,
                        lw=edge_width,
                        connectionstyle='arc3,rad=0.15',
                        alpha=0.7
                    )
                )
                
                # Strength label
                mid_x = (x1 + x2) / 2 + 0.02
                mid_y = (y1 + y2) / 2 + 0.02
                label = f'+{strength*100:.0f}%' if direction == 'positive' else f'-{strength*100:.0f}%'
                ax.text(mid_x, mid_y, label, fontsize=8, fontweight='bold',
                       color=edge_color, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.8))
        
        # Draw event nodes
        for event in events:
            event_id = event['id']
            if event_id not in positions:
                continue
            
            x, y = positions[event_id]
            name = event.get('name', event_id)
            prob = event.get('probability', 50)
            event_type = event.get('type', 'both').lower()
            
            node_color = type_colors.get(event_type, COLORS['primary'])
            
            # Node size based on probability
            node_size = 0.08 + (prob / 100) * 0.04
            
            circle = plt.Circle((x, y), node_size, facecolor=node_color, 
                               edgecolor='white', linewidth=2, zorder=10)
            ax.add_patch(circle)
            
            # Text inside node
            ax.text(x, y, f'{name}\n{prob:.0f}%', ha='center', va='center',
                   fontsize=8, fontweight='bold', color='white', zorder=11)
        
        # Title - render Persian text properly
        fig.suptitle(f'{sanitize_text_for_chart(title)}', fontsize=14, fontweight='bold', y=0.98)
        
        # Legend
        legend_elements = [
            mpatches.Patch(facecolor=COLORS['danger'], label='Cause/Trigger'),
            mpatches.Patch(facecolor=COLORS['success'], label='Effect/Outcome'),
            mpatches.Patch(facecolor=COLORS['warning'], label='Both'),
            plt.Line2D([0], [0], color=COLORS['danger'], lw=2, label='Increases P'),
            plt.Line2D([0], [0], color=COLORS['success'], lw=2, label='Decreases P')
        ]
        ax.legend(handles=legend_elements, loc='lower left', fontsize=8)
        
        # Note
        ax.text(0.98, 0.02, 'Arrow thickness = dependency strength\nArrow color = effect direction',
               ha='right', va='bottom', fontsize=7, style='italic',
               transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return self._save_chart(fig, "event_dependency")

    def create_scenario_comparison_matrix(
        self,
        scenarios: List[Dict[str, Any]],
        factors: List[str],
        title: str = "Scenario Comparison Matrix",
        title_fa: str = "Scenario Comparison Matrix"
    ) -> str:
        """
        Create a heatmap matrix comparing different scenarios across factors.
        
        Args:
            scenarios: List of dicts with keys:
                - name: Scenario name
                - factors: Dict of {factor_name: score (0-100)}
            factors: List of factor names to compare
            title: English title
            title_fa: Persian title
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if not scenarios or not factors:
            ax.text(0.5, 0.5, "No data to display", ha='center', va='center', transform=ax.transAxes)
            return self._save_chart(fig, "scenario_matrix")
        
        # Build matrix
        matrix = []
        scenario_names = []
        for s in scenarios:
            scenario_names.append(sanitize_text_for_chart(s.get('name', 'Unknown')))
            row = []
            s_factors = s.get('factors', {})
            for f in factors:
                row.append(s_factors.get(f, 50))
            matrix.append(row)
        
        matrix = np.array(matrix)
        
        # Create heatmap
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=100)
        
        # Axis labels
        ax.set_xticks(np.arange(len(factors)))
        ax.set_yticks(np.arange(len(scenario_names)))
        ax.set_xticklabels([sanitize_text_for_chart(f) for f in factors], rotation=45, ha='right', fontsize=10)
        ax.set_yticklabels(scenario_names, fontsize=10)
        
        # Add values in cells
        for i in range(len(scenario_names)):
            for j in range(len(factors)):
                val = matrix[i, j]
                text_color = 'white' if val > 60 or val < 40 else 'black'
                ax.text(j, i, f'{val:.0f}%', ha='center', va='center', 
                       fontsize=9, fontweight='bold', color=text_color)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label(sanitize_text_for_chart('Score / Probability'), fontsize=10)
        
        # Title - render Persian text properly
        fig.suptitle(f'{sanitize_text_for_chart(title)}', fontsize=13, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        return self._save_chart(fig, "scenario_matrix")

    def create_iran_political_tree(self) -> str:
        """
        Create a pre-defined scenario tree specific to US-Iran situation.
        
        This is a convenience method that generates a comprehensive
        decision tree for the Iran conflict analysis.
        
        Returns:
            Path to saved chart
        """
        branches = [
            {
                "name": "Diplomatic Path",
                "probability": 35,
                "children": [
                    {
                        "name": "Full Nuclear Deal",
                        "probability": 30,
                        "children": [
                            {"name": "Sanctions Lifted", "probability": 80},
                            {"name": "Partial Relief", "probability": 20}
                        ]
                    },
                    {
                        "name": "Freeze Agreement",
                        "probability": 50,
                        "children": [
                            {"name": "Status Quo", "probability": 70},
                            {"name": "Gradual Progress", "probability": 30}
                        ]
                    },
                    {
                        "name": "Talks Collapse",
                        "probability": 20,
                        "children": [
                            {"name": "Return to Tension", "probability": 90},
                            {"name": "New Initiative", "probability": 10}
                        ]
                    }
                ]
            },
            {
                "name": "Military Action",
                "probability": 40,
                "children": [
                    {
                        "name": "Limited Strike",
                        "probability": 65,
                        "children": [
                            {"name": "Nuclear Sites Only", "probability": 60},
                            {"name": "IRGC Targets", "probability": 40}
                        ]
                    },
                    {
                        "name": "Sustained Campaign",
                        "probability": 25,
                        "children": [
                            {"name": "Air Campaign", "probability": 80},
                            {"name": "Naval Blockade", "probability": 20}
                        ]
                    },
                    {
                        "name": "Regime Change Operation",
                        "probability": 10,
                        "children": [
                            {"name": "Support Opposition", "probability": 70},
                            {"name": "Direct Intervention", "probability": 30}
                        ]
                    }
                ]
            },
            {
                "name": "Status Quo",
                "probability": 25,
                "children": [
                    {
                        "name": "Managed Tension",
                        "probability": 60,
                        "children": [
                            {"name": "Proxy Conflicts", "probability": 70},
                            {"name": "Cyber War", "probability": 30}
                        ]
                    },
                    {
                        "name": "Gradual Escalation",
                        "probability": 40,
                        "children": [
                            {"name": "Nuclear Progress", "probability": 80},
                            {"name": "Regional Spread", "probability": 20}
                        ]
                    }
                ]
            }
        ]
        
        return self.create_scenario_tree(
            root_event="Current Situation\nFeb 2026",
            branches=branches,
            title="US-Iran Conflict Scenario Tree",
            title_fa="US-Iran Conflict Scenario Tree"
        )

    def create_iran_dependency_network(self) -> str:
        """
        Create a pre-defined dependency network for Iran situation.
        
        Returns:
            Path to saved chart
        """
        events = [
            {"id": "sanctions", "name": "Sanctions\nIntensity", "probability": 85, "type": "cause"},
            {"id": "protests", "name": "Iran\nProtests", "probability": 70, "type": "cause"},
            {"id": "nuclear", "name": "Nuclear\nProgress", "probability": 65, "type": "both"},
            {"id": "negotiations", "name": "Negotiations\nSuccess", "probability": 35, "type": "effect"},
            {"id": "strike", "name": "US Military\nStrike", "probability": 40, "type": "effect"},
            {"id": "regional", "name": "Regional\nInstability", "probability": 60, "type": "both"},
            {"id": "gold", "name": "Gold\nPrice Surge", "probability": 75, "type": "effect"},
            {"id": "regime", "name": "Regime\nChange", "probability": 25, "type": "effect"},
        ]
        
        dependencies = [
            {"cause": "sanctions", "effect": "protests", "strength": 0.6, "direction": "positive"},
            {"cause": "sanctions", "effect": "nuclear", "strength": 0.4, "direction": "positive"},
            {"cause": "protests", "effect": "regime", "strength": 0.7, "direction": "positive"},
            {"cause": "nuclear", "effect": "strike", "strength": 0.8, "direction": "positive"},
            {"cause": "nuclear", "effect": "negotiations", "strength": 0.5, "direction": "negative"},
            {"cause": "negotiations", "effect": "strike", "strength": 0.7, "direction": "negative"},
            {"cause": "strike", "effect": "regional", "strength": 0.9, "direction": "positive"},
            {"cause": "strike", "effect": "gold", "strength": 0.8, "direction": "positive"},
            {"cause": "regional", "effect": "gold", "strength": 0.5, "direction": "positive"},
            {"cause": "regime", "effect": "negotiations", "strength": 0.6, "direction": "positive"},
        ]
        
        return self.create_event_dependency_graph(
            events=events,
            dependencies=dependencies,
            title="US-Iran Conflict Dependency Network",
            title_fa="US-Iran Conflict Dependency Network"
        )

    def create_conditional_scenarios(self) -> str:
        """
        Create pre-defined conditional flow chart for Iran scenarios.
        
        Returns:
            Path to saved chart
        """
        conditions = [
            {
                "condition": "Istanbul Negotiations Fail",
                "condition_prob": 40,
                "outcomes": [
                    {"outcome": "Military Strike within 90 days", "probability": 55, "impact": "critical"},
                    {"outcome": "New Sanctions Package", "probability": 35, "impact": "high"},
                    {"outcome": "Back-channel Continues", "probability": 10, "impact": "medium"}
                ]
            },
            {
                "condition": "Iran Tests Nuclear Device",
                "condition_prob": 15,
                "outcomes": [
                    {"outcome": "Immediate Strike", "probability": 75, "impact": "critical"},
                    {"outcome": "UN Security Council", "probability": 20, "impact": "high"},
                    {"outcome": "MAD Deterrence", "probability": 5, "impact": "uncertain"}
                ]
            },
            {
                "condition": "Regime Collapses",
                "condition_prob": 20,
                "outcomes": [
                    {"outcome": "Democratic Transition", "probability": 30, "impact": "low"},
                    {"outcome": "Civil War", "probability": 40, "impact": "critical"},
                    {"outcome": "Military Takeover", "probability": 30, "impact": "high"}
                ]
            },
            {
                "condition": "Deal Reached",
                "condition_prob": 30,
                "outcomes": [
                    {"outcome": "Full Normalization", "probability": 25, "impact": "low"},
                    {"outcome": "Partial Lifting", "probability": 55, "impact": "medium"},
                    {"outcome": "Hardliner Backlash", "probability": 20, "impact": "high"}
                ]
            }
        ]
        
        return self.create_conditional_flow_chart(
            conditions=conditions,
            title="Conditional Scenarios: If X Then Y",
            title_fa="Conditional Scenarios: If X Then Y"
        )
    
    def create_regime_change_sankey(self) -> str:
        """
        Create a Sankey-style diagram showing regime change scenarios.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Define the flow data
        # Left column: Current state, Middle: Triggers, Right: Outcomes
        
        # Create a manual Sankey-like visualization using rectangles and arrows
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # Background
        ax.set_facecolor('#f8f9fa')
        
        # Title
        ax.text(5, 9.5, 'Regime Change Scenario Flow', 
                ha='center', fontsize=14, fontweight='bold')
        
        # Column headers
        headers = [
            (1, 8.5, 'Current State'),
            (5, 8.5, 'Trigger Events'),
            (9, 8.5, 'Outcomes')
        ]
        for x, y, text in headers:
            ax.text(x, y, text, ha='center', fontsize=11, fontweight='bold', 
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Current state box (left)
        current = mpatches.FancyBboxPatch((0.2, 4), 1.6, 3, boxstyle="round,pad=0.05",
                                          facecolor=COLORS['primary'], edgecolor='black', alpha=0.8)
        ax.add_patch(current)
        ax.text(1, 5.5, 'Islamic\nRepublic\n(100%)', ha='center', va='center', 
                fontsize=10, color='white', fontweight='bold')
        
        # Trigger events (middle)
        triggers = [
            (4, 6.5, 'US Strike\n(25%)', COLORS['danger'], 0.8),
            (4, 4.5, 'Mass Protests\n(70%)', COLORS['warning'], 0.7),
            (4, 2.5, 'Nuclear Deal\n(35%)', COLORS['success'], 0.6),
            (6, 5.5, 'IRGC Fracture\n(20%)', COLORS['secondary'], 0.5),
        ]
        
        for x, y, text, color, alpha in triggers:
            box = mpatches.FancyBboxPatch((x-0.8, y-0.8), 1.6, 1.6, boxstyle="round,pad=0.05",
                                          facecolor=color, edgecolor='black', alpha=alpha)
            ax.add_patch(box)
            ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Outcomes (right)
        outcomes = [
            (8.5, 7, 'Military Rule\n(35%)', COLORS['dark']),
            (8.5, 5.2, 'Chaos\n(25%)', COLORS['danger']),
            (8.5, 3.4, 'Democracy\n(18%)', COLORS['success']),
            (8.5, 1.6, 'Regime Survives\n(55%)', COLORS['primary']),
        ]
        
        for x, y, text, color in outcomes:
            box = mpatches.FancyBboxPatch((x-0.7, y-0.7), 1.4, 1.4, boxstyle="round,pad=0.05",
                                          facecolor=color, edgecolor='black', alpha=0.8)
            ax.add_patch(box)
            ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold', color='white')
        
        # Draw arrows (simplified)
        arrow_style = dict(arrowstyle='->', color='gray', lw=1.5)
        
        # From current to triggers
        ax.annotate('', xy=(3.2, 6.5), xytext=(1.8, 5.5), arrowprops=arrow_style)
        ax.annotate('', xy=(3.2, 4.5), xytext=(1.8, 5.5), arrowprops=arrow_style)
        ax.annotate('', xy=(3.2, 2.5), xytext=(1.8, 5.5), arrowprops=arrow_style)
        
        # From triggers to outcomes
        ax.annotate('', xy=(7.8, 7), xytext=(4.8, 6.5), arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.annotate('', xy=(7.8, 5.2), xytext=(4.8, 4.5), arrowprops=dict(arrowstyle='->', color='orange', lw=2))
        ax.annotate('', xy=(7.8, 3.4), xytext=(4.8, 2.5), arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.annotate('', xy=(7.8, 1.6), xytext=(4.8, 2.5), arrowprops=dict(arrowstyle='->', color='blue', lw=1))
        
        # Legend/notes
        ax.text(5, 0.3, 
                'Note: Probabilities are not mutually exclusive. Multiple triggers can occur simultaneously.',
                ha='center', fontsize=9, style='italic', alpha=0.7)
        
        
        ax.axis('off')
        plt.tight_layout()
        
        return self._save_chart(fig, "regime_change_sankey")
    
    def create_market_politics_heatmap(self) -> str:
        """
        Create a heatmap showing correlation between market indicators and political events.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Correlation matrix data (market indicators vs political outcomes)
        markets = ['Gold', 'VIX', 'Oil', 'S&P 500', 'Bitcoin', 'USD Index']
        events = ['US Strike', 'Regime Fall', 'Nuclear Deal', 'Protests', 'Regional War', 'Sanctions']
        
        # Correlation values (estimated)
        correlations = np.array([
            [0.78, 0.65, 0.45, 0.55, 0.70, 0.40],  # Gold
            [0.65, 0.50, -0.30, 0.45, 0.60, 0.35],  # VIX
            [0.70, 0.55, -0.25, 0.35, 0.75, 0.50],  # Oil
            [-0.45, -0.35, 0.30, -0.25, -0.55, -0.20],  # S&P 500
            [0.20, 0.15, 0.10, 0.25, 0.30, -0.10],  # Bitcoin
            [0.30, 0.25, -0.35, 0.20, 0.40, 0.45],  # USD Index
        ])
        
        # Create heatmap
        im = ax.imshow(correlations, cmap='RdYlGn_r', aspect='auto', vmin=-1, vmax=1)
        
        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Correlation', rotation=-90, va="bottom", fontsize=10)
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(events)))
        ax.set_yticks(np.arange(len(markets)))
        ax.set_xticklabels(events, fontsize=10)
        ax.set_yticklabels(markets, fontsize=10)
        
        # Rotate x labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Add correlation values as text
        for i in range(len(markets)):
            for j in range(len(events)):
                color = 'white' if abs(correlations[i, j]) > 0.4 else 'black'
                text = ax.text(j, i, f'{correlations[i, j]:.2f}',
                              ha="center", va="center", color=color, fontsize=9, fontweight='bold')
        
        ax.set_title('Market-Politics Correlation Matrix', 
                    fontsize=13, fontweight='bold', pad=20)
        
        # Add interpretation legend
        ax.text(0.5, -0.15, 
                '🔴 Strong Positive (>0.5): Event increases market indicator\n'
                '🟢 Strong Negative (<-0.5): Event decreases market indicator',
                transform=ax.transAxes, ha='center', fontsize=9, style='italic')
        
        plt.tight_layout()
        
        return self._save_chart(fig, "market_politics_heatmap")
    
    # =========================================================================
    # PROBABILITY TREES (Multiple Styles)
    # =========================================================================
    
    def create_binary_strike_tree(self) -> str:
        """
        Create a simple binary decision tree for US Strike probability.
        Clear and easy to read.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(16, 11))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 10)
        ax.set_facecolor('#fafafa')
        ax.axis('off')
        
        # Title
        ax.text(7, 9.5, 'US Strike on Iran: Binary Decision Tree', 
                ha='center', fontsize=14, fontweight='bold')
        
        # Root node
        root = mpatches.FancyBboxPatch((5.5, 7), 3, 1.5, boxstyle="round,pad=0.1",
                                        facecolor='#3498db', edgecolor='black', linewidth=2)
        ax.add_patch(root)
        ax.text(7, 7.75, 'Current Situation\nFeb 2026', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Level 1: Strike or No Strike
        # YES branch
        yes_box = mpatches.FancyBboxPatch((1, 4), 3, 1.5, boxstyle="round,pad=0.1",
                                           facecolor='#e74c3c', edgecolor='black', linewidth=2)
        ax.add_patch(yes_box)
        ax.text(2.5, 4.75, 'US STRIKES\n25.5%', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # NO branch
        no_box = mpatches.FancyBboxPatch((10, 4), 3, 1.5, boxstyle="round,pad=0.1",
                                          facecolor='#27ae60', edgecolor='black', linewidth=2)
        ax.add_patch(no_box)
        ax.text(11.5, 4.75, 'NO STRIKE\n74.5%', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Arrows from root
        ax.annotate('', xy=(2.5, 5.5), xytext=(5.5, 7),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=3))
        ax.annotate('', xy=(11.5, 5.5), xytext=(8.5, 7),
                    arrowprops=dict(arrowstyle='->', color='#27ae60', lw=3))
        
        # Labels on arrows
        ax.text(3.5, 6.5, '25.5%', fontsize=12, fontweight='bold', color='#e74c3c')
        ax.text(10, 6.5, '74.5%', fontsize=12, fontweight='bold', color='#27ae60')
        
        # Level 2: Outcomes after Strike
        outcomes_strike = [
            (0, 1, 'Limited Strike\n65%', '#f39c12'),
            (3, 1, 'Full War\n25%', '#c0392b'),
            (6, 1, 'Regime Change\n10%', '#8e44ad'),
        ]
        
        for x, y, text, color in outcomes_strike:
            box = mpatches.FancyBboxPatch((x, y), 2.5, 1.3, boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x + 1.25, y + 0.65, text, ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
            ax.annotate('', xy=(x + 1.25, y + 1.3), xytext=(2.5, 4),
                        arrowprops=dict(arrowstyle='->', color=color, lw=2))
        
        # Level 2: Outcomes after No Strike
        outcomes_no_strike = [
            (9, 1, 'Negotiations\n40%', '#2ecc71'),
            (12, 1, 'Status Quo\n60%', '#16a085'),
        ]
        
        for x, y, text, color in outcomes_no_strike:
            box = mpatches.FancyBboxPatch((x, y), 2.5, 1.3, boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x + 1.25, y + 0.65, text, ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
            ax.annotate('', xy=(x + 1.25, y + 1.3), xytext=(11.5, 4),
                        arrowprops=dict(arrowstyle='->', color=color, lw=2))
        
        # Legend/Note
        ax.text(7, 0.3, 'Probabilities are based on Polymarket data + Reddit sentiment analysis',
                ha='center', fontsize=9, style='italic', alpha=0.7)
        
        plt.tight_layout()
        return self._save_chart(fig, "binary_strike_tree")
    
    def create_regime_outcome_tree(self) -> str:
        """
        Create a probability tree for regime outcomes.
        Shows what happens if regime falls vs survives.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 12)
        ax.set_facecolor('#f5f5f5')
        ax.axis('off')
        
        # Title
        ax.text(8, 11.5, 'Iran Regime Outcome Tree', 
                ha='center', fontsize=15, fontweight='bold')
        ax.text(8, 11, 'Conditional Probabilities: P(Outcome | Trigger)', 
                ha='center', fontsize=11, style='italic', alpha=0.8)
        
        # Root: Islamic Republic
        root = mpatches.FancyBboxPatch((6.5, 8.5), 3, 1.5, boxstyle="round,pad=0.1",
                                        facecolor='#2c3e50', edgecolor='black', linewidth=2)
        ax.add_patch(root)
        ax.text(8, 9.25, 'Islamic Republic\n(Current)', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Level 1: Regime Falls (30%) vs Survives (70%)
        # Falls
        falls_box = mpatches.FancyBboxPatch((1, 5.5), 3.5, 1.5, boxstyle="round,pad=0.1",
                                             facecolor='#e74c3c', edgecolor='black', linewidth=2)
        ax.add_patch(falls_box)
        ax.text(2.75, 6.25, 'REGIME FALLS\n30%', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Survives
        survives_box = mpatches.FancyBboxPatch((11.5, 5.5), 3.5, 1.5, boxstyle="round,pad=0.1",
                                                facecolor='#27ae60', edgecolor='black', linewidth=2)
        ax.add_patch(survives_box)
        ax.text(13.25, 6.25, 'REGIME SURVIVES\n70%', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Arrows from root
        ax.annotate('', xy=(2.75, 7), xytext=(6.5, 8.5),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=3))
        ax.annotate('', xy=(13.25, 7), xytext=(9.5, 8.5),
                    arrowprops=dict(arrowstyle='->', color='#27ae60', lw=3))
        ax.text(4, 8, '30%', fontsize=13, fontweight='bold', color='#e74c3c',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax.text(11, 8, '70%', fontsize=13, fontweight='bold', color='#27ae60',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Level 2: Outcomes if Regime Falls
        outcomes_falls = [
            (0, 2, 'Military Rule\n35%', '#34495e', '10.5%'),
            (2.2, 0.3, 'Civil War\n25%', '#c0392b', '7.5%'),
            (4.4, 2, 'Democracy\n20%', '#3498db', '6.0%'),
            (0.5, 3.8, 'Monarchy\n8%', '#9b59b6', '2.4%'),
            (3.5, 3.8, 'Chaos\n12%', '#e67e22', '3.6%'),
        ]
        
        for x, y, text, color, total in outcomes_falls:
            box = mpatches.FancyBboxPatch((x, y), 2, 1.3, boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x + 1, y + 0.65, text, ha='center', va='center', 
                    fontsize=8, fontweight='bold', color='white')
            ax.annotate('', xy=(x + 1, y + 1.3), xytext=(2.75, 5.5),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.7))
            # Total probability label
            ax.text(x + 1, y - 0.3, f'Total: {total}', ha='center', fontsize=8, 
                    fontweight='bold', color=color)
        
        # Level 2: Outcomes if Regime Survives
        outcomes_survives = [
            (10, 2, 'Reform\n25%', '#2ecc71', '17.5%'),
            (12.5, 2, 'Hardline\n45%', '#16a085', '31.5%'),
            (12.5, 0.3, 'Stagnation\n30%', '#1abc9c', '21.0%'),
        ]
        
        for x, y, text, color, total in outcomes_survives:
            box = mpatches.FancyBboxPatch((x, y), 2.3, 1.3, boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x + 1.15, y + 0.65, text, ha='center', va='center', 
                    fontsize=8, fontweight='bold', color='white')
            ax.annotate('', xy=(x + 1.15, y + 1.3), xytext=(13.25, 5.5),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.7))
            ax.text(x + 1.15, y - 0.3, f'Total: {total}', ha='center', fontsize=8, 
                    fontweight='bold', color=color)
        
        # Formula box
        formula_text = "Formula: P(Outcome) = P(Branch) × P(Outcome|Branch)"
        ax.text(8, -0.3, formula_text, ha='center', fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        plt.tight_layout()
        return self._save_chart(fig, "regime_outcome_tree")
    
    def create_timeline_probability_tree(self) -> str:
        """
        Create a timeline-based probability tree showing how probabilities
        change over different time windows.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 16))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 16)
        ax.set_facecolor('#f8f9fa')
        ax.axis('off')

        ax.text(5, 15.2, 'Strike Probability by Timeline (Cumulative)', 
                ha='center', fontsize=15, fontweight='bold')

        timeline = [
            ('Feb 2026', 5, 13.5, 5.0, '#27ae60'),
            ('Mar 2026', 5, 11.0, 15.0, '#f1c40f'),
            ('Apr 2026', 5, 8.5, 25.0, '#e67e22'),
            ('May 2026', 5, 6.0, 35.0, '#e74c3c'),
            ('Jun 2026', 5, 3.5, 50.5, '#c0392b'),
        ]

        for i, (label, x, y, prob, color) in enumerate(timeline):
            box = mpatches.FancyBboxPatch((x - 2.2, y - 0.9), 4.4, 1.8, 
                                          boxstyle="round,pad=0.08",
                                          facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(box)
            ax.text(x, y, f'{label}\nCumulative: {prob:.1f}%', ha='center', va='center', 
                    fontsize=11, fontweight='bold', color='white')

            if i < len(timeline) - 1:
                next_prob = timeline[i + 1][3]
                delta = next_prob - prob
                ax.annotate('', xy=(x, y - 1.2), xytext=(x, y - 0.1),
                            arrowprops=dict(arrowstyle='->', color='gray', lw=2))
                ax.text(x + 2.6, y - 0.65, f'+{delta:.1f}%', ha='left',
                        fontsize=10, fontweight='bold', color='gray')

        ax.text(5, 1.0, 'Window probabilities and hazard rates are derived from this term structure.',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout()
        return self._save_chart(fig, "timeline_probability_tree")
    
    def create_bayesian_update_tree(self) -> str:
        """
        Create a Bayesian-style probability tree showing how
        prior probabilities update with new evidence.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(18, 13))
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 12)
        ax.set_facecolor('#fff')
        ax.axis('off')
        
        # Title
        ax.text(8, 11.5, 'Bayesian Probability Updates', 
                ha='center', fontsize=15, fontweight='bold')
        
        # Prior probability (starting point)
        prior_box = mpatches.FancyBboxPatch((6.5, 9), 3, 1.5, boxstyle="round,pad=0.1",
                                             facecolor='#3498db', edgecolor='black', linewidth=2)
        ax.add_patch(prior_box)
        ax.text(8, 9.75, 'PRIOR\nP(Strike) = 25%', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Evidence updates
        evidence_items = [
            {
                'name': 'Istanbul Talks Fail',
                'x': 2, 'y': 6,
                'likelihood_ratio': 2.0,
                'posterior': 40,
                'color': '#e74c3c'
            },
            {
                'name': 'Gold > $5,500',
                'x': 6.5, 'y': 6,
                'likelihood_ratio': 1.5,
                'posterior': 33,
                'color': '#f39c12'
            },
            {
                'name': 'Iran Nuclear Test',
                'x': 11, 'y': 6,
                'likelihood_ratio': 4.0,
                'posterior': 60,
                'color': '#9b59b6'
            },
        ]
        
        for ev in evidence_items:
            # Evidence box
            box = mpatches.FancyBboxPatch((ev['x'], ev['y']), 3, 1.8, boxstyle="round,pad=0.1",
                                           facecolor=ev['color'], edgecolor='black', linewidth=2)
            ax.add_patch(box)
            ax.text(ev['x'] + 1.5, ev['y'] + 0.9, 
                    f"{ev['name']}\nLR = {ev['likelihood_ratio']}\nP(Strike|E) = {ev['posterior']}%", 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')
            
            # Arrow from prior
            ax.annotate('', xy=(ev['x'] + 1.5, ev['y'] + 1.8), xytext=(8, 9),
                        arrowprops=dict(arrowstyle='->', color=ev['color'], lw=2))
        
        # Combined evidence (if all happen)
        combined_box = mpatches.FancyBboxPatch((6, 2.5), 4, 1.8, boxstyle="round,pad=0.1",
                                                facecolor='#c0392b', edgecolor='black', linewidth=3)
        ax.add_patch(combined_box)
        ax.text(8, 3.4, 'ALL EVIDENCE\nP(Strike|All) = 75%', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        
        # Arrows to combined
        for ev in evidence_items:
            ax.annotate('', xy=(8, 4.3), xytext=(ev['x'] + 1.5, ev['y']),
                        arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, ls='--'))
        
        # Bayes formula
        formula = r"""Bayes' Theorem: P(A|B) = P(B|A) × P(A) / P(B)

Likelihood Ratio (LR) = P(Evidence|Strike) / P(Evidence|No Strike)"""
        
        ax.text(8, 0.8, formula, ha='center', fontsize=9, family='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))
        
        plt.tight_layout()
        return self._save_chart(fig, "bayesian_update_tree")
    
    def create_war_scenario_tree(self) -> str:
        """
        Create a detailed tree for different war scenarios and their outcomes.
        
        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(24, 18))
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 16)
        ax.set_facecolor('#f5f5f5')
        ax.axis('off')
        
        # Title
        ax.text(10, 15.0, 'War Scenario Decision Tree', 
                ha='center', fontsize=16, fontweight='bold')
        
        # Root: If Strike Happens
        root = mpatches.FancyBboxPatch((8, 12), 4, 1.8, boxstyle="round,pad=0.1",
                                        facecolor='#e74c3c', edgecolor='black', linewidth=2)
        ax.add_patch(root)
        ax.text(10, 12.9, 'IF US STRIKES IRAN\n(Given: 25.5%)', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        
        # Level 1: Type of Strike
        strike_types = [
            ('Limited Strike\n(Nuclear Sites)', 3, 9.5, 60, '#f39c12'),
            ('Sustained Campaign\n(Air + Naval)', 10, 9.5, 30, '#e67e22'),
            ('Full Invasion\n(Ground Forces)', 17, 9.5, 10, '#c0392b'),
        ]
        
        for label, x, y, prob, color in strike_types:
            box = mpatches.FancyBboxPatch((x - 1.5, y - 0.75), 3, 1.5, 
                                           boxstyle="round,pad=0.1",
                                           facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(box)
            ax.text(x, y, f'{wrap_text_for_chart(label, width=16)}\n{prob}%', ha='center', va='center', 
                    fontsize=10, fontweight='bold', color='white')
            ax.annotate('', xy=(x, y + 0.75), xytext=(10, 12),
                        arrowprops=dict(arrowstyle='->', color=color, lw=2))
            ax.text(x - 0.5 if x < 9 else x + 0.5, y + 1.5, f'{prob}%', 
                    fontsize=11, fontweight='bold', color=color)
        
        # Level 2: Duration outcomes for Limited Strike
        limited_outcomes = [
            ('Days', 1.5, 6.0, 50, '#2ecc71'),
            ('Weeks', 3.5, 6.0, 35, '#f1c40f'),
            ('Months', 5.5, 6.0, 15, '#e67e22'),
        ]
        
        for label, x, y, prob, color in limited_outcomes:
            box = mpatches.FancyBboxPatch((x - 0.7, y - 0.6), 1.4, 1.2, 
                                           boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x, y, f'{label}\n{prob}%', ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white' if color != '#f1c40f' else 'black')
            ax.annotate('', xy=(x, y + 0.6), xytext=(3, 8.75),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        
        # Level 2: Duration outcomes for Sustained Campaign
        sustained_outcomes = [
            ('Weeks', 8.0, 6.0, 30, '#f1c40f'),
            ('Months', 10.0, 6.0, 50, '#e67e22'),
            ('Years', 12.0, 6.0, 20, '#c0392b'),
        ]
        
        for label, x, y, prob, color in sustained_outcomes:
            box = mpatches.FancyBboxPatch((x - 0.7, y - 0.6), 1.4, 1.2, 
                                           boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x, y, f'{label}\n{prob}%', ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white' if color != '#f1c40f' else 'black')
            ax.annotate('', xy=(x, y + 0.6), xytext=(10, 8.75),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        
        # Level 2: Duration outcomes for Full Invasion
        invasion_outcomes = [
            ('Months', 15.0, 6.0, 20, '#e67e22'),
            ('Years', 17.0, 6.0, 60, '#c0392b'),
            ('Decade+', 19.0, 6.0, 20, '#8e44ad'),
        ]
        
        for label, x, y, prob, color in invasion_outcomes:
            box = mpatches.FancyBboxPatch((x - 0.7, y - 0.6), 1.4, 1.2, 
                                           boxstyle="round,pad=0.05",
                                           facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(x, y, f'{label}\n{prob}%', ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
            ax.annotate('', xy=(x, y + 0.6), xytext=(17, 8.75),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        
        # Casualties row
        casualties_box = mpatches.FancyBboxPatch((0.5, 2), 19, 1.8, boxstyle="round,pad=0.1",
                                                  facecolor='#ecf0f1', edgecolor='black', linewidth=1)
        ax.add_patch(casualties_box)
        ax.text(10, 3.3, 'Estimated Casualties', ha='center', fontsize=12, fontweight='bold')
        
        casualty_data = [
            ('Limited', 2.5, '1K-10K'),
            ('Sustained', 9, '10K-100K'),
            ('Invasion', 15, '100K-1M+'),
        ]
        
        for label, x, casualties in casualty_data:
            ax.text(x, 2.5, f'{label}: {casualties}', ha='center', fontsize=10, fontweight='bold')
        
        # Economic impact row
        ax.text(10, 0.8, 'Economic Impact: Limited (-5% GDP) → Sustained (-15% GDP) → Invasion (-30%+ GDP)', 
                ha='center', fontsize=11, style='italic')
        
        
        plt.tight_layout()
        return self._save_chart(fig, "war_scenario_tree")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_generated_charts(self) -> List[str]:
        """Return list of all generated chart paths."""
        return self.generated_charts
    
    def clear_old_charts(self, days: int = 7):
        """Remove charts older than specified days."""
        import time
        now = time.time()
        cutoff = now - (days * 86400)
        
        for filepath in Path(self.output_dir).glob('*.png'):
            if filepath.stat().st_mtime < cutoff:
                filepath.unlink()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_all_charts(analysis_data: Dict, polymarket_data: Dict, 
                        news_data: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate all charts for a complete report.
    
    Args:
        analysis_data: Reddit/LLM analysis results
        polymarket_data: Polymarket data
        news_data: Optional news analysis data
    
    Returns:
        Dictionary mapping chart names to file paths
    """
    generator = ChartGenerator()
    charts = {}
    
    # Extract data with defaults
    results = analysis_data.get('results', {})
    attack_likely = results.get('attack_likely', 0)
    no_attack = results.get('no_attack', 0)
    uncertain = results.get('uncertain', 0)
    
    pm_analysis = polymarket_data.get('market_analysis', {})
    main_prob = pm_analysis.get('probabilities', {}).get('This Month', 45)
    
    # 1. Probability gauge
    charts['probability_gauge'] = generator.create_probability_gauge(main_prob, "Strike Probability")
    
    # 2. Probability donut
    charts['probability_donut'] = generator.create_probability_donut(main_prob, "Attack vs No Attack")
    
    # 3. Reddit sentiment
    if attack_likely + no_attack + uncertain > 0:
        charts['reddit_sentiment'] = generator.create_reddit_sentiment_chart(
            attack_likely, no_attack, uncertain, "Reddit User Predictions"
        )
    
    # 4. Source comparison
    source_probs = {
        'Reddit': results.get('attack_probability', 40),
        'Polymarket': main_prob,
        'Gold Signal': pm_analysis.get('gold_based_probabilities', {}).get('This Month', 35),
    }
    if news_data:
        source_probs['News'] = news_data.get('strike_probability', 40)
    charts['probability_comparison'] = generator.create_probability_comparison(source_probs)
    
    # 5. Deadline timeline
    deadlines = []
    for deadline_name, prob in pm_analysis.get('probabilities', {}).items():
        deadlines.append({
            'label': deadline_name,
            'probability': prob,
            'date': deadline_name,
            'volume': pm_analysis.get('volumes', {}).get(deadline_name, 0)
        })
    if deadlines:
        charts['deadline_timeline'] = generator.create_deadline_timeline(deadlines)
    
    # 6. Market comparison
    gold_price = pm_analysis.get('gold', {}).get('price', 2850)
    btc_price = pm_analysis.get('bitcoin', {}).get('price', 97500)
    charts['market_comparison'] = generator.create_market_comparison(
        gold_price, btc_price, 
        pm_analysis.get('gold', {}).get('change_24h', 0),
        pm_analysis.get('bitcoin', {}).get('change_24h', 0)
    )
    
    # 7. Crisis correlation
    charts['crisis_correlation'] = generator.create_crisis_correlation_chart()
    
    # 8. Portfolio allocation
    portfolio = {
        'Gold': 25,
        'Bitcoin': 15,
        'Cash/USD': 40,
        'Polymarket': 10,
        'Stocks': 10
    }
    charts['portfolio_allocation'] = generator.create_portfolio_allocation(portfolio)
    
    # 9. News sentiment if available
    if news_data:
        sentiment = news_data.get('sentiment_distribution', {})
        if sentiment:
            charts['news_sentiment'] = generator.create_sentiment_breakdown(
                sentiment, "News Sentiment Analysis"
            )
    
    # 10. Summary dashboard
    dashboard_data = {
        'main_probability': main_prob,
        'source_probabilities': source_probs,
        'sentiment': {'Attack Likely': attack_likely, 'No Attack': no_attack, 'Uncertain': uncertain},
        'deadlines': deadlines[:4] if deadlines else [],
        'portfolio': portfolio,
        'key_metrics': {
            'Total Users': f"{attack_likely + no_attack + uncertain:,}",
            'PM Probability': f"{main_prob}%",
            'Gold Price': f"${gold_price:,.0f}",
            'BTC Price': f"${btc_price:,.0f}"
        },
        'smart_money': {'YES': 35, 'NO': 65}
    }
    charts['summary_dashboard'] = generator.create_summary_dashboard(dashboard_data)
    
    return charts


if __name__ == "__main__":
    # Test chart generation
    print("Testing Chart Generator...")
    
    gen = ChartGenerator()
    
    # Test probability gauge
    path1 = gen.create_probability_gauge(45.2, "Test Probability")
    print(f"✅ Created: {path1}")
    
    # Test probability comparison
    path2 = gen.create_probability_comparison({
        'Reddit': 42,
        'Polymarket': 45,
        'News': 38,
        'Gold Signal': 35
    })
    print(f"✅ Created: {path2}")
    
    # Test deadline timeline
    path3 = gen.create_deadline_timeline([
        {'label': 'Feb 28', 'probability': 45, 'date': '2026-02-28', 'volume': 5000000},
        {'label': 'Mar 31', 'probability': 50, 'date': '2026-03-31', 'volume': 8000000},
        {'label': 'Jun 30', 'probability': 55, 'date': '2026-06-30', 'volume': 15000000},
    ])
    print(f"✅ Created: {path3}")
    
    # Test market comparison
    path4 = gen.create_market_comparison(2850, 97500, 0.5, -1.2)
    print(f"✅ Created: {path4}")
    
    # Test portfolio allocation  
    path5 = gen.create_portfolio_allocation({
        'Gold': 25,
        'Bitcoin': 15,
        'Cash': 40,
        'Polymarket': 10,
        'Stocks': 10
    })
    print(f"✅ Created: {path5}")
    
    print(f"\n✅ All test charts created in: {gen.output_dir}")
    print(f"Total charts: {len(gen.generated_charts)}")
