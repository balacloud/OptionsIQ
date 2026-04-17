import { useState } from 'react';

// Gate knowledge base: question + pass/fail answers + why it matters
const GATE_KB = {
  ivr: {
    category: 'pricing',
    question: 'Is IV cheap enough to buy?',
    passAnswer: 'YES — IV is relatively low, so options are cheaper to buy.',
    failAnswer: 'NO — IV is high, meaning options are expensive to buy right now.',
    why: 'When you buy options, high IV means you overpay — any move must be large enough to overcome that premium.',
  },
  ivr_seller: {
    category: 'pricing',
    question: 'Is premium expensive enough to sell?',
    passAnswer: 'YES — IV is elevated, so you collect richer premium for selling.',
    failAnswer: 'NO — IV is too low, meaning you\'re selling options cheaply for the risk you\'re taking.',
    why: 'When you sell options, high IV means you get paid more. One bad move can wipe out several wins if premium is thin.',
  },
  hv_iv: {
    category: 'pricing',
    question: 'Are options fairly priced vs recent movement?',
    passAnswer: 'YES — Implied volatility is in line with how much the ETF has actually moved.',
    failAnswer: 'NO — Options are mispriced relative to real movement. Proceed with caution.',
    why: 'If options are priced much higher than the ETF actually moves, sellers benefit. If lower, buyers get an edge.',
  },
  strike_otm: {
    category: 'pricing',
    question: 'Is the strike safely away from the current price?',
    passAnswer: 'YES — Your strike gives the ETF room to move before this trade gets into trouble.',
    failAnswer: 'NO — The strike is too close to the current price. Even a normal move could push you into a loss.',
    why: 'More distance means more breathing room. A wider margin of safety increases your chance of keeping the full credit.',
  },
  theta_burn: {
    category: 'pricing',
    question: 'Will time decay help or hurt this trade?',
    passAnswer: 'YES — Time decay is working in your favor, eroding the value of the options you sold.',
    failAnswer: 'NO — Time decay is working against you, eating into your premium too fast.',
    why: 'For sellers, theta is profit. For buyers, theta is a cost. Getting the timing right matters.',
  },
  dte: {
    category: 'pricing',
    question: 'Is the expiry date in the right window for buying?',
    passAnswer: 'YES — Expiry is in the 45–90 day window where buyers get good delta without too much decay.',
    failAnswer: 'NO — Expiry is too close (fast decay) or too far (capital tied up too long).',
    why: 'Buyers need enough time for the move to happen, but not so much that they overpay for time value.',
  },
  dte_seller: {
    category: 'pricing',
    question: 'Is the expiry date in the right window for selling?',
    passAnswer: 'YES — Expiry is in the 21–45 day window where time decay accelerates most for sellers.',
    failAnswer: 'NO — Expiry is outside the optimal seller window. Theta decay may be too slow or expiry too risky.',
    why: 'Time decay accelerates in the final 21–45 days — that\'s when sellers collect premium fastest.',
  },
  events: {
    category: 'market',
    question: 'Are there any surprise events before expiry?',
    passAnswer: 'NO events — No earnings, Fed meetings, or major events fall before your expiry date.',
    failAnswer: 'YES — A major event (earnings, FOMC) falls before expiry. This could cause a large gap move.',
    why: 'One earnings surprise can cause a 5–10% overnight gap. That turns a calm trade into a max-loss trade instantly.',
  },
  liquidity: {
    category: 'risk',
    question: 'Can I get in and out of this trade easily?',
    passAnswer: 'YES — Bid-ask spread and open interest look healthy. You\'ll get fair fills entering and exiting.',
    failAnswer: 'NO — Wide spreads or low volume means you\'ll overpay to enter and lose more trying to exit.',
    why: 'Illiquid options quietly cost money. Poor fills can damage returns even when your market view is right.',
  },
  market_regime: {
    category: 'market',
    question: 'Is the broad market trend supporting this trade?',
    passAnswer: 'YES — SPY\'s overall trend is aligned with your trade direction.',
    failAnswer: 'NO — The broad market is moving against your trade direction. Fighting the trend raises risk.',
    why: 'Trading with the market trend improves your odds. Selling calls in a strong rally risks assignment.',
  },
  market_regime_seller: {
    category: 'market',
    question: 'Is the broad market calm enough to sell premium?',
    passAnswer: 'YES — Market conditions support selling premium. Trend is moderate and IV is elevated.',
    failAnswer: 'NO — Market is too volatile or trending too strongly. Selling into this increases assignment risk.',
    why: 'Selling in the direction of a strong trend is risky. A fast-moving market can blow through your strikes.',
  },
  risk_defined: {
    category: 'risk',
    question: 'Is my maximum possible loss capped?',
    passAnswer: 'YES — This is a defined-risk spread. Your max loss is known before you place the trade.',
    failAnswer: 'NO — This strategy has unlimited loss potential. Consider adding a protective leg.',
    why: 'A defined max loss prevents one bad trade from being catastrophic. It\'s the most important safety feature.',
  },
  position_size: {
    category: 'risk',
    question: 'Can I afford this trade within my risk limits?',
    passAnswer: 'YES — This trade stays within the recommended 1–2% account risk per position.',
    failAnswer: 'NO — Position size exceeds safe limits for your account. Reduce size or skip this trade.',
    why: 'Risking too much on one trade can cripple your account. No single trade should threaten your overall capital.',
  },
  max_loss: {
    category: 'risk',
    question: 'Is total potential loss within acceptable limits?',
    passAnswer: 'YES — Max loss is within acceptable bounds for this account size.',
    failAnswer: 'NO — Potential loss is too large relative to account size. Adjust or skip.',
    why: 'Even with defined risk, if max loss is too large as a percentage of your account, one bad trade hurts too much.',
  },
};

const CATEGORY_ORDER = ['market', 'pricing', 'risk'];
const CATEGORY_LABELS = {
  market: 'Market Conditions',
  pricing: 'Option Pricing',
  risk: 'Risk Management',
};

function getKb(gateId) {
  return GATE_KB[gateId] || {
    category: 'risk',
    question: `Gate: ${gateId}`,
    passAnswer: 'This gate passed.',
    failAnswer: 'This gate failed.',
    why: 'This safety check protects your trade.',
  };
}

function statusIcon(status) {
  if (status === 'pass') return '✓';
  if (status === 'warn') return '!';
  return '✗';
}

function GateRow({ gate }) {
  const [open, setOpen] = useState(gate.status !== 'pass');
  const kb = getKb(gate.id);

  return (
    <div className={`ge-gate-row ge-gate-${gate.status}`}>
      <button className="ge-gate-header" onClick={() => setOpen(o => !o)}>
        <span className={`ge-gate-icon ge-icon-${gate.status}`}>{statusIcon(gate.status)}</span>
        <span className="ge-gate-question">{kb.question}</span>
        <span className="ge-gate-value">{gate.computed_value ?? ''}</span>
        <span className={`ge-chevron ${open ? 'ge-chevron-open' : ''}`}>▼</span>
      </button>

      {open && (
        <div className="ge-gate-detail">
          <div className={`ge-answer ge-answer-${gate.status}`}>
            <span className={`ge-answer-icon ge-icon-${gate.status}`}>{statusIcon(gate.status)}</span>
            <span>{gate.status === 'pass' ? kb.passAnswer : gate.status === 'warn' ? kb.passAnswer : kb.failAnswer}</span>
          </div>

          {gate.reason && (
            <div className="ge-gate-reason">
              <span className="ge-reason-data">Data: {gate.reason}</span>
            </div>
          )}

          <div className="ge-why">
            <span className="ge-why-icon">$</span>
            <span>{kb.why}</span>
          </div>

          {/* Gate meter bar */}
          <div className="ge-meter">
            <div
              className={`ge-meter-fill ge-meter-${gate.status}`}
              style={{ width: gate.status === 'pass' ? '85%' : gate.status === 'warn' ? '45%' : '15%' }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default function GateExplainer({ gates, direction }) {
  const anyFail = gates.some(g => g.status === 'fail');
  const anyWarn = gates.some(g => g.status === 'warn');
  const [open, setOpen] = useState(anyFail || anyWarn);

  if (gates.length === 0) {
    return (
      <div className="gate-explainer">
        <div className="ge-header" onClick={() => setOpen(o => !o)}>
          <div className="ge-header-left">
            <span className="ge-title">Safety Checks</span>
            <span className="ge-subtitle">Run analysis to see gate results</span>
          </div>
          <span className={`ge-chevron ${open ? 'ge-chevron-open' : ''}`}>▼</span>
        </div>
      </div>
    );
  }

  const pass  = gates.filter(g => g.status === 'pass').length;
  const warn  = gates.filter(g => g.status === 'warn').length;
  const fail  = gates.filter(g => g.status === 'fail').length;
  const total = gates.length;
  const readinessPct = (pass / total) * 100;

  // Group gates by category
  const grouped = {};
  CATEGORY_ORDER.forEach(cat => { grouped[cat] = []; });
  gates.forEach(gate => {
    const kb = getKb(gate.id);
    const cat = kb.category;
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(gate);
  });

  // Dot summary
  const dots = gates.map(g => (
    <span
      key={g.id}
      className={`gdot ${g.status === 'pass' ? 'pass' : g.status === 'warn' ? 'warn' : 'fail'}`}
      title={`${g.name}: ${g.status}${g.reason ? ' — ' + g.reason : ''}`}
    />
  ));

  return (
    <div className="gate-explainer">
      <div className="ge-header" onClick={() => setOpen(o => !o)}>
        <div className="ge-header-left">
          <div className="ge-title-row">
            <span className="ge-title">Safety Checks</span>
            <div className="gate-dot-row">{dots}</div>
          </div>
          <div className="ge-score-row">
            <span className={`ge-score ${fail > 0 ? 'ge-score-fail' : warn > 0 ? 'ge-score-warn' : 'ge-score-pass'}`}>
              {pass}/{total} passed
              {warn > 0 && <span className="text-amber"> · {warn} caution</span>}
              {fail > 0 && <span className="text-red"> · {fail} failed</span>}
            </span>
          </div>

          {/* Readiness bar */}
          <div className="ge-readiness-bar">
            <div className="ge-readiness-fill" style={{ width: `${readinessPct}%`, background: fail > 0 ? 'var(--red)' : warn > 0 ? 'var(--amber)' : 'var(--green)' }} />
          </div>
        </div>
        <span className={`ge-chevron ${open ? 'ge-chevron-open' : ''}`}>▼</span>
      </div>

      {open && (
        <div className="ge-body">
          {CATEGORY_ORDER.map(cat => {
            const catGates = grouped[cat];
            if (!catGates || catGates.length === 0) return null;
            return (
              <div key={cat} className="ge-category">
                <div className="ge-category-label">{CATEGORY_LABELS[cat]}</div>
                <div className="ge-gates-list">
                  {catGates.map(gate => (
                    <GateRow key={gate.id} gate={gate} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
