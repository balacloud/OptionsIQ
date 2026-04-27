import { useState } from 'react';

const ETF_SECTOR = {
  XLK:  'Technology',
  XLY:  'Consumer Discretionary',
  XLP:  'Consumer Staples',
  XLV:  'Health Care',
  XLF:  'Financials',
  XLI:  'Industrials',
  XLE:  'Energy',
  XLU:  'Utilities',
  XLB:  'Materials',
  XLRE: 'Real Estate',
  XLC:  'Communication Services',
  MDY:  'Mid-Cap S&P 400',
  IWM:  'Small-Cap Russell 2000',
  SCHB: 'Broad Market',
  QQQ:  'Nasdaq 100',
  TQQQ: '3x Nasdaq (leveraged)',
};

const DIR_LABELS = {
  buy_call:  'buy_call (bullish)',
  sell_call: 'sell_call (neutral/bearish)',
  buy_put:   'buy_put (bearish)',
  sell_put:  'sell_put (neutral/bullish)',
};

function todayStr() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });
}

function buildPrompt1() {
  return `Today is ${todayStr()}. I trade options on sector ETFs (16 ETFs: XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, SCHB, QQQ, TQQQ).

Give me a morning regime check in this exact format:

**MACRO BACKDROP (today)**
- VIX level and what it means (calm/elevated/fear)
- Is SPY above or below its 200-day SMA?
- Any overnight news that changes the market tone?

**EVENTS IN NEXT 21 DAYS (date + what it is)**
- Next FOMC meeting or Fed speaker
- Next CPI / NFP / major economic release
- Any Treasury auction or debt ceiling risk

**VERDICT: Is this a good week to BUY options premium or SELL premium?**
(one sentence, yes/no with brief reason)`;
}

function buildPrompt2(ticker, direction) {
  const sector = ETF_SECTOR[ticker] || ticker;
  const dirLabel = DIR_LABELS[direction] || direction;
  return `Today is ${todayStr()}. I'm considering a ${dirLabel} trade on ${ticker} (${sector} sector ETF).

Give me a focused catalyst check in this format:

**WHAT'S MOVING THIS SECTOR THIS WEEK**
- Top 1-3 news items or data releases affecting this sector right now

**EARNINGS RISK**
- Are any major companies inside ${ticker} reporting earnings in the next 21 days? List them with dates.

**ANALYST SENTIMENT**
- Any recent upgrades, downgrades, or price target changes on ${ticker} itself or its top 5 holdings this week?

**IV CONTEXT**
- Is there a specific reason IV would be elevated or suppressed in ${ticker} right now?

**ONE-LINE VERDICT**
- Is the sector narrative aligned or against a ${direction.includes('call') ? 'bullish' : 'bearish'} options trade?`;
}

function CopyButton({ getText, label }) {
  const [state, setState] = useState('idle'); // idle | copied

  const handleCopy = async () => {
    const text = getText();
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;opacity:0';
      document.body.appendChild(ta);
      ta.focus(); ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setState('copied');
    setTimeout(() => setState('idle'), 2500);
  };

  return (
    <button
      className={`pre-prompt-copy-btn${state === 'copied' ? ' copied' : ''}`}
      onClick={handleCopy}
    >
      {state === 'copied' ? '✓ Copied' : label}
    </button>
  );
}

export default function PreAnalysisPrompts({ ticker, direction }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="pre-prompts-wrap">
      <button
        className={`pre-prompts-toggle${open ? ' open' : ''}`}
        onClick={() => setOpen(o => !o)}
      >
        <span className="pre-prompts-icon">🔍</span>
        <span>Pre-Analysis Research</span>
        <span className="pre-prompts-hint">Run Perplexity prompts before analyzing</span>
        <span className="pre-prompts-chevron">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="pre-prompts-body">
          {/* Prompt 1 */}
          <div className="pre-prompt-block">
            <div className="pre-prompt-header">
              <span className="pre-prompt-label">Prompt 1 — Macro Regime Check</span>
              <span className="pre-prompt-tool">Perplexity</span>
            </div>
            <pre className="pre-prompt-text">{buildPrompt1()}</pre>
            <CopyButton getText={buildPrompt1} label="⎘ Copy Prompt 1" />
          </div>

          {/* Prompt 2 */}
          <div className="pre-prompt-block">
            <div className="pre-prompt-header">
              <span className="pre-prompt-label">Prompt 2 — Sector Catalyst Check</span>
              <span className="pre-prompt-tool">Perplexity</span>
            </div>
            <pre className="pre-prompt-text">{buildPrompt2(ticker, direction)}</pre>
            <CopyButton
              getText={() => buildPrompt2(ticker, direction)}
              label="⎘ Copy Prompt 2"
            />
          </div>

          <div className="pre-prompts-footer">
            After Perplexity → Run Analysis → use "Copy for ChatGPT" for stress test
          </div>
        </div>
      )}
    </div>
  );
}
