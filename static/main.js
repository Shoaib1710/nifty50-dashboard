// ═══════════════════════════════════════════════════════════
//  static/main.js  —  Nifty 50 AI Dashboard Frontend
// ═══════════════════════════════════════════════════════════

// ─── Theme colors ────────────────────────────────────────────────
const C = {
  bg:     '#0a0e1a', card:   '#111827', border: '#1f2937',
  accent: '#3b82f6', green:  '#10b981', red:    '#ef4444',
  yellow: '#f59e0b', purple: '#8b5cf6', text:   '#e5e7eb',
  sub:    '#6b7280', orange: '#f97316',
};

const LAYOUT_BASE = {
  paper_bgcolor: C.bg, plot_bgcolor: C.card,
  font: { color: C.text, family: 'Segoe UI, system-ui, sans-serif' },
  margin: { l: 10, r: 10, t: 40, b: 10 },
  legend: { bgcolor: C.bg, bordercolor: C.border },
};
const AXIS = { gridcolor: C.border, zerolinecolor: C.border };

// ─── State ──────────────────────────────────────────────────────
let currentSymbol = 'NIFTY_INDEX';
let currentPeriod = '1y';
let chartData     = null;
let mlData        = null;

// ─── Utilities ──────────────────────────────────────────────────
function showSpinner(title = 'Loading…', msg = 'Please wait') {
  document.getElementById('spinner-title').textContent = title;
  document.getElementById('spinner-msg').textContent   = msg;
  document.getElementById('spinner').style.display     = 'flex';
}
function hideSpinner() { document.getElementById('spinner').style.display = 'none'; }

function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `show ${type}`;
  setTimeout(() => { el.className = ''; }, 3500);
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmt(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function quantile(arr, q) {
  const sorted = [...arr].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length * q)];
}

// ─── Tab switching ───────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');

    // Lazy load on tab switch
    const tab = btn.dataset.tab;
    if (tab === 'tab-heat') fetchHeatmap();
    if (tab === 'tab-news') fetchNews();
    if (tab === 'tab-fund') fetchFundamentals();
  });
});

// ─── Populate dropdowns ──────────────────────────────────────────
async function populateSymbols() {
  const res  = await fetch('/api/stocks');
  const data = await res.json();
  const dd   = document.getElementById('symbol-dd');
  dd.innerHTML = '';
  data.options.forEach(opt => {
    const o = document.createElement('option');
    o.value = opt.value;
    o.textContent = opt.label;
    if (opt.value === 'NIFTY_INDEX') o.selected = true;
    dd.appendChild(o);
  });
}

// ─── Fetch chart data ────────────────────────────────────────────
async function fetchData() {
  showSpinner('Fetching Market Data', 'Downloading price history…');
  try {
    const res = await fetch(`/api/data?symbol=${encodeURIComponent(currentSymbol)}&period=${currentPeriod}`);
    chartData = await res.json();
    if (chartData.error) { showToast('⚠️ ' + chartData.error, 'error'); chartData = null; return; }
    updateKPIs();
    drawCandle();
    drawRSI();
    drawMACD();
    drawBacktest();
    showToast('✅ Data loaded', 'success');
  } catch (e) {
    showToast('❌ Network error: ' + e.message, 'error');
  } finally {
    hideSpinner();
  }
}

// ─── Fetch heatmap ───────────────────────────────────────────────
async function fetchHeatmap() {
  try {
    const res  = await fetch('/api/heatmap');
    const data = await res.json();
    drawHeatmap(data);
  } catch (e) {
    console.warn('Heatmap fetch failed', e);
  }
}

// ─── Fetch news & sentiment ──────────────────────────────────────
async function fetchNews() {
  try {
    const res  = await fetch(`/api/news?symbol=${encodeURIComponent(currentSymbol)}`);
    const data = await res.json();
    renderNews(data);
  } catch (e) {
    console.warn('News fetch failed', e);
  }
}

// ─── Fetch fundamentals ──────────────────────────────────────────
async function fetchFundamentals() {
  showSpinner('Loading Fundamentals', 'Fetching company data…');
  try {
    const res  = await fetch(`/api/fundamentals?symbol=${encodeURIComponent(currentSymbol)}`);
    const data = await res.json();
    renderFundamentals(data);
  } catch (e) {
    console.warn('Fundamentals fetch failed', e);
  } finally {
    hideSpinner();
  }
}

// ─── Run ML ──────────────────────────────────────────────────────
async function runML() {
  showSpinner('Training AI Models', 'LSTM + Random Forest + Gradient Boosting…');
  document.getElementById('train-btn').disabled = true;
  try {
    const res = await fetch('/api/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: currentSymbol, period: currentPeriod }),
    });
    mlData = await res.json();
    if (mlData.error) { showToast('⚠️ ' + mlData.error, 'error'); mlData = null; return; }
    drawLSTM();
    drawFeatures();
    updateMLKPIs();
    showToast('🤖 ML Training complete!', 'success');
  } catch (e) {
    showToast('❌ ML error: ' + e.message, 'error');
  } finally {
    hideSpinner();
    document.getElementById('train-btn').disabled = false;
  }
}

// ─── KPI Update ──────────────────────────────────────────────────
function updateKPIs() {
  if (!chartData) return;
  const kpi = chartData.kpi;
  const chgColor = kpi.change >= 0 ? C.green : C.red;
  setText('kpi-price',  `₹${fmt(kpi.price)}`);
  setText('kpi-name',   kpi.name);
  setText('kpi-change', `${kpi.change >= 0 ? '+' : ''}${kpi.change.toFixed(2)}`);
  document.getElementById('kpi-change').style.color = chgColor;
  setText('kpi-pct',    `(${kpi.pct >= 0 ? '+' : ''}${kpi.pct.toFixed(2)}%)`);
  setText('kpi-high',   `₹${fmt(kpi.high52)}`);
  setText('kpi-low',    `₹${fmt(kpi.low52)}`);
  const sig   = kpi.signal || 'HOLD';
  const sigEl = document.getElementById('kpi-signal');
  sigEl.textContent = sig;
  sigEl.className = 'value signal-' + sig.toLowerCase();
  setText('kpi-rsi', kpi.rsi ? `RSI: ${kpi.rsi.toFixed(1)}` : '—');
}

function updateMLKPIs() {
  if (!mlData) return;
  const sigEl = document.getElementById('kpi-ai');
  sigEl.textContent = mlData.current_signal || '—';
  sigEl.className = 'value signal-' + (mlData.current_signal || 'hold').toLowerCase();
  setText('kpi-conf', `Confidence: ${mlData.confidence}%`);
}

// ─── Candlestick Chart ────────────────────────────────────────────
function drawCandle() {
  if (!chartData) return;
  const d = chartData;
  const traces = [];

  traces.push({
    type: 'candlestick',
    x: d.dates, open: d.open, high: d.high, low: d.low, close: d.close,
    name: 'Price',
    increasing: { line: { color: C.green } },
    decreasing: { line: { color: C.red } },
    xaxis: 'x', yaxis: 'y',
  });

  if (d.bb_upper) traces.push({ type: 'scatter', x: d.dates, y: d.bb_upper, name: 'BB Upper', line: { color: C.sub, dash: 'dash', width: 1 }, opacity: .5, yaxis: 'y' });
  if (d.bb_mid)   traces.push({ type: 'scatter', x: d.dates, y: d.bb_mid,   name: 'BB Mid',   line: { color: C.sub, dash: 'dot',  width: 1 }, opacity: .5, yaxis: 'y' });
  if (d.bb_lower) traces.push({ type: 'scatter', x: d.dates, y: d.bb_lower, name: 'BB Lower', line: { color: C.sub, dash: 'dash', width: 1 }, opacity: .5, yaxis: 'y' });
  if (d.ema20)    traces.push({ type: 'scatter', x: d.dates, y: d.ema20,    name: 'EMA 20',   line: { color: C.orange, width: 1.5 }, yaxis: 'y' });
  if (d.ema50)    traces.push({ type: 'scatter', x: d.dates, y: d.ema50,    name: 'EMA 50',   line: { color: C.purple, width: 1.5 }, yaxis: 'y' });

  const buys  = d.signals.filter(s => s.type === 'BUY');
  const sells = d.signals.filter(s => s.type === 'SELL');
  if (buys.length)  traces.push({ type: 'scatter', x: buys.map(s => s.date),  y: buys.map(s => s.y),  mode: 'markers', name: 'BUY',  marker: { symbol: 'triangle-up',   size: 10, color: C.green }, yaxis: 'y' });
  if (sells.length) traces.push({ type: 'scatter', x: sells.map(s => s.date), y: sells.map(s => s.y), mode: 'markers', name: 'SELL', marker: { symbol: 'triangle-down', size: 10, color: C.red   }, yaxis: 'y' });

  const volColors = d.close.map((c, i) => c >= (d.open[i] || c) ? C.green : C.red);
  traces.push({ type: 'bar', x: d.dates, y: d.volume, name: 'Volume', marker: { color: volColors }, opacity: .5, xaxis: 'x', yaxis: 'y2' });

  const layout = {
    ...LAYOUT_BASE,
    title: `${d.name} — Candlestick + Bollinger Bands + Signals`,
    xaxis:  { ...AXIS, rangeslider: { visible: false }, domain: [0, 1] },
    yaxis:  { ...AXIS, domain: [0.25, 1] },
    yaxis2: { ...AXIS, domain: [0, 0.22] },
    grid:   { rows: 2, columns: 1, pattern: 'independent' },
  };
  Plotly.newPlot('candle-chart', traces, layout, { responsive: true, displayModeBar: false });
}

// ─── RSI ──────────────────────────────────────────────────────────
function drawRSI() {
  if (!chartData || !chartData.rsi) return;
  const d = chartData;
  Plotly.newPlot('rsi-chart', [{
    type: 'scatter', x: d.dates, y: d.rsi, name: 'RSI',
    line: { color: C.accent, width: 2 }, fill: 'tozeroy', fillcolor: 'rgba(59,130,246,.06)',
  }], {
    ...LAYOUT_BASE, title: 'RSI (14)',
    yaxis: { ...AXIS, range: [0, 100] }, xaxis: AXIS,
    shapes: [
      { type: 'line', x0: d.dates[0], x1: d.dates.at(-1), y0: 70, y1: 70, line: { color: C.red,   dash: 'dash', width: 1 } },
      { type: 'line', x0: d.dates[0], x1: d.dates.at(-1), y0: 30, y1: 30, line: { color: C.green, dash: 'dash', width: 1 } },
    ],
    annotations: [
      { x: d.dates.at(-1), y: 70, text: 'Overbought', showarrow: false, font: { color: C.red,   size: 10 }, xanchor: 'right' },
      { x: d.dates.at(-1), y: 30, text: 'Oversold',   showarrow: false, font: { color: C.green, size: 10 }, xanchor: 'right' },
    ],
  }, { responsive: true, displayModeBar: false });
}

// ─── MACD ─────────────────────────────────────────────────────────
function drawMACD() {
  if (!chartData || !chartData.macd) return;
  const d = chartData;
  const histColors = d.macd_hist.map(v => v >= 0 ? C.green : C.red);
  Plotly.newPlot('macd-chart', [
    { type: 'scatter', x: d.dates, y: d.macd,      name: 'MACD',      line: { color: C.accent, width: 2 } },
    { type: 'scatter', x: d.dates, y: d.macd_sig,  name: 'Signal',    line: { color: C.yellow, width: 1.5, dash: 'dash' } },
    { type: 'bar',     x: d.dates, y: d.macd_hist, name: 'Histogram', marker: { color: histColors }, opacity: .6 },
  ], { ...LAYOUT_BASE, title: 'MACD', xaxis: AXIS, yaxis: AXIS }, { responsive: true, displayModeBar: false });
}

// ─── LSTM Chart ───────────────────────────────────────────────────
function drawLSTM() {
  if (!chartData) return;
  const d  = chartData;
  const ml = mlData;
  const traces = [
    { type: 'scatter', x: d.dates, y: d.close, name: 'Actual Price', line: { color: C.accent, width: 1.5 } },
  ];
  if (ml) {
    if (ml.test_dates)   traces.push({ type: 'scatter', x: ml.test_dates,   y: ml.pred_prices,   name: 'LSTM Predicted', line: { color: C.yellow, width: 2, dash: 'dash' } });
    if (ml.future_dates) traces.push({ type: 'scatter', x: ml.future_dates, y: ml.future_prices, name: 'Forecast',       line: { color: C.green,  width: 2.5 }, fill: 'tozeroy', fillcolor: 'rgba(16,185,129,.06)' });
  }
  Plotly.newPlot('lstm-chart', traces, {
    ...LAYOUT_BASE, title: `${d.name} — LSTM + Attention Forecast`, xaxis: AXIS, yaxis: AXIS,
  }, { responsive: true, displayModeBar: false });

  if (!ml) return;
  const trend = ml.future_prices && ml.future_prices.at(-1) > ml.future_prices[0] ? '📈 Upward' : '📉 Downward';
  const sigColors = { BUY: C.green, SELL: C.red, HOLD: C.yellow };
  document.getElementById('accuracy-body').innerHTML = `
    <p style="color:${C.sub};font-size:.72rem;margin-bottom:6px;">━━━ Accuracy Scores ━━━</p>
    ${accRow('LSTM (Directional)', ml.lstm_acc)}
    ${accRow('Random Forest', ml.rf_acc)}
    ${accRow('Gradient Boosting', ml.gb_acc)}
    ${accRow('🏆 Ensemble (Final)', ml.ensemble_acc, true)}
    <hr class="acc-divider"/>
    <p style="color:${C.sub};font-size:.72rem;margin-bottom:6px;">━━━ Error Metrics ━━━</p>
    <p style="margin-bottom:4px;">RMSE : ₹${ml.rmse}</p>
    <p style="margin-bottom:4px;">MAPE : ${ml.mape}%</p>
    <hr class="acc-divider"/>
    <p style="color:${C.sub};font-size:.72rem;margin-bottom:6px;">━━━ AI Signal ━━━</p>
    <p style="color:${sigColors[ml.current_signal] || C.text};font-size:1.4rem;font-weight:900;margin-bottom:4px;">${ml.current_signal}</p>
    <p style="margin-bottom:4px;">Confidence : ${ml.confidence}%</p>
    <p style="color:${C.accent};">15-Day Trend : ${trend}</p>
  `;
}

function accRow(label, val, big = false) {
  const c = val >= 75 ? C.green : val >= 65 ? C.yellow : C.red;
  return `<div class="acc-row">
    <span class="acc-label">${label}</span>
    <span class="acc-val" style="color:${c};font-size:${big ? '1rem' : '0.88rem'};">${val}%</span>
  </div>`;
}

// ─── Feature Importance ───────────────────────────────────────────
function drawFeatures() {
  if (!mlData || !mlData.importance) return;
  const imp  = mlData.importance.slice(0, 15);
  const max  = imp[0]?.Importance || 1;
  const vals = imp.map(r => r.Importance);
  const p66  = quantile(vals, .66), p33 = quantile(vals, .33);
  const colors = vals.map(v => v > p66 ? C.green : v > p33 ? C.yellow : C.red);
  const revImp = [...imp].reverse(), revC = [...colors].reverse();

  Plotly.newPlot('feature-chart',
    [{ type: 'bar', orientation: 'h',
       x: revImp.map(r => r.Importance), y: revImp.map(r => r.Feature),
       marker: { color: revC },
       text: revImp.map(r => r.Importance.toFixed(3)), textposition: 'outside',
    }],
    { ...LAYOUT_BASE, title: 'Feature Importance (Random Forest)',
      xaxis: { ...AXIS }, yaxis: { ...AXIS }, margin: { l: 10, r: 70, t: 40, b: 10 } },
    { responsive: true, displayModeBar: false });

  document.getElementById('feature-body').innerHTML = imp.map((r, i) => {
    const c   = r.Importance > 0.05 ? C.green : r.Importance > 0.02 ? C.yellow : C.sub;
    const pct = (r.Importance / max * 100).toFixed(0);
    return `<div class="feat-row">
      <span style="color:${C.sub};min-width:22px;">${i + 1}.</span>
      <span style="color:${C.text};flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${r.Feature}">${r.Feature}</span>
      <div class="feat-bar-wrap"><div class="feat-bar" style="width:${pct}%;background:${c};"></div></div>
      <span style="color:${c};min-width:46px;text-align:right;">${r.Importance.toFixed(4)}</span>
    </div>`;
  }).join('');
}

// ─── Heatmap ──────────────────────────────────────────────────────
function drawHeatmap(data) {
  if (!data) return;
  Plotly.newPlot('heatmap-chart', [{
    type: 'treemap',
    labels:  data.names,
    parents: data.sectors,
    values:  data.abs_rets,
    text:    data.rets.map(r => `${r >= 0 ? '+' : ''}${r.toFixed(2)}%`),
    textinfo: 'label+text',
    marker: {
      colors: data.rets,
      colorscale: [[0, C.red], [.5, C.card], [1, C.green]],
      cmid: 0,
    },
  }], { ...LAYOUT_BASE, title: "Nifty 50 — Today's Performance Heatmap" },
  { responsive: true, displayModeBar: false });

  Plotly.newPlot('sector-chart', [{
    type: 'bar', orientation: 'h',
    x: data.sect_rets, y: data.sect_names,
    marker: { color: data.sect_rets.map(r => r >= 0 ? C.green : C.red) },
    text: data.sect_rets.map(r => `${r >= 0 ? '+' : ''}${r.toFixed(2)}%`), textposition: 'outside',
  }], {
    ...LAYOUT_BASE, title: 'Sector Performance',
    xaxis: { ...AXIS }, yaxis: { ...AXIS }, margin: { l: 10, r: 70, t: 40, b: 10 },
  }, { responsive: true, displayModeBar: false });
}

// ─── News & Sentiment ─────────────────────────────────────────────
function renderNews(data) {
  if (!data) return;
  const sent     = data.sentiment;
  const scorePct = (sent.score + 1) / 2 * 100;

  Plotly.newPlot('sent-gauge', [{
    type: 'indicator', mode: 'gauge+number+delta',
    value: scorePct,
    title: { text: `Sentiment<br><sub>${sent.overall}</sub>`, font: { color: C.text } },
    delta: { reference: 50 },
    gauge: {
      axis: { range: [0, 100], tickcolor: C.sub },
      bar:  { color: C.accent },
      steps: [{ range: [0, 40], color: C.red }, { range: [40, 60], color: C.yellow }, { range: [60, 100], color: C.green }],
      threshold: { line: { color: 'white', width: 3 }, value: scorePct },
    },
  }], { ...LAYOUT_BASE, margin: { l: 20, r: 20, t: 60, b: 10 } }, { responsive: true, displayModeBar: false });

  const pos = sent.pos_pct || 0, neg = sent.neg_pct || 0, neu = 100 - pos - neg;
  Plotly.newPlot('sent-bar', [
    { type: 'bar', name: 'Positive', x: ['Sentiment'], y: [pos], marker: { color: C.green } },
    { type: 'bar', name: 'Neutral',  x: ['Sentiment'], y: [neu], marker: { color: C.yellow } },
    { type: 'bar', name: 'Negative', x: ['Sentiment'], y: [neg], marker: { color: C.red } },
  ], { ...LAYOUT_BASE, barmode: 'stack', title: `News Split · ${sent.method}`, xaxis: AXIS, yaxis: AXIS, legend: { bgcolor: C.bg } },
  { responsive: true, displayModeBar: false });

  const badgeClass = { Positive: 'badge-pos', Negative: 'badge-neg', Neutral: 'badge-neu' };
  document.getElementById('news-list').innerHTML = data.news.map((item, i) => {
    const s = data.sentiments[i] || { label: 'Neutral', score: 0 };
    return `<div class="news-card">
      <div class="news-meta">
        <span class="sentiment-badge ${badgeClass[s.label] || 'badge-neu'}">${s.label}</span>
        <span class="news-publisher">${item.publisher}</span>
      </div>
      <div class="news-title"><a href="${item.link}" target="_blank" rel="noopener">${item.title}</a></div>
      <div class="news-date">${item.published}</div>
    </div>`;
  }).join('');
}

// ─── Fundamentals ─────────────────────────────────────────────────
function renderFundamentals(data) {
  if (!data || !data.stocks || data.stocks.length === 0) {
    document.getElementById('fund-body').innerHTML = '<p style="color:var(--sub)">No fundamental data available.</p>';
    return;
  }
  document.getElementById('fund-body').innerHTML = data.stocks.map(f => `
    <div class="fund-card">
      <h3>${f.name}</h3>
      <div class="fund-grid">
        ${fundItem('Market Cap',     f.market_cap)}
        ${fundItem('P/E Ratio',      f.pe_ratio)}
        ${fundItem('P/B Ratio',      f.pb_ratio)}
        ${fundItem('EPS',            f.eps)}
        ${fundItem('ROE',            f.roe)}
        ${fundItem('Div Yield',      f.div_yield)}
        ${fundItem('Revenue Growth', f.revenue_growth)}
        ${fundItem('Profit Margin',  f.profit_margin)}
        ${fundItem('D/E Ratio',      f.debt_to_equity)}
        ${fundItem('Current Ratio',  f.current_ratio)}
        ${fundItem('Sector',         f.sector)}
        ${fundItem('Employees',      f.employees)}
      </div>
      <p class="fund-desc">${f.description || ''}</p>
    </div>`).join('');
}

function fundItem(label, value) {
  return `<div class="fund-item">
    <div class="fi-label">${label}</div>
    <div class="fi-val">${value || '—'}</div>
  </div>`;
}

// ─── Backtest ─────────────────────────────────────────────────────
function drawBacktest() {
  if (!chartData || !chartData.backtest) return;
  const bt     = chartData.backtest;
  const equity = [100];
  (bt.trades || []).forEach(t => equity.push(equity.at(-1) * (1 + t.return_pct / 100)));

  Plotly.newPlot('bt-chart', [{
    type: 'scatter', y: equity, mode: 'lines+markers',
    line: { color: C.accent, width: 2 },
    fill: 'tozeroy', fillcolor: 'rgba(59,130,246,.07)',
    name: 'Portfolio Value',
  }], {
    ...LAYOUT_BASE,
    title: `${chartData.name} — Strategy Equity Curve (Start = ₹100)`,
    xaxis: { ...AXIS, title: 'Trade #' },
    yaxis: { ...AXIS, title: 'Portfolio Value' },
    shapes: [{ type: 'line', x0: 0, x1: equity.length - 1, y0: 100, y1: 100, line: { color: C.sub, dash: 'dash' } }],
  }, { responsive: true, displayModeBar: false });

  const retColor = bt.total_return >= 0 ? C.green : C.red;
  document.getElementById('bt-stats').innerHTML = `
    <div class="bt-stats-card">
      <h3>📊 Strategy Results</h3>
      <div class="bt-stat-row">
        <span class="bt-stat-label">Total Return</span>
        <span style="color:${retColor};font-weight:800;">${bt.total_return >= 0 ? '+' : ''}${bt.total_return.toFixed(2)}%</span>
      </div>
      <div class="bt-stat-row">
        <span class="bt-stat-label">Win Rate</span>
        <span>${bt.win_rate}%</span>
      </div>
      <div class="bt-stat-row">
        <span class="bt-stat-label">Total Trades</span>
        <span>${bt.num_trades}</span>
      </div>
      <div class="bt-stat-row">
        <span class="bt-stat-label">Avg Return</span>
        <span>${bt.avg_return >= 0 ? '+' : ''}${bt.avg_return.toFixed(2)}%</span>
      </div>
      <div class="bt-stat-row">
        <span class="bt-stat-label">Strategy</span>
        <span style="color:var(--sub);font-size:.78rem;">RSI + MACD crossover</span>
      </div>
    </div>`;
}

// ─── Event Listeners ──────────────────────────────────────────────
document.getElementById('symbol-dd').addEventListener('change', function () {
  currentSymbol = this.value;
  fetchData();
  fetchNews();
});
document.getElementById('period-dd').addEventListener('change', function () {
  currentPeriod = this.value;
  fetchData();
});
document.getElementById('refresh-btn').addEventListener('click', () => {
  fetchData();
  fetchHeatmap();
  fetchNews();
});
document.getElementById('train-btn').addEventListener('click', runML);

// ─── Initial load ─────────────────────────────────────────────────
(async function init() {
  await populateSymbols();
  await fetchData();
})();
