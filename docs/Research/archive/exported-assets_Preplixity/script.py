
html_content = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Options Trade Education Panel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ─── TOKENS ─────────────────────────────────────────── */
:root {
  --bg:        #0D1117;
  --surface:   #161B22;
  --surface2:  #1C2128;
  --surface3:  #21262D;
  --border:    rgba(255,255,255,0.08);
  --border2:   rgba(255,255,255,0.13);

  --green:     #00C896;
  --green-dim: rgba(0,200,150,0.15);
  --green-glow:rgba(0,200,150,0.25);
  --red:       #FF4444;
  --red-dim:   rgba(255,68,68,0.15);
  --amber:     #F59E0B;
  --amber-dim: rgba(245,158,11,0.15);
  --blue:      #3B82F6;
  --blue-dim:  rgba(59,130,246,0.15);

  --text:      #E6EDF3;
  --muted:     #8B949E;
  --faint:     #484F58;

  --mono: 'JetBrains Mono', monospace;
  --sans: 'Inter', sans-serif;

  --r-sm: 4px; --r-md: 8px; --r-lg: 12px; --r-xl: 16px;

  --text-xs:   0.6875rem;
  --text-sm:   0.75rem;
  --text-base: 0.875rem;
  --text-lg:   1rem;
  --text-xl:   1.125rem;
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;background:#000}
body{
  font-family:var(--sans);
  font-size:var(--text-base);
  color:var(--text);
  background:var(--bg);
  min-height:100vh;
  padding:24px 16px 48px;
  display:flex;
  flex-direction:column;
  align-items:center;
}

/* ─── LAYOUT ─────────────────────────────────────────── */
.page-header{
  width:100%;max-width:620px;
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:20px;
}
.logo{display:flex;align-items:center;gap:8px;font-weight:600;font-size:var(--text-lg);letter-spacing:-0.02em}
.logo svg{color:var(--green)}
.trade-badge{
  background:var(--surface2);border:1px solid var(--border2);
  border-radius:var(--r-lg);padding:6px 12px;
  font-family:var(--mono);font-size:var(--text-xs);
  color:var(--muted);display:flex;gap:8px;align-items:center;
}
.trade-badge .sym{color:var(--text);font-weight:600}
.trade-badge .strat{color:var(--red);font-weight:500}

.panel-wrap{width:100%;max-width:600px;display:flex;flex-direction:column;gap:12px}

/* ─── TAB NAV ────────────────────────────────────────── */
.tab-nav{
  display:flex;gap:2px;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--r-lg);
  padding:4px;
}
.tab-btn{
  flex:1;padding:8px 4px;
  background:none;border:none;
  color:var(--muted);font-family:var(--sans);font-size:var(--text-xs);font-weight:500;
  border-radius:var(--r-md);cursor:pointer;
  transition:all 160ms ease;
  display:flex;flex-direction:column;align-items:center;gap:3px;
  line-height:1.2;
}
.tab-btn .t-num{
  width:18px;height:18px;
  border-radius:50%;
  background:var(--surface3);
  display:flex;align-items:center;justify-content:center;
  font-size:9px;font-weight:600;font-family:var(--mono);
  transition:all 160ms ease;
}
.tab-btn.active{color:var(--text);background:var(--surface2)}
.tab-btn.active .t-num{background:var(--green);color:#000}
.tab-btn:hover:not(.active){color:var(--text);background:rgba(255,255,255,0.04)}

/* ─── PANEL CARD ─────────────────────────────────────── */
.panel{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--r-xl);
  overflow:hidden;
  display:none;
}
.panel.active{display:block}

.panel-head{
  padding:14px 18px 12px;
  border-bottom:1px solid var(--border);
  display:flex;align-items:flex-start;justify-content:space-between;gap:8px;
}
.panel-head-left{display:flex;flex-direction:column;gap:3px}
.panel-title{font-size:var(--text-base);font-weight:600;color:var(--text)}
.panel-sub{font-size:var(--text-xs);color:var(--muted)}
.gate-badge{
  font-size:10px;font-weight:600;font-family:var(--mono);
  padding:3px 8px;border-radius:var(--r-sm);
  white-space:nowrap;flex-shrink:0;margin-top:2px;
}
.gate-pass{background:var(--green-dim);color:var(--green);border:1px solid rgba(0,200,150,0.3)}
.gate-fail{background:var(--red-dim);color:var(--red);border:1px solid rgba(255,68,68,0.3)}
.gate-warn{background:var(--amber-dim);color:var(--amber);border:1px solid rgba(245,158,11,0.3)}
.gate-info{background:var(--blue-dim);color:var(--blue);border:1px solid rgba(59,130,246,0.3)}

.panel-body{padding:16px 18px}

/* ─── CONCEPT 1: MAX PROFIT / LOSS ──────────────────── */
.rr-section{display:flex;flex-direction:column;gap:10px}
.rr-label-row{display:flex;justify-content:space-between;align-items:center}
.rr-label{font-size:var(--text-xs);color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;font-weight:500}
.rr-bar-track{
  height:28px;background:var(--surface3);border-radius:var(--r-md);overflow:hidden;
  display:flex;position:relative;
}
.rr-bar-profit{
  background:var(--green);display:flex;align-items:center;justify-content:flex-end;
  padding-right:8px;font-size:var(--text-xs);font-weight:600;color:#000;
  border-radius:var(--r-md) 0 0 var(--r-md);
  transition:width 600ms cubic-bezier(0.16,1,0.3,1);
}
.rr-bar-loss{
  background:var(--red);display:flex;align-items:center;justify-content:flex-start;
  padding-left:8px;font-size:var(--text-xs);font-weight:600;color:#fff;
  border-radius:0 var(--r-md) var(--r-md) 0;
  transition:width 600ms cubic-bezier(0.16,1,0.3,1);
}
.rr-stats{display:flex;gap:8px}
.rr-stat{
  flex:1;background:var(--surface2);border-radius:var(--r-md);padding:10px 12px;
  border:1px solid var(--border);
}
.rr-stat-val{font-family:var(--mono);font-size:var(--text-xl);font-weight:600;line-height:1}
.rr-stat-lbl{font-size:10px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:0.05em}
.rr-stat.profit .rr-stat-val{color:var(--green)}
.rr-stat.loss .rr-stat-val{color:var(--red)}
.rr-ratio{
  background:var(--surface2);border-radius:var(--r-md);padding:8px 12px;
  border:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
}
.rr-ratio-label{font-size:var(--text-xs);color:var(--muted)}
.rr-ratio-val{font-family:var(--mono);font-size:var(--text-sm);font-weight:600;color:var(--amber)}

/* ─── NUMBER LINE ─────────────────────────────────────── */
.nl-wrap{position:relative;width:100%;height:110px;margin:8px 0 4px}

.nl-zones{
  position:absolute;top:0;left:0;right:0;height:44px;
  border-radius:var(--r-md);overflow:hidden;display:flex;
}
.nl-zone{display:flex;align-items:center;justify-content:center}
.nl-zone-label{font-size:9px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;opacity:0.7}

.nl-axis{
  position:absolute;top:52px;left:0;right:0;height:2px;
  background:var(--border2);border-radius:2px;
}

/* price markers */
.nl-marker{
  position:absolute;top:44px;
  display:flex;flex-direction:column;align-items:center;
  transform:translateX(-50%);
  pointer-events:none;
}
.nl-marker-line{width:2px;height:16px;border-radius:2px}
.nl-marker-dot{
  width:10px;height:10px;border-radius:50%;
  border:2px solid var(--bg);
  position:absolute;top:3px;
  transform:translateX(-50%);
  left:50%;
}
.nl-marker-label{
  font-family:var(--mono);font-size:9px;font-weight:600;
  margin-top:4px;white-space:nowrap;
}
.nl-marker-sublabel{
  font-size:8px;color:var(--muted);
  white-space:nowrap;margin-top:1px;
}

/* zone labels below line */
.nl-zone-labels{
  position:absolute;top:78px;left:0;right:0;
  display:flex;justify-content:space-between;
  padding:0 4px;
}
.nl-zlabel{font-size:9px;color:var(--muted)}

/* p/l zone overlay */
.nl-pnl-track{
  position:absolute;top:22px;left:0;right:0;height:22px;
  border-radius:var(--r-sm);overflow:hidden;display:flex;
}

/* ─── CONCEPT 3: BREAKEVEN EXPLAINER ─────────────────── */
.be-formula{
  background:var(--surface2);border-radius:var(--r-md);padding:12px 14px;
  border:1px solid var(--border);
  font-family:var(--mono);font-size:var(--text-sm);
  display:flex;flex-direction:column;gap:6px;
}
.be-row{display:flex;justify-content:space-between;align-items:center}
.be-key{color:var(--muted);font-size:var(--text-xs)}
.be-val{font-weight:600}
.be-divider{border:none;border-top:1px solid var(--border);margin:2px 0}
.be-result{color:var(--amber);font-size:var(--text-base);font-weight:700}

.expiry-chart{margin-top:12px}
.ec-label{font-size:var(--text-xs);color:var(--muted);margin-bottom:6px}
.ec-grid{
  position:relative;height:60px;
  background:var(--surface2);border-radius:var(--r-md);
  border:1px solid var(--border);overflow:hidden;
}
.ec-profit-zone{
  position:absolute;top:0;bottom:0;left:0;
  background:var(--green-dim);
  border-right:1px dashed rgba(0,200,150,0.4);
}
.ec-loss-zone{
  position:absolute;top:0;bottom:0;right:0;
  background:var(--red-dim);
}
.ec-be-line{
  position:absolute;top:0;bottom:0;width:2px;
  background:var(--amber);opacity:0.7;
}
.ec-label-inner{
  position:absolute;bottom:6px;
  font-size:9px;font-family:var(--mono);font-weight:600;
}

/* ─── CONCEPT 4: EVENTS / DTE ────────────────────────── */
.dte-track{
  position:relative;height:32px;
  background:var(--surface3);border-radius:var(--r-md);overflow:hidden;
  margin:8px 0;
}
.dte-optimal{
  position:absolute;top:0;bottom:0;
  background:var(--green-dim);
  border-left:1px solid rgba(0,200,150,0.4);
  border-right:1px solid rgba(0,200,150,0.4);
}
.dte-current{
  position:absolute;top:0;bottom:0;width:3px;
  background:var(--blue);border-radius:2px;
}
.dte-label{
  position:absolute;top:50%;transform:translateY(-50%);
  font-size:9px;font-family:var(--mono);color:var(--muted);
}

.event-list{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.event-item{
  display:flex;align-items:center;gap:8px;
  background:var(--surface2);border-radius:var(--r-md);
  padding:8px 12px;border:1px solid var(--border);
}
.event-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.event-text{font-size:var(--text-xs);flex:1}
.event-dte{font-family:var(--mono);font-size:var(--text-xs);color:var(--muted)}
.event-flag{font-size:10px;font-weight:600}

/* ─── GATES TABLE ─────────────────────────────────────── */
.gates-list{display:flex;flex-direction:column;gap:8px}
.gate-row{
  background:var(--surface2);border-radius:var(--r-lg);
  border:1px solid var(--border);overflow:hidden;
}
.gate-header{
  display:flex;align-items:center;gap:10px;padding:10px 14px;
  cursor:pointer;
  transition:background 150ms ease;
}
.gate-header:hover{background:rgba(255,255,255,0.03)}
.gate-num{
  width:22px;height:22px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:700;font-family:var(--mono);
  flex-shrink:0;
}
.gate-name{font-size:var(--text-sm);font-weight:600;flex:1}
.gate-status-pill{
  font-size:10px;font-weight:600;font-family:var(--mono);
  padding:2px 8px;border-radius:var(--r-sm);
  flex-shrink:0;
}
.gate-chevron{color:var(--muted);transition:transform 200ms ease;flex-shrink:0}
.gate-row.open .gate-chevron{transform:rotate(180deg)}

.gate-detail{
  display:none;padding:0 14px 12px;
  border-top:1px solid var(--border);
}
.gate-row.open .gate-detail{display:block;padding-top:10px}
.gate-q{font-size:var(--text-xs);color:var(--muted);margin-bottom:8px;font-style:italic}

.gate-answers{display:flex;flex-direction:column;gap:6px}
.gate-answer{
  display:flex;gap:8px;align-items:flex-start;
  font-size:var(--text-xs);
}
.gate-answer-icon{
  width:16px;height:16px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:8px;font-weight:700;flex-shrink:0;margin-top:1px;
}
.icon-pass{background:var(--green-dim);color:var(--green)}
.icon-fail{background:var(--red-dim);color:var(--red)}
.icon-why{background:var(--amber-dim);color:var(--amber)}

.gate-meter{
  height:6px;background:var(--surface3);border-radius:var(--r-sm);
  overflow:hidden;margin:8px 0;
}
.gate-meter-fill{height:100%;border-radius:var(--r-sm);transition:width 500ms ease}

/* ─── CONCEPT 5: LIQUIDITY ──────────────────────────── */
.liq-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px}
.liq-stat{
  background:var(--surface2);border-radius:var(--r-md);padding:10px;
  border:1px solid var(--border);text-align:center;
}
.liq-val{font-family:var(--mono);font-size:var(--text-base);font-weight:600}
.liq-key{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;margin-top:3px}
.spread-bar-wrap{margin-top:4px}
.spread-bar-track{
  height:20px;background:var(--surface3);border-radius:var(--r-sm);
  overflow:hidden;position:relative;
}
.spread-bar-fill{
  height:100%;border-radius:var(--r-sm);
  display:flex;align-items:center;padding-left:8px;
  font-size:9px;font-weight:600;
}

/* ─── SCROLL & MISC ──────────────────────────────────── */
.info-row{
  display:flex;gap:6px;align-items:flex-start;
  background:var(--surface2);border-radius:var(--r-md);padding:9px 12px;
  border:1px solid var(--border);margin-top:8px;
  font-size:var(--text-xs);
}
.info-icon{color:var(--blue);flex-shrink:0;margin-top:1px}
.info-text{color:var(--muted);line-height:1.5}
.info-text strong{color:var(--text)}

.section-label{
  font-size:10px;text-transform:uppercase;letter-spacing:0.08em;
  font-weight:600;color:var(--faint);margin-bottom:6px;
}

.divider{border:none;border-top:1px solid var(--border);margin:14px 0}

/* ─── PUT TOGGLE ─────────────────────────────────────── */
.toggle-row{display:flex;gap:6px;margin-bottom:12px}
.toggle-btn{
  flex:1;padding:7px;font-size:var(--text-xs);font-weight:600;
  border-radius:var(--r-md);border:1px solid var(--border);
  background:none;color:var(--muted);cursor:pointer;
  transition:all 150ms ease;
}
.toggle-btn.active-call{background:var(--red-dim);color:var(--red);border-color:rgba(255,68,68,0.3)}
.toggle-btn.active-put{background:var(--blue-dim);color:var(--blue);border-color:rgba(59,130,246,0.3)}

/* ─── PROGRESS DOTS ─────────────────────────────────── */
.progress-row{display:flex;align-items:center;justify-content:center;gap:6px;margin-top:8px}
.p-dot{width:6px;height:6px;border-radius:50%;background:var(--surface3);transition:all 200ms ease;cursor:pointer}
.p-dot.active{width:18px;border-radius:3px;background:var(--green)}

</style>
</head>
<body>

<div class="page-header">
  <div class="logo">
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <rect x="1" y="1" width="20" height="20" rx="5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M6 14 L10 8 L14 11 L18 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="18" cy="6" r="1.5" fill="currentColor"/>
    </svg>
    OptionsIQ
  </div>
  <div class="trade-badge">
    <span class="sym">XLF</span>
    <span>$52.16</span>
    <span class="strat">BEAR CALL SPREAD</span>
  </div>
</div>

<!-- TAB NAV -->
<div class="panel-wrap">
<nav class="tab-nav" role="tablist">
  <button class="tab-btn active" onclick="switchTab(0)" role="tab">
    <span class="t-num">1</span>Risk
  </button>
  <button class="tab-btn" onclick="switchTab(1)" role="tab">
    <span class="t-num">2</span>Zones
  </button>
  <button class="tab-btn" onclick="switchTab(2)" role="tab">
    <span class="t-num">3</span>B/E
  </button>
  <button class="tab-btn" onclick="switchTab(3)" role="tab">
    <span class="t-num">4</span>Timing
  </button>
  <button class="tab-btn" onclick="switchTab(4)" role="tab">
    <span class="t-num">5</span>Gates
  </button>
</nav>

<!-- ══════════════════════════════════════════
     PANEL 1 — RISK/REWARD
════════════════════════════════════════════ -->
<section class="panel active" id="panel-0">
  <div class="panel-head">
    <div class="panel-head-left">
      <div class="panel-title">Max Profit vs Max Loss</div>
      <div class="panel-sub">Your best case and worst case — defined before you place the trade</div>
    </div>
    <div class="gate-badge gate-pass">RISK DEFINED ✓</div>
  </div>
  <div class="panel-body">
    <div class="rr-section">

      <div class="section-label">Proportional Risk / Reward Bar</div>
      <div class="rr-bar-track">
        <!-- profit = $21 / total $100 = 21%; loss = $79 -->
        <div class="rr-bar-profit" style="width:21%">$21</div>
        <div class="rr-bar-loss" style="width:79%">$79</div>
      </div>

      <div class="rr-stats">
        <div class="rr-stat profit">
          <div class="rr-stat-val">+$21</div>
          <div class="rr-stat-lbl">Max Profit</div>
        </div>
        <div class="rr-stat loss">
          <div class="rr-stat-val">−$79</div>
          <div class="rr-stat-lbl">Max Loss</div>
        </div>
        <div class="rr-stat" style="border-color:rgba(245,158,11,0.3)">
          <div class="rr-stat-val" style="color:var(--amber)">$100</div>
          <div class="rr-stat-lbl">Width × 100</div>
        </div>
      </div>

      <div class="rr-ratio">
        <span class="rr-ratio-label">Risk : Reward Ratio</span>
        <span class="rr-ratio-val">3.76 : 1 — You risk $3.76 to make $1</span>
      </div>

      <div class="divider"></div>

      <div class="section-label">How it works</div>

      <div style="display:flex;flex-direction:column;gap:6px">
        <div class="info-row">
          <div class="info-icon">▼</div>
          <div class="info-text"><strong>SELL 54C @ $0.27</strong> — you collect $27 premium. This is your income.</div>
        </div>
        <div class="info-row" style="border-color:rgba(59,130,246,0.2)">
          <div class="info-icon" style="color:var(--blue)">▲</div>
          <div class="info-text"><strong>BUY 55C @ $0.06</strong> — you pay $6 as a hedge. This caps your max loss.</div>
        </div>
        <div class="info-row" style="border-color:rgba(0,200,150,0.2)">
          <div class="info-icon" style="color:var(--green)">$</div>
          <div class="info-text"><strong>Net credit = $0.21 × 100 = $21</strong> — collected upfront. You keep this if XLF stays below $54.</div>
        </div>
        <div class="info-row" style="border-color:rgba(255,68,68,0.2)">
          <div class="info-icon" style="color:var(--red)">!</div>
          <div class="info-text"><strong>Max loss = ($1.00 − $0.21) × 100 = $79</strong> — if XLF closes above $55 at expiry.</div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     PANEL 2 — STRIKE ZONE VISUALIZATION
════════════════════════════════════════════ -->
<section class="panel" id="panel-1">
  <div class="panel-head">
    <div class="panel-head-left">
      <div class="panel-title">Strike Zone Visualization</div>
      <div class="panel-sub">Where each price level sits — and what it means for your trade</div>
    </div>
    <div class="gate-badge gate-warn">OTM +3.5%</div>
  </div>
  <div class="panel-body">

    <div class="toggle-row">
      <button class="toggle-btn active-call" id="btn-call" onclick="setOptionType('call')">CALL Spread (Bear)</button>
      <button class="toggle-btn" id="btn-put" onclick="setOptionType('put')">PUT Spread (Bull)</button>
    </div>

    <!-- Number line container -->
    <div id="nl-container">
      <!-- Rendered by JS -->
    </div>

    <div class="divider"></div>

    <div id="strike-legend" style="display:flex;flex-direction:column;gap:6px"></div>

    <div class="info-row" style="margin-top:10px">
      <div class="info-icon">💡</div>
      <div class="info-text" id="otm-tip">For a <strong>bear call spread</strong>, you WANT the stock price to stay <strong>below your short strike ($54)</strong>. ITM = bad for this trade.</div>
    </div>

  </div>
</section>

<!-- ══════════════════════════════════════════
     PANEL 3 — BREAKEVEN
════════════════════════════════════════════ -->
<section class="panel" id="panel-2">
  <div class="panel-head">
    <div class="panel-head-left">
      <div class="panel-title">Breakeven Point</div>
      <div class="panel-sub">The exact price where you neither profit nor lose at expiry</div>
    </div>
    <div class="gate-badge gate-warn">BE = $54.21</div>
  </div>
  <div class="panel-body">

    <div class="section-label">Breakeven Formula</div>
    <div class="be-formula">
      <div class="be-row">
        <span class="be-key">Short Strike</span>
        <span class="be-val">$54.00</span>
      </div>
      <div class="be-row">
        <span class="be-key">+ Net Credit Received</span>
        <span class="be-val" style="color:var(--green)">+$0.21</span>
      </div>
      <hr class="be-divider">
      <div class="be-row">
        <span class="be-key">Breakeven Price</span>
        <span class="be-val be-result">$54.21</span>
      </div>
    </div>

    <div class="divider"></div>
    <div class="section-label">Price-at-Expiry P/L Map</div>

    <!-- SVG payoff diagram -->
    <div style="position:relative;background:var(--surface2);border-radius:var(--r-lg);border:1px solid var(--border);padding:10px 14px 8px;overflow:hidden">
      <svg width="100%" height="100" viewBox="0 0 540 100" preserveAspectRatio="none" id="payoff-svg">
        <!-- Background zones -->
        <!-- Profit zone: left of BE -->
        <rect x="0" y="0" width="245" height="100" fill="rgba(0,200,150,0.08)" rx="0"/>
        <!-- Loss zone: right of BE -->
        <rect x="245" y="0" width="295" height="100" fill="rgba(255,68,68,0.08)" rx="0"/>

        <!-- Axis -->
        <line x1="0" y1="62" x2="540" y2="62" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>

        <!-- Payoff line: flat at +21 left of short strike (~50px = $50), slopes down to 0 at BE (~245px=$54.21), continues to -79 at long strike (~380px=$55), then flat -->
        <!-- Map: $50=0px, $56=540px => 90px per dollar -->
        <!-- $52=left, $50=0, short=54→360, BE=54.21→378.9, long=55→450, $56=540 -->
        <!-- Rescaled: visible range $51–$56 = 540px → 108px/$ -->
        <!-- $51=0, $52=108, $53=216, $54=324, $54.21=346.7, $55=432, $56=540 -->
        <!-- Profit zone top = y20, breakeven y=62, max loss y=92 -->
        <polyline
          points="0,20 324,20 346.7,62 432,92 540,92"
          fill="none"
          stroke="rgba(255,255,255,0.5)"
          stroke-width="1.5"
          stroke-dasharray="4 3"
        />
        <!-- Solid profit/loss colored line -->
        <polyline
          points="0,20 324,20"
          fill="none" stroke="#00C896" stroke-width="2.5" stroke-linecap="round"
        />
        <polyline
          points="324,20 346.7,62 432,92 540,92"
          fill="none" stroke="#FF4444" stroke-width="2.5" stroke-linecap="round"
        />

        <!-- Current price marker $52.16 = 108+(0.16*108)=125.3 -->
        <line x1="125.3" y1="0" x2="125.3" y2="100" stroke="#3B82F6" stroke-width="1" stroke-dasharray="3 2"/>
        <text x="128" y="12" fill="#3B82F6" font-size="8" font-family="JetBrains Mono,monospace" font-weight="600">$52.16</text>

        <!-- BE marker -->
        <line x1="346.7" y1="0" x2="346.7" y2="100" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="4 2"/>
        <text x="349" y="22" fill="#F59E0B" font-size="8" font-family="JetBrains Mono,monospace" font-weight="600">BE $54.21</text>

        <!-- Short strike $54 -->
        <circle cx="324" cy="20" r="4" fill="#00C896"/>
        <text x="305" y="14" fill="#00C896" font-size="7.5" font-family="JetBrains Mono,monospace">SELL 54C</text>

        <!-- Long strike $55 -->
        <circle cx="432" cy="92" r="4" fill="#FF4444"/>
        <text x="435" y="87" fill="#FF4444" font-size="7.5" font-family="JetBrains Mono,monospace">BUY 55C</text>

        <!-- X-axis price labels -->
        <text x="0" y="100" fill="#484F58" font-size="7.5" font-family="JetBrains Mono,monospace">$51</text>
        <text x="101" y="100" fill="#484F58" font-size="7.5" font-family="JetBrains Mono,monospace">$52</text>
        <text x="209" y="100" fill="#484F58" font-size="7.5" font-family="JetBrains Mono,monospace">$53</text>
        <text x="317" y="100" fill="#484F58" font-size="7.5" font-family="JetBrains Mono,monospace">$54</text>
        <text x="425" y="100" fill="#484F58" font-size="7.5" font-family="JetBrains Mono,monospace">$55</text>
        <text x="523" y="100" fill="#484F58" font-size="7.5" font-family="JetBrains Mono,monospace">$56</text>

        <!-- P/L labels -->
        <text x="4" y="32" fill="#00C896" font-size="8" font-family="JetBrains Mono,monospace" font-weight="600">+$21 MAX</text>
        <text x="448" y="92" fill="#FF4444" font-size="8" font-family="JetBrains Mono,monospace" font-weight="600">−$79 MAX</text>
      </svg>
    </div>

    <div class="info-row" style="margin-top:10px">
      <div class="info-icon">💡</div>
      <div class="info-text">XLF is currently <strong>$1.84 below</strong> your short strike and <strong>$2.05 below</strong> breakeven. The stock needs to rise <strong>3.9%</strong> before you start losing money.</div>
    </div>

  </div>
</section>

<!-- ══════════════════════════════════════════
     PANEL 4 — TIMING: DTE + EVENTS
════════════════════════════════════════════ -->
<section class="panel" id="panel-3">
  <div class="panel-head">
    <div class="panel-head-left">
      <div class="panel-title">Timing: DTE & Events</div>
      <div class="panel-sub">Days to expiry and what scheduled events could move the stock</div>
    </div>
    <div class="gate-badge gate-fail">EVENT RISK ⚠</div>
  </div>
  <div class="panel-body">

    <div class="section-label">Days to Expiry (DTE) — Optimal Seller Range: 21–45 days</div>

    <!-- DTE bar -->
    <div class="dte-track">
      <!-- optimal zone: 21-45 out of 0-90 range -->
      <!-- 0=0% 90=100%, 21=23.3%, 45=50% -->
      <div class="dte-optimal" style="left:23.3%;right:50%"></div>
      <!-- current DTE = 31 days = 34.4% -->
      <div class="dte-current" style="left:34.4%"></div>
      <span class="dte-label" style="left:4px">0</span>
      <span class="dte-label" style="left:23%">21</span>
      <span class="dte-label" style="left:48%">45</span>
      <span class="dte-label" style="right:4px">90</span>
    </div>

    <div style="display:flex;gap:8px;margin-bottom:10px">
      <div class="rr-stat" style="flex:1;border-color:rgba(59,130,246,0.3)">
        <div class="rr-stat-val" style="color:var(--blue)">31</div>
        <div class="rr-stat-lbl">Current DTE</div>
      </div>
      <div class="rr-stat" style="flex:1;border-color:rgba(0,200,150,0.3)">
        <div class="rr-stat-val" style="color:var(--green)">21–45</div>
        <div class="rr-stat-lbl">Ideal for Sellers</div>
      </div>
      <div class="rr-stat" style="flex:1;border-color:rgba(0,200,150,0.2)">
        <div class="rr-stat-val" style="color:var(--green)">✓ IN RANGE</div>
        <div class="rr-stat-lbl">DTE Status</div>
      </div>
    </div>

    <div class="info-row">
      <div class="info-icon">⏱</div>
      <div class="info-text">Time decay (theta) works <strong>in your favor</strong> as a credit seller. Every day XLF stays below $54.21, the option loses value and you profit.</div>
    </div>

    <div class="divider"></div>
    <div class="section-label">Scheduled Events Within Expiry Window</div>

    <div class="event-list">
      <div class="event-item" style="border-color:rgba(255,68,68,0.3)">
        <div class="event-dot" style="background:var(--red)"></div>
        <div class="event-text"><strong>XLF Earnings</strong> — Financial sector ETF rebalance + bank earnings season</div>
        <div class="event-dte">DTE 18</div>
        <div class="event-flag" style="color:var(--red)">HIGH</div>
      </div>
      <div class="event-item" style="border-color:rgba(245,158,11,0.3)">
        <div class="event-dot" style="background:var(--amber)"></div>
        <div class="event-text"><strong>FOMC Meeting</strong> — Fed rate decision (banks sensitive to rate changes)</div>
        <div class="event-dte">DTE 24</div>
        <div class="event-flag" style="color:var(--amber)">MED</div>
      </div>
      <div class="event-item" style="border-color:rgba(59,130,246,0.2)">
        <div class="event-dot" style="background:var(--blue)"></div>
        <div class="event-text"><strong>CPI Data Release</strong> — Inflation print, affects financials indirectly</div>
        <div class="event-dte">DTE 7</div>
        <div class="event-flag" style="color:var(--blue)">LOW</div>
      </div>
    </div>

    <div class="info-row" style="margin-top:10px;border-color:rgba(255,68,68,0.2)">
      <div class="info-icon" style="color:var(--red)">⚠</div>
      <div class="info-text"><strong>Warning:</strong> Earnings events inside your expiry window can cause large gap moves. IV spikes before the event inflate premium, then collapses after — a double-edged sword for credit sellers.</div>
    </div>

  </div>
</section>

<!-- ══════════════════════════════════════════
     PANEL 5 — 7 SAFETY GATES
════════════════════════════════════════════ -->
<section class="panel" id="panel-4">
  <div class="panel-head">
    <div class="panel-head-left">
      <div class="panel-title">7 Safety Gates</div>
      <div class="panel-sub">All gates must pass before placing the trade</div>
    </div>
    <div class="gate-badge gate-warn">5/7 PASS</div>
  </div>
  <div class="panel-body">

    <!-- Gate score bar -->
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;margin-bottom:5px">
        <span style="font-size:var(--text-xs);color:var(--muted)">Trade Readiness Score</span>
        <span style="font-family:var(--mono);font-size:var(--text-xs);color:var(--amber)">5 / 7 gates pass</span>
      </div>
      <div class="gate-meter">
        <div class="gate-meter-fill" style="width:71.4%;background:linear-gradient(90deg,var(--green),var(--amber))"></div>
      </div>
    </div>

    <div class="gates-list" id="gates-list">
    <!-- Rendered by JS -->
    </div>

  </div>
</section>

<!-- progress dots -->
<div class="progress-row" id="progress-dots">
  <div class="p-dot active" onclick="switchTab(0)"></div>
  <div class="p-dot" onclick="switchTab(1)"></div>
  <div class="p-dot" onclick="switchTab(2)"></div>
  <div class="p-dot" onclick="switchTab(3)"></div>
  <div class="p-dot" onclick="switchTab(4)"></div>
</div>

</div><!-- end panel-wrap -->

<script>
/* ─── TAB SWITCHING ──────────────────── */
let currentTab = 0;
function switchTab(idx) {
  document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
  document.querySelectorAll('.panel').forEach((p,i) => p.classList.toggle('active', i===idx));
  document.querySelectorAll('.p-dot').forEach((d,i) => d.classList.toggle('active', i===idx));
  currentTab = idx;
  if(idx === 1) renderNumberLine('call');
}

/* ─── NUMBER LINE ──────────────────── */
let optionType = 'call';
function setOptionType(type) {
  optionType = type;
  document.getElementById('btn-call').className = 'toggle-btn' + (type==='call' ? ' active-call' : '');
  document.getElementById('btn-put').className = 'toggle-btn' + (type==='put' ? ' active-put' : '');
  renderNumberLine(type);
}

function renderNumberLine(type) {
  const container = document.getElementById('nl-container');
  const legend = document.getElementById('strike-legend');
  const tip = document.getElementById('otm-tip');

  // Price points for CALL spread
  // Range: $50 to $57 = 7 pts
  // Current: $52.16, Short: $54, Long: $55, BE: $54.21
  const rangeMin = 50, rangeMax = 57, rangeSpan = rangeMax - rangeMin;
  const pct = v => ((v - rangeMin) / rangeSpan * 100).toFixed(2) + '%';
  const pctN = v => (v - rangeMin) / rangeSpan * 100;

  if (type === 'call') {
    // CALL: ITM = below current price, OTM = above current price (for calls)
    // Wait — for CALL options:
    // ITM call: strike < current price
    // ATM call: strike ≈ current price
    // OTM call: strike > current price
    container.innerHTML = `
    <div style="position:relative;width:100%;height:120px;margin:8px 0 4px">
      <!-- ZONE BAR -->
      <div style="position:absolute;top:0;left:0;right:0;height:36px;border-radius:8px;overflow:hidden;display:flex">
        <!-- ITM zone: $50 to $52.16 = 30.9% -->
        <div style="width:${pctN(52.16)}%;background:rgba(255,68,68,0.22);display:flex;align-items:center;justify-content:center">
          <span style="font-size:9px;font-weight:600;color:#FF4444;letter-spacing:0.06em;text-transform:uppercase">ITM</span>
        </div>
        <!-- ATM zone: tiny band around $52.16 -->
        <div style="width:3%;background:rgba(245,158,11,0.3);display:flex;align-items:center;justify-content:center">
          <span style="font-size:8px;font-weight:600;color:#F59E0B">ATM</span>
        </div>
        <!-- OTM zone: rest -->
        <div style="flex:1;background:rgba(0,200,150,0.15);display:flex;align-items:center;justify-content:center">
          <span style="font-size:9px;font-weight:600;color:#00C896;letter-spacing:0.06em;text-transform:uppercase">OTM → 54C &amp; 55C live here</span>
        </div>
      </div>

      <!-- P/L Zone bar below zones -->
      <div style="position:absolute;top:42px;left:0;right:0;height:18px;border-radius:4px;overflow:hidden;display:flex">
        <!-- profit zone: everything left of BE ($54.21 = 60.1%) -->
        <div style="width:${pctN(54.21)}%;background:rgba(0,200,150,0.2);display:flex;align-items:center;padding-left:6px">
          <span style="font-size:8px;color:#00C896;font-weight:600">PROFIT ZONE ✓</span>
        </div>
        <!-- loss zone -->
        <div style="flex:1;background:rgba(255,68,68,0.2);display:flex;align-items:center;justify-content:flex-end;padding-right:6px">
          <span style="font-size:8px;color:#FF4444;font-weight:600">LOSS ZONE ✗</span>
        </div>
      </div>

      <!-- AXIS LINE -->
      <div style="position:absolute;top:68px;left:0;right:0;height:2px;background:rgba(255,255,255,0.12);border-radius:2px"></div>

      <!-- MARKERS: Current price $52.16 -->
      <div style="position:absolute;left:${pct(52.16)};top:60px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center">
        <div style="width:2px;height:16px;background:#3B82F6;border-radius:2px"></div>
        <div style="width:10px;height:10px;border-radius:50%;background:#3B82F6;border:2px solid #0D1117;margin-top:-5px;margin-left:0"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:8.5px;font-weight:600;color:#3B82F6;margin-top:4px;white-space:nowrap">$52.16</span>
        <span style="font-size:7.5px;color:#8B949E;white-space:nowrap">Current</span>
      </div>

      <!-- Short strike $54 -->
      <div style="position:absolute;left:${pct(54)};top:60px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center">
        <div style="width:2px;height:16px;background:#FF4444;border-radius:2px"></div>
        <div style="width:10px;height:10px;border-radius:50%;background:#FF4444;border:2px solid #0D1117;margin-top:-5px"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:8.5px;font-weight:600;color:#FF4444;margin-top:4px;white-space:nowrap">$54.00</span>
        <span style="font-size:7.5px;color:#8B949E;white-space:nowrap">SELL 54C</span>
      </div>

      <!-- BE $54.21 -->
      <div style="position:absolute;left:${pct(54.21)};top:60px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center">
        <div style="width:1.5px;height:16px;background:#F59E0B;border-radius:2px"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:7.5px;font-weight:600;color:#F59E0B;margin-top:5px;white-space:nowrap">BE $54.21</span>
      </div>

      <!-- Long strike $55 -->
      <div style="position:absolute;left:${pct(55)};top:60px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center">
        <div style="width:2px;height:16px;background:#00C896;border-radius:2px"></div>
        <div style="width:10px;height:10px;border-radius:50%;background:#00C896;border:2px solid #0D1117;margin-top:-5px"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:8.5px;font-weight:600;color:#00C896;margin-top:4px;white-space:nowrap">$55.00</span>
        <span style="font-size:7.5px;color:#8B949E;white-space:nowrap">BUY 55C</span>
      </div>

      <!-- $50 and $57 labels -->
      <div style="position:absolute;left:0;top:78px;font-size:8px;font-family:'JetBrains Mono',monospace;color:#484F58">$50</div>
      <div style="position:absolute;right:0;top:78px;font-family:'JetBrains Mono',monospace;font-size:8px;color:#484F58">$57</div>
    </div>`;

    legend.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
      <div class="info-row" style="margin-top:0"><div style="color:#FF4444;font-weight:700;font-size:11px;flex-shrink:0">ITM</div><div class="info-text">Strike &lt; Stock Price. Call has intrinsic value. <strong>Bad for this trade.</strong></div></div>
      <div class="info-row" style="margin-top:0"><div style="color:#00C896;font-weight:700;font-size:11px;flex-shrink:0">OTM</div><div class="info-text">Strike &gt; Stock Price. No intrinsic value yet. <strong>Good for this trade.</strong></div></div>
    </div>`;

    tip.innerHTML = `For a <strong>bear call spread</strong>, you WANT the stock to stay <strong>below your short strike ($54)</strong>. Both calls expire worthless and you keep the $21 credit.`;
  } else {
    // PUT options: ITM/OTM flip
    // PUT ITM: strike > current price (put has intrinsic value)
    // PUT OTM: strike < current price
    container.innerHTML = `
    <div style="position:relative;width:100%;height:120px;margin:8px 0 4px">
      <div style="position:absolute;top:0;left:0;right:0;height:36px;border-radius:8px;overflow:hidden;display:flex">
        <!-- OTM zone for puts: below current price -->
        <div style="width:${pctN(52.16)}%;background:rgba(0,200,150,0.15);display:flex;align-items:center;justify-content:center">
          <span style="font-size:9px;font-weight:600;color:#00C896;letter-spacing:0.06em;text-transform:uppercase">OTM puts here</span>
        </div>
        <div style="width:3%;background:rgba(245,158,11,0.3);display:flex;align-items:center;justify-content:center">
          <span style="font-size:8px;font-weight:600;color:#F59E0B">ATM</span>
        </div>
        <!-- ITM zone for puts: above current price -->
        <div style="flex:1;background:rgba(255,68,68,0.22);display:flex;align-items:center;justify-content:center">
          <span style="font-size:9px;font-weight:600;color:#FF4444;letter-spacing:0.06em;text-transform:uppercase">ITM puts here ⬅ flipped!</span>
        </div>
      </div>

      <div style="position:absolute;top:42px;left:0;right:0;height:18px;border-radius:4px;overflow:hidden;display:flex">
        <div style="flex:1;background:rgba(255,68,68,0.2);display:flex;align-items:center;padding-left:6px">
          <span style="font-size:8px;color:#FF4444;font-weight:600">LOSS ZONE (put spread)</span>
        </div>
        <div style="width:${(rangeMax - 54.21)/rangeSpan*100}%;background:rgba(0,200,150,0.2);display:flex;align-items:center;justify-content:flex-end;padding-right:6px">
          <span style="font-size:8px;color:#00C896;font-weight:600">PROFIT ZONE</span>
        </div>
      </div>

      <div style="position:absolute;top:68px;left:0;right:0;height:2px;background:rgba(255,255,255,0.12);border-radius:2px"></div>

      <div style="position:absolute;left:${pct(52.16)};top:60px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center">
        <div style="width:2px;height:16px;background:#3B82F6;border-radius:2px"></div>
        <div style="width:10px;height:10px;border-radius:50%;background:#3B82F6;border:2px solid #0D1117;margin-top:-5px"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:8.5px;font-weight:600;color:#3B82F6;margin-top:4px;white-space:nowrap">$52.16</span>
        <span style="font-size:7.5px;color:#8B949E;white-space:nowrap">Current</span>
      </div>

      <div style="position:absolute;left:0;top:78px;font-size:8px;font-family:'JetBrains Mono',monospace;color:#484F58">$50</div>
      <div style="position:absolute;right:0;top:78px;font-family:'JetBrains Mono',monospace;font-size:8px;color:#484F58">$57</div>
    </div>`;

    legend.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
      <div class="info-row" style="margin-top:0"><div style="color:#00C896;font-weight:700;font-size:11px;flex-shrink:0">OTM</div><div class="info-text">PUT strike &lt; Stock Price. No intrinsic value. Cheaper premium.</div></div>
      <div class="info-row" style="margin-top:0"><div style="color:#FF4444;font-weight:700;font-size:11px;flex-shrink:0">ITM</div><div class="info-text">PUT strike &gt; Stock Price. Has intrinsic value. Higher premium.</div></div>
    </div>`;

    tip.innerHTML = `⬅ <strong>Notice the flip!</strong> For PUT options, ITM/OTM zones are reversed vs. calls. A $54 PUT would be <strong>ITM</strong> (since $54 &gt; $52.16 current price).`;
  }
}

/* ─── GATES DATA & RENDER ───────────── */
const gates = [
  {
    num:1, name:'IV Rank', status:'PASS', color:'green',
    question:'Are options cheap or expensive right now?',
    pass:'IV Rank is 68% — options are expensive, which is great for sellers collecting premium.',
    fail:'IV Rank below 30% means options are cheap and you would collect very little premium for the risk taken.',
    why:'Selling expensive options gives you more credit upfront and a larger buffer before you lose money.',
    meter:68, meterColor:'var(--green)',
    detail:'IVR: 68 / 100'
  },
  {
    num:2, name:'Strike OTM %', status:'PASS', color:'green',
    question:'Is the sold strike far enough away from the current price?',
    pass:'54C is 3.5% above current price $52.16 — a comfortable buffer against random noise.',
    fail:'A strike less than 2% OTM is dangerously close; a normal daily move could push the stock past it.',
    why:'The further OTM your short strike, the more room the stock has to move before you start losing money.',
    meter:70, meterColor:'var(--green)',
    detail:'OTM: +$1.84 (3.5%)'
  },
  {
    num:3, name:'DTE', status:'PASS', color:'green',
    question:'Is there the right amount of time left until this option expires?',
    pass:'31 days to expiry is squarely in the 21-45 day sweet spot for credit spread sellers.',
    fail:'Under 21 days gives too little premium; over 45 days exposes you to more potential stock movement.',
    why:'Time decay (theta) accelerates in the last 30 days — you profit fastest when selling in this window.',
    meter:80, meterColor:'var(--green)',
    detail:'DTE: 31 days'
  },
  {
    num:4, name:'Events', status:'FAIL', color:'red',
    question:'Does anything big happen before this option expires?',
    pass:'No earnings or FOMC within the window — the stock is unlikely to gap violently against your position.',
    fail:'An earnings report falls on DTE 18 — inside your expiry window. This could cause a large gap move.',
    why:'A single gap-up past your short strike can turn a max-profit scenario into a max-loss overnight.',
    meter:30, meterColor:'var(--red)',
    detail:'Earnings DTE 18 ⚠'
  },
  {
    num:5, name:'Liquidity', status:'PASS', color:'green',
    question:'Can you easily get in and out of this trade at a fair price?',
    pass:'Bid-ask spread is $0.03 (tight), open interest is 4,200, and daily volume is 850 — highly liquid.',
    fail:'A wide bid-ask spread means you pay a large hidden cost just to enter and exit the trade.',
    why:'Illiquid options can cost you 10-30% of your expected profit just in entry/exit slippage.',
    meter:85, meterColor:'var(--green)',
    detail:'Spread: $0.03 | OI: 4.2k'
  },
  {
    num:6, name:'Market Regime', status:'PASS', color:'green',
    question:'Is the overall market in a trending or choppy environment?',
    pass:'SPY is above its 200-day SMA and 5-day return is -0.4% — slight pullback in an uptrend, neutral-bearish bias suits this trade.',
    fail:'If SPY is below its 200-day SMA in a downtrend, volatility spikes and mean-reverting strategies struggle.',
    why:'Options strategies work better when the market regime matches your trade directional bias.',
    meter:65, meterColor:'var(--amber)',
    detail:'SPY above 200SMA ✓'
  },
  {
    num:7, name:'Risk Defined', status:'PASS', color:'green',
    question:'Is the absolute most you can lose known before entering the trade?',
    pass:'This is a spread — your max loss is capped at $79 no matter how high XLF goes.',
    fail:'A naked short call has unlimited theoretical loss; a single large move can wipe out your entire account.',
    why:'Defined-risk trades let you size positions correctly so no single trade can cause catastrophic loss.',
    meter:100, meterColor:'var(--green)',
    detail:'Max Loss: $79 ✓'
  }
];

function renderGates() {
  const list = document.getElementById('gates-list');
  list.innerHTML = gates.map((g,i) => `
  <div class="gate-row" id="gate-row-${i}">
    <div class="gate-header" onclick="toggleGate(${i})">
      <div class="gate-num" style="background:${g.color==='green'?'var(--green-dim)':g.color==='red'?'var(--red-dim)':'var(--amber-dim)'};color:${g.color==='green'?'var(--green)':g.color==='red'?'var(--red)':'var(--amber)'}">${g.num}</div>
      <div class="gate-name">${g.name}</div>
      <span style="font-size:var(--text-xs);color:var(--muted);font-family:var(--mono)">${g.detail}</span>
      <div class="gate-status-pill ${g.status==='PASS'?'gate-pass':g.status==='FAIL'?'gate-fail':'gate-warn'}">${g.status}</div>
      <svg class="gate-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
    </div>
    <div class="gate-detail">
      <div class="gate-q">❓ ${g.question}</div>
      <div class="gate-meter"><div class="gate-meter-fill" style="width:${g.meter}%;background:${g.meterColor}"></div></div>
      <div class="gate-answers">
        <div class="gate-answer">
          <div class="gate-answer-icon icon-pass">✓</div>
          <div><strong style="color:var(--green)">PASS:</strong> ${g.pass}</div>
        </div>
        <div class="gate-answer">
          <div class="gate-answer-icon icon-fail">✗</div>
          <div><strong style="color:var(--red)">FAIL:</strong> ${g.fail}</div>
        </div>
        <div class="gate-answer">
          <div class="gate-answer-icon icon-why">$</div>
          <div><strong style="color:var(--amber)">WHY:</strong> ${g.why}</div>
        </div>
      </div>
    </div>
  </div>`).join('');
}

function toggleGate(i) {
  const row = document.getElementById('gate-row-'+i);
  row.classList.toggle('open');
}

// Init
renderGates();
renderNumberLine('call');
</script>
</body>
</html>"""

with open('/root/options-edu-panel.html', 'w') as f:
    f.write(html_content)
print("Written:", len(html_content), "chars")
