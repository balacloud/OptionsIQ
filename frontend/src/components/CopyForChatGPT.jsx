import { useState } from 'react';

const DIR_LABELS = {
  buy_call: 'Buy Call (bullish)',
  sell_call: 'Sell Call (neutral/bearish)',
  buy_put: 'Buy Put (bearish)',
  sell_put: 'Sell Put / Bull Put Spread (neutral/bullish)',
};

function buildPrompt(ticker, direction, data) {
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  const v = data.verdict || {};
  const gates = data.gates || [];
  const strat = data.top_strategies?.[0];
  const ivr = data.ivr_data;
  const pnl = data.pnl_table?.scenarios || [];

  // Gate summary
  const gateLines = gates.map(g => {
    const icon = g.status === 'pass' ? '✅' : g.status === 'warn' ? '⚠️' : '❌';
    const val = g.computed_value || g.value || '';
    return `  ${icon} ${g.name}${val ? ': ' + val : ''}${g.reason ? ' — ' + g.reason : ''}`;
  }).join('\n');

  // Strategy summary
  let stratLines = 'No strategy generated.';
  if (strat) {
    stratLines = [
      `  Type: ${strat.label || strat.strategy_type}`,
      strat.strike     ? `  Strike: $${strat.strike}` : null,
      strat.expiry     ? `  Expiry: ${strat.expiry} (${strat.dte} DTE)` : null,
      strat.premium    ? `  Premium: $${strat.premium?.toFixed(2)} per share ($${((strat.premium || 0) * 100).toFixed(0)} per contract)` : null,
      strat.delta      ? `  Delta: ${strat.delta?.toFixed(3)}` : null,
      strat.theta      ? `  Theta: ${strat.theta?.toFixed(3)} per day` : null,
      strat.iv         ? `  IV: ${(strat.iv * 100).toFixed(1)}%` : null,
    ].filter(Boolean).join('\n');
  }

  // IVR summary
  let ivrLines = 'IV data not available.';
  if (ivr) {
    ivrLines = [
      `  Current IV: ${ivr.current_iv?.toFixed(1)}%`,
      `  IVR (percentile rank): ${ivr.ivr_pct?.toFixed(1)}% ${ivr.ivr_pct < 25 ? '(cheap — good to buy)' : ivr.ivr_pct > 60 ? '(expensive — consider selling)' : '(moderate)'}`,
      `  HV20: ${ivr.hv_20?.toFixed(1)}%`,
    ].join('\n');
  }

  // P&L table (top 4 rows)
  let pnlLines = 'P&L table not available.';
  if (pnl.length > 0) {
    const rows = pnl.slice(0, 6).map(r => {
      const move = r.stock_move_pct != null ? `${r.stock_move_pct > 0 ? '+' : ''}${r.stock_move_pct}%` : '';
      const pnlVal = r.pnl_c1 !== '--' && r.pnl_c1 != null ? `$${r.pnl_c1} (${r.pnl_pct_c1}%)` : '--';
      return `  ${r.scenario_label}: stock ${move} → P&L ${pnlVal}`;
    });
    pnlLines = rows.join('\n');
  }

  return `Today is ${today}. I'm analyzing an options trade and need your help stress-testing it.

═══════════════════════════════════════
TRADE SETUP (from OptionsIQ analysis)
═══════════════════════════════════════
Ticker: ${ticker}
Direction: ${DIR_LABELS[direction] || direction}
Underlying price: $${data.underlying_price?.toFixed(2) || 'N/A'}
Verdict: ${v.color?.toUpperCase() || 'N/A'} — ${v.score_label || ''} (${v.pass || 0}/${(v.pass || 0) + (v.warn || 0) + (v.fail || 0)} gates passed)
Verdict headline: "${v.headline || ''}"

GATE SCORES:
${gateLines || '  No gate data.'}

TOP STRATEGY (Rank 1):
${stratLines}

IV DATA:
${ivrLines}

P&L SCENARIOS (Rank 1 strategy):
${pnlLines}

═══════════════════════════════════════
WHAT I NEED FROM YOU
═══════════════════════════════════════

1. **3 STRONGEST BEAR CASES** — reasons this trade fails even though the system says GO.
   Be specific. Not "markets can go down." Name the actual risk for ${ticker} right now.

2. **WHAT WOULD INVALIDATE THIS SETUP**
   - If ${ticker} closes below $X, the thesis is broken
   - If [EVENT] happens before expiry, exit immediately

3. **IS THE STRUCTURE RIGHT?**
   - Given this setup, is ${strat?.label || 'this strategy'} the right instrument?
   - Any adjustment worth considering? (different DTE, different strike, spread instead of naked?)

4. **FINAL VERDICT: TAKE THE TRADE OR WAIT?**
   One sentence with the main reason.`;
}

export default function CopyForChatGPT({ ticker, direction, data }) {
  const [copied, setCopied] = useState(false);

  if (!data?.verdict || !data?.top_strategies?.length) return null;

  const handleCopy = async () => {
    const prompt = buildPrompt(ticker, direction, data);
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // fallback for older browsers
      const ta = document.createElement('textarea');
      ta.value = prompt;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="copy-chatgpt-wrap">
      <button
        className={`copy-chatgpt-btn${copied ? ' copied' : ''}`}
        onClick={handleCopy}
        title="Copies a pre-filled stress-test prompt with your full analysis — paste directly into ChatGPT"
      >
        {copied ? '✓ Copied to clipboard' : '⎘ Copy for ChatGPT — Stress Test'}
      </button>
      {copied && (
        <div className="copy-chatgpt-hint">
          Paste into ChatGPT → GPT-4o will give you the 3 strongest bear cases for this trade.
        </div>
      )}
    </div>
  );
}
