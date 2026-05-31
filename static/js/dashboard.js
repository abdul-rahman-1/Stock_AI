// Main Dashboard Logic — Aligned with GEMINI.md institutional schema
'use strict';
let chart;
let candlestickSeries;

const initChart = () => {
    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer) return;

    try {
        chart = LightweightCharts.createChart(chartContainer, {
            layout: {
                background: { color: 'transparent' },
                textColor: 'rgba(255, 255, 255, 0.5)',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        candlestickSeries = chart.addCandlestickSeries({
            upColor: '#00ff88',
            downColor: '#ff3366',
            borderVisible: false,
            wickUpColor: '#00ff88',
            wickDownColor: '#ff3366',
        });

        window.addEventListener('resize', () => {
            chart.applyOptions({ width: chartContainer.clientWidth, height: chartContainer.clientHeight });
        });
    } catch (err) {
        console.error("Chart Init Error:", err);
    }
};

const updateChartFromSeries = (series) => {
    if (!series || !Array.isArray(series) || series.length === 0) return;
    try {
        const chartData = series.map(d => ({
            time: d[0],
            open: d[1],
            high: d[2],
            low: d[3],
            close: d[4],
        })).filter(d => d.time != null && d.open != null)
           .sort((a, b) => a.time - b.time);

        if (chartData.length > 0) {
            candlestickSeries.setData(chartData);
            chart.timeScale().fitContent();
        }
    } catch (err) {
        console.error("Chart Series Update Error:", err);
    }
};

// ─────────────────────────────────────────────────────────────
//  Main UI updater — reads from GEMINI.md institutional schema
// ─────────────────────────────────────────────────────────────
const updateUI = (data) => {
    // Handle top-level fetch / server errors
    if (!data) {
        const summaryText = document.getElementById('ai-summary-text');
        if (summaryText) summaryText.innerHTML = '<span class="text-rose-400 font-bold">ERROR:</span> No data received from server.';
        return;
    }

    // The analysis object is always at data.analysis
    const analysis = data.analysis || {};

    // If Gemini returned a hard error (no price data at all), show and bail
    if (!analysis || (analysis.error && !analysis.price)) {
        const summaryText = document.getElementById('ai-summary-text');
        const errMsg    = analysis?.error   || data?.error   || 'Analysis Failed';
        const errDetail = analysis?.details || data?.details || 'Check API Keys and server logs.';
        console.error('AI Analysis Error:', errMsg, errDetail);
        if (summaryText) {
            summaryText.innerHTML = `<span class="text-rose-400 font-bold">ERROR:</span> ${errMsg}<br><small class="text-white/30">${errDetail}</small>`;
        }
        return;
    }

    // Soft error — Gemini failed but we still have price/chart data from Python
    const hasGeminiError = !!analysis.error;

    // analysis is already defined above

    // ── Destructure GEMINI.md schema fields ──
    const price        = analysis.price            || {};
    const tech         = analysis.technical_analysis || {};
    const structure    = analysis.market_structure  || {};
    const volume       = analysis.volume_analysis   || {};
    const sentiment    = analysis.sentiment_analysis || {};
    const trade        = analysis.trade_setup        || {};
    const risk         = analysis.risk_analysis      || {};
    const aiSummary    = analysis.ai_summary         || {};
    const trend        = analysis.trend              || {};

    // ── Stock title & price header ──
    const stockEl = document.getElementById('stock-title');
    if (stockEl) stockEl.textContent = (analysis.stock || '').toUpperCase();

    const priceEl = document.getElementById('price-display');
    if (priceEl) {
        const change    = price.change || 0;
        const changePct = price.change_percent || 0;
        const isUp      = change >= 0;
        const fmt = (n) => n ? parseFloat(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--';
        priceEl.innerHTML = `
            <span class="text-2xl font-bold">₹${fmt(price.current)}</span>
            <span class="${isUp ? 'text-emerald-400' : 'text-rose-400'} ml-2">
                ${isUp ? '▲' : '▼'} ${Math.abs(changePct).toFixed(2)}%
            </span>
            <span class="text-white/30 text-xs ml-2 mono">H: ₹${fmt(price.day_high)}  L: ₹${fmt(price.day_low)}  VWAP: ₹${price.vwap ? fmt(price.vwap) : '--'}</span>
            ${hasGeminiError ? '<span class="ml-2 text-[9px] text-yellow-500/60 mono">[AI partial — raw data shown]</span>' : ''}
        `;
    }

    // ── Trend badges ──
    const trendEl = document.getElementById('trend-display');
    if (trendEl) {
        const trendColor = (t) => {
            if (!t) return 'text-white/30';
            const l = t.toLowerCase();
            if (l.includes('bull') || l.includes('up')) return 'text-emerald-400';
            if (l.includes('bear') || l.includes('down')) return 'text-rose-400';
            return 'text-yellow-400';
        };
        trendEl.innerHTML = `
            <span class="px-2 py-0.5 rounded bg-white/5 text-[10px] mono ${trendColor(trend.short_term)}">1m: ${trend.short_term || '--'}</span>
            <span class="px-2 py-0.5 rounded bg-white/5 text-[10px] mono ${trendColor(trend.intraday)}">Intraday: ${trend.intraday || '--'}</span>
            <span class="px-2 py-0.5 rounded bg-white/5 text-[10px] mono ${trendColor(trend.swing)}">Swing: ${trend.swing || '--'}</span>
        `;
    }

    // ── Technical indicators ──
    const rsiEl = document.getElementById('rsi-val');
    if (rsiEl) {
        const rsi = tech.rsi || 0;
        rsiEl.textContent = rsi.toFixed(2);
        rsiEl.className = `text-xl font-bold mono ${rsi > 70 ? 'text-rose-400' : rsi < 30 ? 'text-emerald-400' : 'text-white'}`;
    }

    const emaEl = document.getElementById('ema-val');
    if (emaEl) emaEl.textContent = `${(tech.ema9 || 0).toFixed(1)} / ${(tech.ema20 || 0).toFixed(1)}`;

    const macdEl = document.getElementById('macd-val');
    if (macdEl) {
        const macd = tech.macd_signal || '--';
        const macdColor = macd.toLowerCase().includes('bull') ? 'text-emerald-400' : macd.toLowerCase().includes('bear') ? 'text-rose-400' : 'text-white';
        macdEl.className = `text-sm font-bold mono ${macdColor}`;
        macdEl.textContent = macd;
    }

    const volEl = document.getElementById('volatility-val');
    if (volEl) {
        const vol = tech.volatility || '--';
        const volColor = vol.toLowerCase() === 'high' ? 'text-rose-400' : vol.toLowerCase() === 'low' ? 'text-emerald-400' : 'text-yellow-400';
        volEl.className = `text-sm font-bold mono ${volColor}`;
        volEl.textContent = vol;
    }

    // ── Support & Resistance ──
    const resList = document.getElementById('resistance-list');
    const supList = document.getElementById('support-list');
    const resistanceLevels = structure.resistance_levels || [];
    const supportLevels    = structure.support_levels    || [];

    if (resList) {
        resList.innerHTML = resistanceLevels.length > 0
            ? resistanceLevels.map(val => `<div class="bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded text-xs mono text-rose-400">₹${val}</div>`).join('')
            : '<div class="text-xs text-white/20 mono">No resistance levels identified</div>';
    }
    if (supList) {
        supList.innerHTML = supportLevels.length > 0
            ? supportLevels.map(val => `<div class="bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded text-xs mono text-emerald-400">₹${val}</div>`).join('')
            : '<div class="text-xs text-white/20 mono">No support levels identified</div>';
    }

    // ── Breakout / Reversal probabilities ──
    const brkEl = document.getElementById('breakout-prob');
    const revEl = document.getElementById('reversal-prob');
    if (brkEl) brkEl.textContent = `${structure.breakout_probability || 0}%`;
    if (revEl) revEl.textContent = `${structure.reversal_probability || 0}%`;

    // ── Volume analysis ──
    const volInstEl = document.getElementById('inst-activity');
    const volAccEl  = document.getElementById('acc-dist');
    if (volInstEl) volInstEl.textContent = volume.institutional_activity || '--';
    if (volAccEl)  volAccEl.textContent  = volume.accumulation_distribution || '--';

    // ── Trade call card — full adaptive render ──
    const signalBadge  = document.getElementById('signal-badge');
    const signal       = (trade.signal || 'WAITING').toUpperCase();
    const isHold       = signal === 'HOLD' || signal === 'WAITING';
    const isBuy        = signal === 'BUY';
    const isSell       = signal === 'SELL';

    // Signal badge
    if (signalBadge) {
        signalBadge.textContent = signal;
        signalBadge.className = `px-4 py-2 rounded-full text-2xl font-black italic tracking-widest mono ${
            isBuy  ? 'bg-emerald-500/20 text-emerald-400 shadow-lg shadow-emerald-500/20' :
            isSell ? 'bg-rose-500/20    text-rose-400    shadow-lg shadow-rose-500/20'    :
                     'bg-yellow-500/10  text-yellow-400'
        }`;
    }

    // Update the card header label
    const callHeader = document.getElementById('trade-call-header');
    if (callHeader) {
        callHeader.textContent = isHold ? 'WATCH LEVELS' : 'INTRADAY CALL';
    }

    // Format a price: show -- only if truly 0 or missing
    const fmtPrice = (val, prefix = '₹') => {
        const n = parseFloat(val);
        if (!n || n === 0) return '--';
        return `${prefix}${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    // Labels adapt: for HOLD they say "Watch Entry / Watch Stop" etc.
    const setRow = (labelId, valId, labelText, val, colorClass = '') => {
        const lEl = document.getElementById(labelId);
        const vEl = document.getElementById(valId);
        if (lEl) lEl.textContent = labelText;
        if (vEl) {
            vEl.textContent  = fmtPrice(val);
            if (colorClass) vEl.className = `mono font-bold ${colorClass}`;
        }
    };

    if (isHold) {
        setRow('lbl-entry',   'entry-val',   'Watch Entry',   trade.entry,     'text-yellow-400');
        setRow('lbl-target1', 'target1-val', 'Upside Target', trade.target1,   'text-emerald-400');
        setRow('lbl-target2', 'target2-val', 'Extended Target',trade.target2,  'text-emerald-400');
        setRow('lbl-sl',      'sl-val',      'Downside Risk', trade.stop_loss, 'text-rose-400');
    } else {
        setRow('lbl-entry',   'entry-val',   'Entry',     trade.entry,     'text-white');
        setRow('lbl-target1', 'target1-val', 'Target 1',  trade.target1,   'text-emerald-400');
        setRow('lbl-target2', 'target2-val', 'Target 2',  trade.target2,   'text-emerald-400');
        setRow('lbl-sl',      'sl-val',      'Stop Loss', trade.stop_loss, 'text-rose-400');
    }

    const rrEl = document.getElementById('rr-ratio');
    if (rrEl) rrEl.textContent = trade.risk_reward_ratio || (isHold ? 'Watch mode' : '--');

    // HOLD reason box
    const holdBox = document.getElementById('hold-reason-box');
    const holdReasonEl = document.getElementById('hold-reason-text');
    const triggerEl    = document.getElementById('hold-trigger-text');
    if (holdBox) {
        if (isHold && (trade.hold_reason || trade.watch_trigger)) {
            holdBox.classList.remove('hidden');
            if (holdReasonEl) holdReasonEl.textContent = trade.hold_reason  || trade.trade_quality || '';
            if (triggerEl)    triggerEl.textContent    = trade.watch_trigger || '';
        } else {
            holdBox.classList.add('hidden');
        }
    }

    const tradeTypeEl = document.getElementById('trade-type-badges');
    if (tradeTypeEl) {
        const badges = [];
        if (trade.scalp_trade)    badges.push('<span class="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded text-cyan-400 text-[10px] mono">SCALP</span>');
        if (trade.breakout_trade) badges.push('<span class="px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 rounded text-purple-400 text-[10px] mono">BREAKOUT</span>');
        if (trade.swing_trade)    badges.push('<span class="px-2 py-0.5 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-400 text-[10px] mono">SWING</span>');
        tradeTypeEl.innerHTML = badges.join('') || '';
    }

    const confVal = document.getElementById('confidence-val');
    const confBar = document.getElementById('confidence-bar');
    const conf = trade.confidence || 0;
    if (confVal) confVal.textContent = `${conf}%`;
    if (confBar) {
        confBar.style.width = `${conf}%`;
        confBar.className = `h-full transition-all duration-1000 ${conf >= 75 ? 'bg-emerald-500' : conf >= 60 ? 'bg-yellow-500' : 'bg-rose-500'}`;
    }

    // ── Sentiment meter ──
    const sentScoreEl = document.getElementById('sentiment-score');
    const sentLabelEl = document.getElementById('sentiment-label');
    let rawScore = sentiment.score || 0;
    if (Math.abs(rawScore) <= 1 && rawScore !== 0) rawScore *= 100; // normalize if -1..1

    if (sentScoreEl) {
        sentScoreEl.textContent = Math.round(rawScore);
        sentScoreEl.className = `text-2xl font-black mono ${rawScore > 20 ? 'text-emerald-400' : rawScore < -20 ? 'text-rose-400' : 'text-yellow-400'}`;
    }
    if (sentLabelEl) sentLabelEl.textContent = sentiment.overall_sentiment || 'Neutral';

    const arc = document.getElementById('sentiment-arc');
    if (arc) {
        const offset = 126 - ((rawScore + 100) / 200) * 126;
        arc.style.strokeDashoffset = Math.max(0, Math.min(126, offset));
    }

    // ── Sentiment news counts ──
    const bullEl = document.getElementById('bull-news');
    const bearEl = document.getElementById('bear-news');
    const neutEl = document.getElementById('neut-news');
    if (bullEl) bullEl.textContent = sentiment.bullish_news || 0;
    if (bearEl) bearEl.textContent = sentiment.bearish_news || 0;
    if (neutEl) neutEl.textContent = sentiment.neutral_news || 0;

    // ── AI Summary ──
    const summaryTextEl = document.getElementById('ai-summary-text');
    if (summaryTextEl) summaryTextEl.textContent = aiSummary.intraday_outlook || 'No intraday outlook generated.';

    const riskWarningEl = document.getElementById('risk-warning');
    const riskTextEl    = document.getElementById('risk-text');
    const riskMsg = aiSummary.risk_warning || risk.overall_risk || '';
    if (riskMsg && riskWarningEl) {
        riskWarningEl.classList.remove('hidden');
        if (riskTextEl) riskTextEl.textContent = riskMsg;
    } else if (riskWarningEl) {
        riskWarningEl.classList.add('hidden');
    }

    // ── News list ──
    const newsList = document.getElementById('news-list');
    if (newsList) {
        const majorNews = sentiment.major_news || [];
        if (majorNews.length > 0) {
            newsList.innerHTML = majorNews.map(n =>
                `<div class="border-b border-white/5 pb-3 last:border-0 last:pb-0">
                    <p class="text-xs text-white/70 leading-relaxed">${typeof n === 'string' ? n : (n.title || n.headline || JSON.stringify(n))}</p>
                </div>`
            ).join('');
        } else if (sentiment.institutional_sentiment) {
            newsList.innerHTML = `<p class="text-xs text-white/70 leading-relaxed">${sentiment.institutional_sentiment}</p>`;
        } else {
            newsList.innerHTML = '<p class="text-xs text-white/30 text-center py-8">No recent news found.</p>';
        }
    }

    // ── Chart data ──
    if (analysis.chart_series && analysis.chart_series.length > 0) {
        updateChartFromSeries(analysis.chart_series);
    } else {
        console.log("No chart_series returned by AI.");
    }

    // ── Trigger reveal animation ──
    if (window.revealAnalysis) window.revealAnalysis();
};

// ─────────────────────────────────────────────────────────────
//  Analyze button handler
// ─────────────────────────────────────────────────────────────
document.getElementById('analyze-btn').addEventListener('click', async () => {
    const stockInput = document.getElementById('stock-input');
    const stock = stockInput ? stockInput.value.trim().toUpperCase() : '';
    if (!stock) return alert("Please enter a stock symbol (e.g., TATASTEEL.NS)");

    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
        gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.5 });
    }

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock })
        });
        const data = await response.json();

        // Hard server error (no analysis object at all)
        if (data.error && !data.analysis) {
            alert(`Server Error: ${data.error}\n${data.details || ''}`);
        } else {
            // updateUI handles both full success and soft-error (partial) responses
            updateUI(data);
        }
    } catch (err) {
        console.error("Fetch error:", err);
        alert("Connectivity Error — check the backend server is running on port 5000.");
    } finally {
        if (overlay) {
            gsap.to(overlay, {
                opacity: 0,
                duration: 0.5,
                onComplete: () => { overlay.style.display = 'none'; }
            });
        }
    }
});

// Also trigger on Enter key
document.getElementById('stock-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('analyze-btn').click();
});

initChart();
