import { useState } from 'react';

// ── Lesson 1: Strikes ──────────────────────────────────────────────────────
function LessonStrikes() {
  const [stockPrice, setStockPrice] = useState(180);
  const [optionType, setOptionType] = useState('call');

  const strikes = [160, 170, 180, 190, 200];
  const isCall = optionType === 'call';

  function moneyness(strike) {
    if (isCall) {
      if (strike < stockPrice - 2) return 'itm';
      if (strike > stockPrice + 2) return 'otm';
      return 'atm';
    } else {
      if (strike > stockPrice + 2) return 'itm';
      if (strike < stockPrice - 2) return 'otm';
      return 'atm';
    }
  }

  const moneynessInfo = {
    itm: {
      label: 'In The Money',
      abbr: 'ITM',
      color: 'green',
      desc: isCall
        ? `Already has $${(stockPrice - 160).toFixed(0)}+ of real value. More expensive but moves most with stock.`
        : `Already has $${(170 - stockPrice).toFixed(0)}+ of real value. More expensive but moves most with stock.`,
      delta: isCall ? '~0.68' : '~-0.68',
      why: 'OptionsIQ picks ITM for buyers: intrinsic value buffers time decay. You pay more upfront but the option holds its value better.',
    },
    atm: {
      label: 'At The Money',
      abbr: 'ATM',
      color: 'amber',
      desc: 'Right at the current price — no intrinsic value yet. Cheapest but needs the stock to move to be profitable.',
      delta: isCall ? '~0.50' : '~-0.50',
      why: 'ATM options have the highest time decay. Good for short-term speculation but risky to hold.',
    },
    otm: {
      label: 'Out of The Money',
      abbr: 'OTM',
      color: 'red',
      desc: `Needs the stock to move ${isCall ? 'up' : 'down'} before this option has any real value. Cheapest but most likely to expire worthless.`,
      delta: isCall ? '~0.30' : '~-0.30',
      why: 'OptionsIQ picks OTM for sellers: you collect premium and time works for you. The stock must move significantly to hurt you.',
    },
  };

  return (
    <div className="learn-lesson">
      <div className="learn-lesson-title">Understanding Strikes</div>
      <div className="learn-lesson-intro">
        A "strike" is the price where your option kicks in. Where it sits relative to the current stock price determines its type — and how it behaves.
      </div>

      <div className="learn-controls">
        <div className="learn-control-group">
          <label className="learn-control-label">Stock Price: ${stockPrice}</label>
          <input
            type="range"
            min={155}
            max={205}
            step={1}
            value={stockPrice}
            onChange={e => setStockPrice(Number(e.target.value))}
            className="learn-slider"
          />
          <div className="learn-slider-labels">
            <span>$155</span><span>$205</span>
          </div>
        </div>
        <div className="learn-toggle-row">
          <button
            className={`learn-toggle-btn ${isCall ? 'learn-toggle-active-call' : ''}`}
            onClick={() => setOptionType('call')}
          >
            CALL Option
          </button>
          <button
            className={`learn-toggle-btn ${!isCall ? 'learn-toggle-active-put' : ''}`}
            onClick={() => setOptionType('put')}
          >
            PUT Option
          </button>
        </div>
      </div>

      {/* Number line visualization */}
      <div className="learn-numberline">
        <div className="learn-nl-label-row">
          {isCall ? (
            <>
              <span className="learn-zone-label text-red">← OTM (no value)</span>
              <span className="learn-zone-label text-green">ITM (has value) →</span>
            </>
          ) : (
            <>
              <span className="learn-zone-label text-green">← ITM (has value)</span>
              <span className="learn-zone-label text-red">OTM (no value) →</span>
            </>
          )}
        </div>
        <div className="learn-nl-strikes">
          {strikes.map(s => {
            const mn = moneyness(s);
            return (
              <div key={s} className={`learn-nl-strike learn-nl-strike-${mn}`}>
                <div className="learn-nl-strike-badge">{mn.toUpperCase()}</div>
                <div className="learn-nl-strike-price">${s}</div>
                {s === stockPrice && <div className="learn-nl-current">← Current Price</div>}
              </div>
            );
          })}
        </div>
        <div className="learn-nl-price-marker">
          Current price: <strong>${stockPrice}</strong>
        </div>
      </div>

      {/* Cards for each type */}
      <div className="learn-moneyness-cards">
        {['itm', 'atm', 'otm'].map(mn => {
          const info = moneynessInfo[mn];
          return (
            <div key={mn} className={`learn-mn-card learn-mn-${mn}`}>
              <div className="learn-mn-header">
                <span className="learn-mn-abbr">{info.abbr}</span>
                <span className="learn-mn-label">{info.label}</span>
                <span className="learn-mn-delta">Delta {info.delta}</span>
              </div>
              <div className="learn-mn-desc">{info.desc}</div>
              <div className="learn-mn-why">{info.why}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Lesson 2: Directions ───────────────────────────────────────────────────
function LessonDirections() {
  const [selected, setSelected] = useState(null);

  const directions = [
    {
      id: 'buy_call',
      icon: '▲',
      name: 'Buy Call',
      view: 'Strongly Bullish',
      color: 'green',
      pay: 'PAY premium upfront',
      profit: 'Profit if ETF rises above your breakeven',
      risk: 'Risk: Premium paid (capped)',
      reward: 'Reward: Unlimited upside',
      plShape: 'M0,40 L30,40 L70,0',
      plStroke: '#00C896',
      whenToUse: 'When you expect a large, fast move up. Good for earnings plays on bullish ETFs.',
      example: 'Buy XLF $53 Call for $0.80. If XLF hits $55, your call is worth $2.00 — 150% gain.',
    },
    {
      id: 'sell_put',
      icon: '►',
      name: 'Sell Put',
      view: 'Mildly Bullish / Neutral',
      color: 'green',
      pay: 'COLLECT credit upfront',
      profit: 'Profit if ETF stays flat or rises',
      risk: 'Risk: Spread width (capped)',
      reward: 'Reward: Keep the credit collected',
      plShape: 'M0,0 L40,0 L80,40',
      plStroke: '#00C896',
      whenToUse: 'When you expect the ETF to stay above a certain level. Better odds than Buy Call.',
      example: 'Sell XLF $51 Put for $0.30. If XLF stays above $51, you keep $30/contract.',
    },
    {
      id: 'sell_call',
      icon: '◄',
      name: 'Sell Call',
      view: 'Mildly Bearish / Neutral',
      color: 'red',
      pay: 'COLLECT credit upfront',
      profit: 'Profit if ETF stays flat or drops',
      risk: 'Risk: Spread width (capped)',
      reward: 'Reward: Keep the credit collected',
      plShape: 'M0,0 L40,0 L80,40',
      plStroke: '#FF4444',
      whenToUse: 'When you expect the ETF to stay below a certain level. OptionsIQ uses spreads to cap risk.',
      example: 'Sell XLF $54 Call for $0.27. If XLF stays below $54, you keep $27/contract.',
    },
    {
      id: 'buy_put',
      icon: '▼',
      name: 'Buy Put',
      view: 'Strongly Bearish',
      color: 'red',
      pay: 'PAY premium upfront',
      profit: 'Profit if ETF drops below your breakeven',
      risk: 'Risk: Premium paid (capped)',
      reward: 'Reward: Large downside capture',
      plShape: 'M10,0 L50,40 L80,40',
      plStroke: '#FF4444',
      whenToUse: 'When you expect a large drop. Good for sector ETFs in strong downtrends.',
      example: 'Buy XLF $51 Put for $0.75. If XLF drops to $49, your put is worth $2.00 — 167% gain.',
    },
  ];

  return (
    <div className="learn-lesson">
      <div className="learn-lesson-title">The 4 Directions</div>
      <div className="learn-lesson-intro">
        Every options trade starts with a single question: <strong>"Where do I think this ETF is going?"</strong> Click a direction to learn more.
      </div>

      <div className="learn-key-insight">
        <strong>Key Insight:</strong> Buyers PAY upfront and need big moves. Sellers COLLECT upfront and need the ETF to stay. OptionsIQ uses SPREADS for sellers to cap max loss.
      </div>

      <div className="learn-dir-grid">
        {directions.map(d => (
          <button
            key={d.id}
            className={`learn-dir-card learn-dir-${d.color} ${selected === d.id ? 'learn-dir-selected' : ''}`}
            onClick={() => setSelected(selected === d.id ? null : d.id)}
          >
            <div className="learn-dir-top">
              <span className="learn-dir-icon">{d.icon}</span>
              <div>
                <div className="learn-dir-name">{d.name}</div>
                <div className="learn-dir-view">{d.view}</div>
              </div>
            </div>
            <div className="learn-dir-pay">{d.pay}</div>
            <svg className="learn-dir-pl" viewBox="0 0 80 50" preserveAspectRatio="none">
              <line x1="0" y1="40" x2="80" y2="40" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
              <polyline points={d.plShape} fill="none" stroke={d.plStroke} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        ))}
      </div>

      {selected && (() => {
        const d = directions.find(x => x.id === selected);
        return (
          <div className={`learn-dir-detail learn-dir-detail-${d.color}`}>
            <div className="learn-dir-detail-name">{d.icon} {d.name} — {d.view}</div>
            <div className="learn-dir-detail-grid">
              <div><strong>Profit:</strong> {d.profit}</div>
              <div><strong>{d.risk}</strong></div>
              <div><strong>{d.reward}</strong></div>
            </div>
            <div className="learn-dir-when"><strong>When to use:</strong> {d.whenToUse}</div>
            <div className="learn-dir-example"><strong>Example:</strong> {d.example}</div>
          </div>
        );
      })()}
    </div>
  );
}

// ── Lesson 3: Spreads ──────────────────────────────────────────────────────
function LessonSpreads() {
  // SVG payoff diagram
  const svgW = 300, svgH = 100;
  const priceMin = 50.5, priceMax = 57;
  const pnlMin = -80, pnlMax = 30;

  function toX(price) { return ((price - priceMin) / (priceMax - priceMin)) * svgW; }
  function toY(p) { return svgH - ((p - pnlMin) / (pnlMax - pnlMin)) * svgH; }

  const zeroY = toY(0);
  const profitPoints = `${toX(50.5)},${toY(21)} ${toX(54)},${toY(21)} ${toX(54.21)},${toY(0)}`;
  const lossPoints = `${toX(54.21)},${toY(0)} ${toX(55)},${toY(-79)} ${toX(57)},${toY(-79)}`;

  return (
    <div className="learn-lesson">
      <div className="learn-lesson-title">What Is a Spread?</div>
      <div className="learn-lesson-intro">
        A spread = two options combined: one you SELL + one you BUY as protection. The protection caps your max loss — OptionsIQ always recommends spreads for selling strategies.
      </div>

      <div className="learn-spread-example">
        <div className="learn-spread-title">Example: Bear Call Spread on XLF ($52.16)</div>

        <div className="learn-spread-legs">
          <div className="learn-leg learn-leg-sell">
            <div className="learn-leg-badge">SELL</div>
            <div className="learn-leg-strike">$54 Call</div>
            <div className="learn-leg-desc">You collect $0.27/share — this is your income</div>
          </div>
          <div className="learn-leg-connector">+</div>
          <div className="learn-leg learn-leg-buy">
            <div className="learn-leg-badge">BUY</div>
            <div className="learn-leg-strike">$55 Call</div>
            <div className="learn-leg-desc">You pay $0.06/share — this caps your loss</div>
          </div>
          <div className="learn-leg-result">
            <div className="learn-leg-result-label">Net Credit</div>
            <div className="learn-leg-result-val">$0.21/share ($21/contract)</div>
          </div>
        </div>

        {/* SVG Payoff Diagram */}
        <div className="learn-payoff-wrap">
          <div className="learn-payoff-label">Payoff at Expiry</div>
          <svg width="100%" viewBox={`0 0 ${svgW} ${svgH}`} className="learn-payoff-svg" preserveAspectRatio="xMidYMid meet">
            {/* Zero line */}
            <line x1={0} y1={zeroY} x2={svgW} y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeWidth="1" strokeDasharray="4,4" />
            {/* Profit zone fill */}
            <polygon
              points={`${toX(50.5)},${zeroY} ${toX(50.5)},${toY(21)} ${toX(54)},${toY(21)} ${toX(54.21)},${zeroY}`}
              fill="rgba(0,200,150,0.1)"
            />
            {/* Loss zone fill */}
            <polygon
              points={`${toX(54.21)},${zeroY} ${toX(55)},${toY(-79)} ${toX(57)},${toY(-79)} ${toX(57)},${zeroY}`}
              fill="rgba(255,68,68,0.1)"
            />
            {/* Profit line (green) */}
            <polyline points={profitPoints} fill="none" stroke="#00C896" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            {/* Loss line (red) */}
            <polyline points={lossPoints} fill="none" stroke="#FF4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            {/* Current price line */}
            <line x1={toX(52.16)} y1={0} x2={toX(52.16)} y2={svgH} stroke="#3B82F6" strokeWidth="1.5" strokeDasharray="3,3" />
            {/* Breakeven line */}
            <line x1={toX(54.21)} y1={0} x2={toX(54.21)} y2={svgH} stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="3,3" />
            {/* Labels */}
            <text x={toX(52.16) - 2} y={12} fill="#3B82F6" fontSize="7" textAnchor="end">$52.16</text>
            <text x={toX(54.21) + 2} y={12} fill="#F59E0B" fontSize="7">BE $54.21</text>
            <text x={4} y={toY(21) - 3} fill="#00C896" fontSize="7">+$21</text>
            <text x={4} y={toY(-79) + 10} fill="#FF4444" fontSize="7">−$79</text>
          </svg>
        </div>

        {/* What happens scenarios */}
        <div className="learn-scenarios">
          <div className="learn-scenario learn-scenario-pass">
            <div className="learn-scenario-icon">✓</div>
            <div>
              <strong>XLF stays below $54:</strong> Both options expire worthless. You keep the $21 credit.
            </div>
          </div>
          <div className="learn-scenario learn-scenario-warn">
            <div className="learn-scenario-icon">!</div>
            <div>
              <strong>XLF rises to $54.50:</strong> You're still in the caution zone. P&L = $21 - partial loss.
            </div>
          </div>
          <div className="learn-scenario learn-scenario-fail">
            <div className="learn-scenario-icon">✗</div>
            <div>
              <strong>XLF rises above $55:</strong> Your BUY call protects you. Max loss = $79. CAPPED — not worse.
            </div>
          </div>
        </div>

        <div className="learn-spread-insight">
          <strong>Without the $55 protection:</strong> if XLF rose to $60, your loss would be $579. The $55 call you bought saves you $500. That's why OptionsIQ always uses spreads.
        </div>
      </div>
    </div>
  );
}

// ── Lesson 4: Gates ────────────────────────────────────────────────────────
function LessonGates() {
  const categories = [
    {
      id: 'market',
      label: 'Market Conditions',
      color: 'blue',
      icon: '📊',
      gates: [
        {
          name: 'Market Regime',
          q: 'Is the broad market on your side?',
          explain: 'Checks SPY vs its 200-day moving average and recent trend. Selling calls in a strong rally is like swimming against the current.',
          example: 'SPY above 200d SMA + rising = supportive for bull_put_spread. SPY falling hard = dangerous for sell_call.',
        },
        {
          name: 'Events Gate',
          q: 'Are there any surprise events coming?',
          explain: 'Earnings and Fed meetings (FOMC) can cause 5–10% overnight gaps. If these fall before your expiry, the gate blocks the trade.',
          example: 'XLF reports earnings in 2 weeks and your option expires in 3 weeks — gate fails, trade is blocked.',
        },
      ],
    },
    {
      id: 'pricing',
      label: 'Option Pricing',
      color: 'amber',
      icon: '💰',
      gates: [
        {
          name: 'IV Rank (IVR)',
          q: 'Are options cheap or expensive right now?',
          explain: 'IVR measures how expensive options are today vs the past year. 0% = cheapest ever. 100% = most expensive ever. Buyers want low IVR. Sellers want high IVR.',
          example: 'IVR 68% = expensive. Selling is well-rewarded — you collect richer credit. IVR 15% = cheap. Buyers get a deal.',
        },
        {
          name: 'Strike OTM %',
          q: 'Is the strike safely away from current price?',
          explain: 'The % distance between the current price and the short strike. More distance = more breathing room = higher chance of keeping the credit.',
          example: 'XLF at $52, sell $54 call = 3.8% OTM. The ETF must rise 3.8% before you start losing.',
        },
        {
          name: 'DTE Gate',
          q: 'Is the expiry date in the right window?',
          explain: 'DTE = Days To Expiry. Buyers prefer 45–90 DTE (time to be right). Sellers prefer 21–45 DTE (fastest time decay). Outside these windows = suboptimal.',
          example: '31 DTE = green for sellers. 90 DTE = better for buyers. 7 DTE = too close for either.',
        },
      ],
    },
    {
      id: 'risk',
      label: 'Risk Management',
      color: 'red',
      icon: '🛡️',
      gates: [
        {
          name: 'Liquidity',
          q: 'Can I get in and out easily?',
          explain: 'Checks bid-ask spread, open interest, and volume. Wide spreads mean you overpay to enter and undersell to exit — quietly costing you money.',
          example: 'Bid $0.20, Ask $0.50 = 43% spread = bad liquidity. Bid $0.25, Ask $0.27 = 7% = healthy.',
        },
        {
          name: 'Risk Defined',
          q: 'Is my max possible loss capped?',
          explain: 'Spread trades have a defined max loss. Naked options have unlimited loss. OptionsIQ always recommends spreads so you know the worst-case number before placing.',
          example: 'Bear call spread: max loss = $79. You know this BEFORE placing. Naked call: loss can be $500+ if ETF gaps up.',
        },
        {
          name: 'Max Loss / Position Size',
          q: 'Can I afford this without too much risk?',
          explain: 'Each trade should risk at most 1–2% of your total account. This prevents one bad trade from damaging your portfolio.',
          example: '$10,000 account: max $200 risk per trade. Bear call spread max loss $79 = well within limits. ✓',
        },
      ],
    },
  ];

  const [openGate, setOpenGate] = useState(null);

  return (
    <div className="learn-lesson">
      <div className="learn-lesson-title">What Are Gates?</div>
      <div className="learn-lesson-intro">
        Gates are safety checks that protect your money. Each one asks a simple question. OptionsIQ requires ALL gates to pass before showing GO. Click any gate to learn more.
      </div>

      <div className="learn-gate-rule">
        ALL gates pass = <span className="text-green">GO</span> &nbsp;|&nbsp;
        Any warn = <span className="text-amber">CAUTION</span> &nbsp;|&nbsp;
        Any fail = <span className="text-red">BLOCK</span>
      </div>

      {categories.map(cat => (
        <div key={cat.id} className={`learn-gate-category learn-gate-cat-${cat.color}`}>
          <div className="learn-gate-cat-header">
            {cat.icon} {cat.label}
          </div>
          {cat.gates.map(gate => (
            <div key={gate.name} className="learn-gate-item">
              <button
                className="learn-gate-item-header"
                onClick={() => setOpenGate(openGate === gate.name ? null : gate.name)}
              >
                <span className="learn-gate-item-name">{gate.name}</span>
                <span className="learn-gate-item-q">{gate.q}</span>
                <span className="learn-gate-chevron">{openGate === gate.name ? '▲' : '▼'}</span>
              </button>
              {openGate === gate.name && (
                <div className="learn-gate-item-detail">
                  <div className="learn-gate-explain">{gate.explain}</div>
                  <div className="learn-gate-example">
                    <strong>Example:</strong> {gate.example}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ))}

      <div className="learn-gate-cta">
        Switch to the Signal Board and run analysis on any ETF to see these gates applied to a real trade.
      </div>
    </div>
  );
}

// ── Main LearnTab ──────────────────────────────────────────────────────────
const LESSONS = [
  { id: 'strikes', label: 'Strikes', component: LessonStrikes },
  { id: 'directions', label: 'Directions', component: LessonDirections },
  { id: 'spreads', label: 'Spreads', component: LessonSpreads },
  { id: 'gates', label: 'Gates', component: LessonGates },
];

export default function LearnTab() {
  const [activeLesson, setActiveLesson] = useState('strikes');
  const lesson = LESSONS.find(l => l.id === activeLesson);
  const LessonComponent = lesson?.component;

  return (
    <div className="learn-tab">
      <div className="learn-tab-header">
        <div className="learn-tab-title">Options Basics</div>
        <div className="learn-tab-sub">Interactive lessons — no live data needed</div>
      </div>

      <nav className="learn-lesson-nav">
        {LESSONS.map((l, i) => (
          <button
            key={l.id}
            className={`learn-lesson-btn ${activeLesson === l.id ? 'learn-lesson-btn-active' : ''}`}
            onClick={() => setActiveLesson(l.id)}
          >
            <span className="learn-lesson-num">{i + 1}</span>
            {l.label}
          </button>
        ))}
      </nav>

      <div className="learn-lesson-body">
        {LessonComponent && <LessonComponent />}
      </div>
    </div>
  );
}
