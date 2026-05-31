import os
import json
import time
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

# CRITICAL: load_dotenv MUST be first before any os.getenv() calls
load_dotenv()

# ── Yahoo Finance headers (mimics a real browser to avoid 403/429) ──
YF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://finance.yahoo.com",
    "Referer": "https://finance.yahoo.com/",
}


def _fetch_yf(symbol: str, range_: str, interval: str) -> dict | None:
    """Fetch OHLCV data from Yahoo Finance v8 API. Returns raw JSON or None."""
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?range={range_}&interval={interval}&includePrePost=false"
    )
    for attempt in range(3):
        try:
            r = requests.get(url, headers=YF_HEADERS, timeout=15)
            if r.status_code == 200:
                payload = r.json()
                result = payload.get("chart", {}).get("result", [])
                if result:
                    return result[0]
            elif r.status_code in (429, 503):
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"[YF Fetch] Attempt {attempt+1} failed for {symbol} {range_}/{interval}: {e}")
            time.sleep(1)
    return None


def _parse_ohlcv(yf_result: dict, max_points: int = 120) -> list[list]:
    """Convert Yahoo Finance chart result into [[ts, O, H, L, C, V], ...] format."""
    if not yf_result:
        return []
    try:
        meta = yf_result.get("meta", {})
        timestamps = yf_result.get("timestamp", [])
        quotes = yf_result.get("indicators", {}).get("quote", [{}])[0]
        opens  = quotes.get("open",   [])
        highs  = quotes.get("high",   [])
        lows   = quotes.get("low",    [])
        closes = quotes.get("close",  [])
        vols   = quotes.get("volume", [])

        rows = []
        for i, ts in enumerate(timestamps):
            o = opens[i]  if i < len(opens)  else None
            h = highs[i]  if i < len(highs)  else None
            l = lows[i]   if i < len(lows)   else None
            c = closes[i] if i < len(closes) else None
            v = vols[i]   if i < len(vols)   else None
            if None in (o, h, l, c) or o == 0:
                continue
            rows.append([ts, round(o, 4), round(h, 4), round(l, 4), round(c, 4), int(v or 0)])

        # Return last max_points rows
        return rows[-max_points:]
    except Exception as e:
        print(f"[Parse OHLCV] Error: {e}")
        return []


def _fetch_news(symbol: str, api_token: str) -> list[dict]:
    """Fetch news articles from MarketAux."""
    if not api_token:
        return []
    url = (
        f"https://api.marketaux.com/v1/news/all"
        f"?symbols={symbol}&filter_entities=true&language=en&api_token={api_token}&limit=10"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception as e:
        print(f"[News Fetch] Error: {e}")
    return []


def _summarize_news(articles: list[dict]) -> str:
    """Convert raw news articles into a compact text block for the prompt."""
    if not articles:
        return "No news articles available."
    lines = []
    for a in articles[:10]:
        title     = a.get("title", "")
        sentiment = a.get("entities", [{}])[0].get("sentiment_score", "N/A") if a.get("entities") else "N/A"
        published = a.get("published_at", "")[:10]
        lines.append(f"- [{published}] {title} (sentiment: {sentiment})")
    return "\n".join(lines)


def _ohlcv_to_text(rows: list[list], label: str) -> str:
    """Format OHLCV rows as compact text for the prompt."""
    if not rows:
        return f"{label}: No data available.\n"
    header = f"{label} ({len(rows)} bars) — [timestamp, open, high, low, close, volume]\n"
    body   = "\n".join(str(r) for r in rows[-60:])  # send last 60 bars
    return header + body + "\n"


class AIService:
    def __init__(self):
        self.api_key         = os.getenv("GOOGLE_API_KEY")
        self.news_api_token  = os.getenv("MARKETAUX_API_TOKEN")

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    # ─────────────────────────────────────────────────────────────
    def generate_analysis(self, symbol: str) -> dict:
        """
        1. Fetches Yahoo Finance OHLCV data in Python (avoids bot blocks).
        2. Fetches news from MarketAux in Python.
        3. Embeds all data directly in the prompt.
        4. Calls Gemini (no URL Context tool needed — data is inline).
        """
        if not self.client:
            return {
                "error": "Google API Key not configured.",
                "details": "Please set GOOGLE_API_KEY in your .env file."
            }

        print(f"[AI] Fetching market data for {symbol}...")

        # ── 1. Fetch data server-side ──
        yf_1d  = _fetch_yf(symbol, "1d",  "1m")
        yf_8d  = _fetch_yf(symbol, "8d",  "1m")
        yf_1mo = _fetch_yf(symbol, "1mo", "1h")

        ohlcv_1d  = _parse_ohlcv(yf_1d,  max_points=120)
        ohlcv_8d  = _parse_ohlcv(yf_8d,  max_points=80)
        ohlcv_1mo = _parse_ohlcv(yf_1mo, max_points=60)

        news_articles = _fetch_news(symbol, self.news_api_token)
        news_text     = _summarize_news(news_articles)

        # ── Meta info from Yahoo ──
        meta_1d     = (yf_1d  or {}).get("meta", {})
        current_px  = meta_1d.get("regularMarketPrice", 0)
        prev_close  = meta_1d.get("chartPreviousClose", 0)
        day_high    = meta_1d.get("regularMarketDayHigh", 0)
        day_low     = meta_1d.get("regularMarketDayLow",  0)
        market_state = meta_1d.get("marketState", "UNKNOWN")
        currency    = meta_1d.get("currency", "USD")

        data_status = "FULL" if ohlcv_1d else "PARTIAL — Yahoo Finance returned no intraday data"

        # ── 2. Build prompt — faithful implementation of GEMINI.md ──
        prompt = f"""
You are an institutional-grade AI trading analyst specializing in:
- NSE
- BSE
- Intraday trading
- Swing trading
- Smart money analysis
- Quantitative market analysis

Your objective is to perform DEEP multi-timeframe market analysis for the stock: {symbol}
Current Market State : {market_state}
Currency             : {currency}

You must think like:
- hedge funds
- proprietary trading firms
- institutional traders
- quantitative analysts

====================================================
LIVE MARKET DATA — USE THIS DIRECTLY
====================================================

All data has been pre-fetched for you. Use it directly — do NOT fabricate any values.

Current Price : {current_px}
Previous Close: {prev_close}
Day High      : {day_high}
Day Low       : {day_low}

{_ohlcv_to_text(ohlcv_1d,  "1-DAY INTRADAY DATA (1 MIN bars)")}
{_ohlcv_to_text(ohlcv_8d,  "8-DAY INTRADAY DATA (1 MIN bars)")}
{_ohlcv_to_text(ohlcv_1mo, "1-MONTH DATA (1 HOUR bars)")}

====================================================
NEWS SENTIMENT DATA
====================================================
{news_text}

====================================================
CORE OBJECTIVE
====================================================

Perform deep institutional-level market analysis.

Do NOT generate generic retail-level analysis.

Use:
- price action
- momentum
- volume
- volatility
- market structure
- sentiment
- multi-timeframe trend alignment
- smart money concepts
- institutional behavior
- breakout probability
- reversal probability

to determine the highest probability trading setup.

====================================================
ANALYSIS REQUIREMENTS
====================================================

You MUST deeply analyze:

----------------------------------------------------
1. PRICE STRUCTURE
----------------------------------------------------

Detect:
- current trend
- trend strength
- trend exhaustion
- higher highs / lower lows
- consolidation zones
- breakout structure
- fake breakouts
- liquidity traps
- accumulation
- distribution
- supply zones
- demand zones

Determine:
- bullish structure
- bearish structure
- neutral structure

----------------------------------------------------
2. MULTI-TIMEFRAME ANALYSIS
----------------------------------------------------

Use:
- 1 minute timeframe
- intraday timeframe
- hourly timeframe

Compare:
- short-term momentum
- medium-term momentum
- swing structure

Detect:
- timeframe alignment
- conflicting signals
- momentum shift
- reversal setup

----------------------------------------------------
3. TECHNICAL INDICATORS
----------------------------------------------------

Analyze deeply (calculate from the raw OHLCV data above):

- EMA 9
- EMA 20
- RSI 14
- MACD (12, 26, 9 signal)
- Bollinger Bands (20, 2 std)
- VWAP (from intraday data)
- volatility expansion
- volatility compression
- volume spikes

Determine:
- crossover quality
- overbought/oversold conditions
- momentum acceleration
- momentum weakness
- continuation probability

----------------------------------------------------
4. VOLUME ANALYSIS
----------------------------------------------------

Analyze:
- unusual volume
- relative volume
- buying pressure
- selling pressure
- institutional accumulation
- institutional distribution

Detect:
- breakout confirmation
- weak breakout
- fake breakout
- smart money participation

----------------------------------------------------
5. SENTIMENT ANALYSIS
----------------------------------------------------

Use the news data above to analyze:

- bullish news count
- bearish news count
- neutral news count
- sentiment score
- institutional sentiment
- risk sentiment
- macro impact
- sector impact

Determine:
- whether news supports price movement
- whether price and sentiment diverge
- whether sentiment is strengthening or weakening

----------------------------------------------------
6. RISK ANALYSIS
----------------------------------------------------

Detect:
- high volatility risk
- reversal risk
- trap probability
- news risk
- gap continuation risk
- stop hunt probability

Estimate:
- overall market risk
- trade quality
- probability of success

====================================================
TRADE DECISION ENGINE
====================================================

Generate ONLY high probability setups.

If setup quality is weak: signal = HOLD.

Generate:
- BUY  : Strong bullish confluence across all timeframes. Confidence >= 60.
- SELL : Strong bearish confluence across all timeframes. Confidence >= 60.
- HOLD : Setup not confirmed, conflicting signals, or confidence < 60.

based on:
- trend confirmation
- momentum
- sentiment
- volume
- volatility
- breakout confirmation
- multi-timeframe alignment

====================================================
TRADE REQUIREMENTS
====================================================

If BUY or SELL — provide REAL calculated price levels:
- entry price     (exact level based on structure)
- stop loss       (below demand zone / above supply zone)
- target 1        (first structural resistance/support)
- target 2        (extended target based on swing structure)
- confidence %    (per confidence logic below)
- risk reward ratio (e.g. "1:2.5")
- scalp trade possibility
- breakout trade possibility
- swing trade possibility

If HOLD — STILL populate all price levels as KEY WATCH LEVELS.
Do NOT leave entry, stop_loss, target1, target2 as 0.
- entry     = the level to watch for potential entry trigger
- stop_loss = downside risk if triggered
- target1   = upside potential if setup confirms
- target2   = extended upside
- hold_reason   = 1-2 sentences: WHY setup is not confirmed
- watch_trigger = exact condition to upgrade HOLD → BUY or SELL

====================================================
IMPORTANT RULES
====================================================

1. DO NOT hallucinate data.
2. DO NOT generate generic analysis.
3. DO NOT blindly trust indicators.
4. Prioritize capital preservation.
5. Avoid weak setups.
6. Detect institutional activity.
7. Detect fake breakouts.
8. Use confluence analysis.
9. Think step-by-step internally.
10. Return ONLY structured JSON.

====================================================
CONFIDENCE LOGIC
====================================================

90-100:
Exceptional setup with strong confluence.

75-89:
Strong setup with good confirmation.

60-74:
Moderate setup with elevated risk.

Below 60:
Return HOLD. Confidence field still reflects the true score.

====================================================
CHART SERIES — REQUIRED
====================================================

You MUST include chart_series in your response.
Extract from the 1-DAY INTRADAY DATA above.
Format: [ [unix_timestamp, open, high, low, close], ... ]
Include ALL available data points.

====================================================
FINAL INSTRUCTIONS
====================================================

Think deeply before generating output.

Use:
- technical confluence
- market structure
- sentiment
- volatility
- volume
- momentum
- institutional logic

to generate the final decision.

Return ONLY valid JSON. No markdown. No explanation. No code fences.

{{
  "stock": "{symbol}",
  "market_state": "{market_state}",
  "trend": {{
    "short_term": "",
    "intraday": "",
    "swing": ""
  }},
  "price": {{
    "current": {current_px},
    "day_high": {day_high},
    "day_low": {day_low},
    "vwap": 0,
    "change": 0,
    "change_percent": 0
  }},
  "technical_analysis": {{
    "ema9": 0,
    "ema20": 0,
    "rsi": 0,
    "macd_signal": "",
    "bollinger_band_state": "",
    "volatility": "",
    "momentum_strength": ""
  }},
  "market_structure": {{
    "support_levels": [],
    "resistance_levels": [],
    "trend_strength": "",
    "breakout_probability": 0,
    "reversal_probability": 0,
    "fake_breakout_risk": ""
  }},
  "volume_analysis": {{
    "volume_spike": false,
    "institutional_activity": "",
    "accumulation_distribution": "",
    "buying_pressure": "",
    "selling_pressure": ""
  }},
  "sentiment_analysis": {{
    "score": 0,
    "bullish_news": 0,
    "bearish_news": 0,
    "neutral_news": 0,
    "institutional_sentiment": "",
    "major_news": [],
    "overall_sentiment": ""
  }},
  "trade_setup": {{
    "signal": "",
    "entry": 0,
    "stop_loss": 0,
    "target1": 0,
    "target2": 0,
    "confidence": 0,
    "risk_reward_ratio": "",
    "trade_quality": "",
    "hold_reason": "",
    "watch_trigger": "",
    "scalp_trade": false,
    "breakout_trade": false,
    "swing_trade": false
  }},
  "risk_analysis": {{
    "overall_risk": "",
    "volatility_risk": "",
    "news_risk": "",
    "trap_risk": "",
    "gap_risk": ""
  }},
  "ai_summary": {{
    "short_term_outlook": "",
    "intraday_outlook": "",
    "swing_outlook": "",
    "institutional_view": "",
    "risk_warning": ""
  }},
  "chart_series": []
}}
"""

        print(f"[AI] Sending prompt to Gemini — data embedded inline ({len(ohlcv_1d)} 1d bars, {len(ohlcv_8d)} 8d bars, {len(ohlcv_1mo)} 1mo bars)")

        # ── 3. Call Gemini ──
        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=5000),
                    )
                )

                text = response.text or ""
                print(f"[AI] Response received ({len(text)} chars) — extracting JSON")

                # ── Robust JSON extraction ──
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                json_start = text.find('{')
                json_end   = text.rfind('}')

                if json_start != -1 and json_end != -1:
                    json_str = text[json_start:json_end + 1]
                    parsed   = json.loads(json_str)

                    # ── Inject chart_series from Python data if AI omitted it ──
                    if not parsed.get("chart_series") and ohlcv_1d:
                        parsed["chart_series"] = [[r[0], r[1], r[2], r[3], r[4]] for r in ohlcv_1d]

                    # ── Inject price fields if AI left them at 0 ──
                    price_block = parsed.setdefault("price", {})
                    if not price_block.get("current") and current_px:
                        price_block["current"]    = current_px
                        price_block["day_high"]   = day_high
                        price_block["day_low"]    = day_low
                        if prev_close:
                            change = round(current_px - prev_close, 4)
                            pct    = round((change / prev_close) * 100, 2) if prev_close else 0
                            price_block["change"]         = change
                            price_block["change_percent"] = pct

                    return parsed
                else:
                    print(f"[AI] Attempt {attempt+1}: No JSON found in response.")
                    if attempt == 0:
                        time.sleep(2)

            except Exception as e:
                err_str = str(e)
                print(f"[Gemini Error] Attempt {attempt+1}: {err_str}")
                if attempt == 0:
                    time.sleep(3)

        # ── Fallback: return what we have from Python data ──
        print("[AI] Returning Python-data fallback after Gemini failures.")
        change = round(current_px - prev_close, 4) if prev_close and current_px else 0
        pct    = round((change / prev_close) * 100, 2) if prev_close else 0

        return {
            "stock": symbol,
            "market_state": market_state,
            "error": "Gemini analysis unavailable — showing raw market data only.",
            "price": {
                "current": current_px,
                "day_high": day_high,
                "day_low": day_low,
                "vwap": 0,
                "change": change,
                "change_percent": pct
            },
            "chart_series": [[r[0], r[1], r[2], r[3], r[4]] for r in ohlcv_1d],
            "trend": {"short_term": "N/A", "intraday": "N/A", "swing": "N/A"},
            "technical_analysis": {"ema9": 0, "ema20": 0, "rsi": 0, "macd_signal": "N/A",
                                   "bollinger_band_state": "N/A", "volatility": "N/A", "momentum_strength": "N/A"},
            "market_structure": {"support_levels": [], "resistance_levels": [],
                                 "trend_strength": "N/A", "breakout_probability": 0,
                                 "reversal_probability": 0, "fake_breakout_risk": "N/A"},
            "volume_analysis": {"volume_spike": False, "institutional_activity": "N/A",
                                "accumulation_distribution": "N/A", "buying_pressure": "N/A", "selling_pressure": "N/A"},
            "sentiment_analysis": {"score": 0, "bullish_news": 0, "bearish_news": 0,
                                   "neutral_news": 0, "institutional_sentiment": "N/A",
                                   "major_news": [], "overall_sentiment": "N/A"},
            "trade_setup": {"signal": "HOLD", "entry": 0, "stop_loss": 0, "target1": 0,
                            "target2": 0, "confidence": 0, "risk_reward_ratio": "N/A",
                            "trade_quality": "N/A", "scalp_trade": False,
                            "breakout_trade": False, "swing_trade": False},
            "risk_analysis": {"overall_risk": "N/A", "volatility_risk": "N/A",
                              "news_risk": "N/A", "trap_risk": "N/A", "gap_risk": "N/A"},
            "ai_summary": {"short_term_outlook": "Gemini analysis failed. Raw market data is shown.",
                           "intraday_outlook": "N/A", "swing_outlook": "N/A",
                           "institutional_view": "N/A",
                           "risk_warning": "AI analysis unavailable — do not trade on this data alone."}
        }
