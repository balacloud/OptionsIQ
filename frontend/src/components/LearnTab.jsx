import { useState, useMemo } from 'react';

// ── Gate knowledge base (reused from GateExplainer) ──────────────────────
const GATE_KB = {
  ivr:              { q: 'Is IV cheap enough to buy?', pass: 'IV is relatively low — options are cheaper to buy.', fail: 'IV is high — options are expensive to buy right now.', why: 'When you buy options, high IV means you overpay. Any move must overcome that premium.' },
  ivr_seller:       { q: 'Is premium expensive enough to sell?', pass: 'IV is elevated — you collect richer premium for selling.', fail: 'IV is too low — you\'re selling options cheaply for the risk you\'re taking.', why: 'When you sell options, high IV means you get paid more. Thin premium makes one bad move hard to recover from.' },
  hv_iv:            { q: 'Are options fairly priced vs recent movement?', pass: 'Implied volatility is in line with how much the ETF has actually moved.', fail: 'Options are mispriced relative to real movement.', why: 'If options are priced much higher than the ETF actually moves, sellers benefit. If lower, buyers get an edge.' },
  strike_otm:       { q: 'Is the strike safely away from the current price?', pass: 'Your strike gives the ETF room to move before this trade gets into trouble.', fail: 'The strike is too close. Even a normal move could push you into a loss.', why: 'More distance means more breathing room. Wider margin of safety increases your chance of keeping the full credit.' },
  dte:              { q: 'Is the expiry date in the right window for buying?', pass: 'Expiry is in the 45–90 day window — good delta without too much decay.', fail: 'Expiry is too close (fast decay) or too far (capital tied up too long).', why: 'Buyers need enough time for the move to happen, but not so much that they overpay for time value.' },
  dte_seller:       { q: 'Is the expiry date in the right window for selling?', pass: 'Expiry is in the 21–45 day window where time decay accelerates most for sellers.', fail: 'Expiry is outside the optimal seller window. Theta decay may be too slow or expiry too risky.', why: 'Time decay accelerates in the final 21–45 days — that\'s when sellers collect premium fastest.' },
  events:           { q: 'Are there any surprise events before expiry?', pass: 'No earnings, Fed meetings, or major events fall before your expiry date.', fail: 'A major event (earnings, FOMC) falls before expiry. This could cause a large gap move.', why: 'One earnings surprise can cause a 5–10% overnight gap. That turns a calm trade into a max-loss trade instantly.' },
  liquidity:        { q: 'Can I get in and out of this trade easily?', pass: 'Bid-ask spread and open interest look healthy. You\'ll get fair fills.', fail: 'Wide spreads or low volume means you\'ll overpay to enter and lose more trying to exit.', why: 'Illiquid options quietly cost money. Poor fills can damage returns even when your market view is right.' },
  market_regime:    { q: 'Is the broad market trend supporting this trade?', pass: 'SPY\'s overall trend is aligned with your trade direction.', fail: 'The broad market is moving against your trade direction.', why: 'Trading with the market trend improves your odds. Selling calls in a strong rally risks assignment.' },
  market_regime_seller: { q: 'Is the broad market calm enough to sell premium?', pass: 'Market conditions support selling premium. Trend is moderate and IV is elevated.', fail: 'Market is too volatile or trending too strongly.', why: 'Selling in the direction of a strong trend is risky. A fast-moving market can blow through your strikes.' },
  vix_regime:       { q: 'Is overall market fear at an acceptable level?', pass: 'VIX is in a normal range — not too calm, not crisis-level fear.', fail: 'VIX is at an extreme level. Either fear is too low (complacent) or too high (crisis).', why: 'VIX below 15 means options are priced too cheaply. VIX above 30 means extreme uncertainty that can spike against sellers.' },
  fomc_imminent:    { q: 'Is a Fed meeting about to happen?', pass: 'No FOMC meeting within 5 days — the market won\'t be repriced by a rate decision.', fail: 'FOMC meeting is very close. Markets often freeze before and gap after Fed decisions.', why: 'Rate decisions cause instant repricing across all options. Even a "no change" can move markets 1–2%.' },
  historical_stress:{ q: 'Does this trade survive the ETF\'s worst historical moves?', pass: 'Your strike is outside the ETF\'s worst 21-day swing — it would have survived.', fail: 'Your strike is inside the ETF\'s worst 21-day swing. This trade would have been tested historically.', why: 'Historical max moves tell you what this ETF is capable of doing. Your strike needs to be beyond those levels.' },
};

const DEFAULT_GATE_KB = {
  q: 'Does this gate pass?', pass: 'Conditions are favorable for this trade.', fail: 'Conditions are not favorable for this trade.', why: 'Each gate checks a specific risk dimension before committing capital.',
};

// ── Context computation ────────────────────────────────────────────────────
function computeCtx(ticker, direction, data) {
  const dir = direction || 'sell_call';
  const etfTicker = ticker || 'XLF';
  const strategy = data?.top_strategies?.[0];
  const isReal = !!(ticker && data?.underlying_price);

  let price, shortStrike, longStrike, credit, width, dte, expiryLabel;

  if (isReal) {
    price = parseFloat(data.underlying_price);
    if (strategy?.strike) {
      shortStrike = parseFloat(strategy.strike);
      credit = parseFloat(strategy.premium ?? 0.21);
      width = parseFloat(strategy.spread_width ?? 1.0);
      longStrike = dir === 'sell_put' ? shortStrike - width : shortStrike + width;
      if (strategy.expiry_display) {
        const exp = new Date(strategy.expiry_display.slice(0, 10));
        dte = Math.max(1, Math.round((exp - Date.now()) / 86400000));
        expiryLabel = strategy.expiry_display.slice(0, 10);
      } else {
        dte = 31; expiryLabel = '—';
      }
    } else {
      // Have price but no strategy — use educated defaults relative to price
      shortStrike = dir === 'sell_put'
        ? parseFloat((price * 0.97).toFixed(2))
        : parseFloat((price * 1.03).toFixed(2));
      credit = parseFloat((price * 0.004).toFixed(2));
      width = parseFloat((price * 0.01).toFixed(2));
      longStrike = dir === 'sell_put' ? shortStrike - width : shortStrike + width;
      dte = 31; expiryLabel = '~31 days';
    }
  } else {
    price = 52.16;
    shortStrike = 54; credit = 0.21; width = 1.0;
    longStrike = dir === 'sell_put' ? 53 : 55;
    dte = 31; expiryLabel = '31 days';
  }

  const maxProfit = Math.round(credit * 100);
  const maxLoss = Math.round((width - credit) * 100);
  const totalWidth = Math.round(width * 100);
  const rrRatio = maxLoss > 0 && maxProfit > 0 ? (maxLoss / maxProfit).toFixed(2) : '—';

  const breakeven = parseFloat(
    (dir === 'sell_call' ? shortStrike + credit
     : dir === 'sell_put' ? shortStrike - credit
     : dir === 'buy_call' ? shortStrike + credit
     : shortStrike - credit).toFixed(2)
  );

  const STRAT_LABELS = {
    sell_call: 'BEAR CALL SPREAD',
    sell_put:  'BULL PUT SPREAD',
    buy_call:  'BUY CALL',
    buy_put:   'BUY PUT',
  };

  const isSeller = dir === 'sell_call' || dir === 'sell_put';
  const isCall   = dir === 'sell_call' || dir === 'buy_call';

  const distToShort = Math.abs(shortStrike - price);
  const distToShortPct = ((distToShort / price) * 100).toFixed(1);
  const otmLabel = isCall
    ? (shortStrike > price ? 'OTM' : 'ITM')
    : (shortStrike < price ? 'OTM' : 'ITM');

  // Leg descriptions
  const hedgePremium = Math.max(0, width - credit).toFixed(2);
  const shortLegLabel = isSeller
    ? `SELL ${shortStrike}${isCall ? 'C' : 'P'} @ $${credit.toFixed(2)}`
    : `BUY ${shortStrike}${isCall ? 'C' : 'P'} @ $${credit.toFixed(2)}`;
  const longLegLabel = isSeller
    ? `BUY ${longStrike}${isCall ? 'C' : 'P'} @ $${hedgePremium}`
    : null;

  return {
    ticker: etfTicker, price, dir, stratLabel: STRAT_LABELS[dir] || dir,
    shortStrike: parseFloat(shortStrike), longStrike: parseFloat(longStrike),
    credit: parseFloat(credit), width: parseFloat(width), dte, expiryLabel,
    maxProfit, maxLoss, totalWidth, rrRatio, breakeven,
    isSeller, isCall, isReal,
    otmLabel, otmPct: distToShortPct,
    distToShort: distToShort.toFixed(2),
    shortLegLabel, longLegLabel,
  };
}

// ── Panel 1: Risk / Reward ─────────────────────────────────────────────────
function PanelRisk({ ctx }) {
  const { maxProfit, maxLoss, totalWidth, rrRatio, isSeller, isCall, credit, shortStrike, longStrike, ticker, price } = ctx;
  const profitPct = totalWidth > 0 ? ((maxProfit / totalWidth) * 100).toFixed(0) : 50;
  const lossPct   = 100 - profitPct;
  const hedgePremium = Math.max(0, ctx.width - ctx.credit).toFixed(2);

  return (
    <div className="lt-panel-body">
      <div className="lt-section-label">Proportional Risk / Reward</div>
      <div className="lt-rr-track">
        <div className="lt-rr-profit" style={{ width: `${profitPct}%` }}>+${maxProfit}</div>
        <div className="lt-rr-loss"   style={{ width: `${lossPct}%`   }}>−${maxLoss}</div>
      </div>

      <div className="lt-stats-row">
        <div className="lt-stat lt-stat-green">
          <div className="lt-stat-val">+${maxProfit}</div>
          <div className="lt-stat-lbl">Max Profit</div>
        </div>
        <div className="lt-stat lt-stat-red">
          <div className="lt-stat-val">−${maxLoss}</div>
          <div className="lt-stat-lbl">Max Loss</div>
        </div>
        <div className="lt-stat lt-stat-amber">
          <div className="lt-stat-val">${totalWidth}</div>
          <div className="lt-stat-lbl">Width × 100</div>
        </div>
      </div>

      <div className="lt-rr-ratio">
        <span className="lt-rr-ratio-label">Risk : Reward</span>
        <span className="lt-rr-ratio-val">{rrRatio} : 1 — You risk ${maxLoss} to make ${maxProfit}</span>
      </div>

      <div className="lt-divider" />
      <div className="lt-section-label">How it works</div>
      <div className="lt-info-rows">
        {isSeller ? (
          <>
            <div className="lt-info-row lt-info-green">
              <span className="lt-info-icon">▼</span>
              <span><strong>SELL {shortStrike}{isCall ? 'C' : 'P'} @ ${credit.toFixed(2)}</strong> — you collect ${Math.round(credit * 100)} premium. This is your income.</span>
            </div>
            <div className="lt-info-row lt-info-blue">
              <span className="lt-info-icon">▲</span>
              <span><strong>BUY {longStrike}{isCall ? 'C' : 'P'} @ ${hedgePremium}</strong> — you pay ${Math.round(parseFloat(hedgePremium) * 100)} as a hedge. This caps your max loss.</span>
            </div>
            <div className="lt-info-row lt-info-green">
              <span className="lt-info-icon">$</span>
              <span><strong>Net credit = ${credit.toFixed(2)} × 100 = ${maxProfit}</strong> — collected upfront. You keep this if {ticker} {isCall ? 'stays below' : 'stays above'} ${shortStrike}.</span>
            </div>
            <div className="lt-info-row lt-info-red">
              <span className="lt-info-icon">!</span>
              <span><strong>Max loss = (${ctx.width.toFixed(2)} − ${credit.toFixed(2)}) × 100 = ${maxLoss}</strong> — if {ticker} closes {isCall ? 'above' : 'below'} ${longStrike} at expiry.</span>
            </div>
          </>
        ) : (
          <>
            <div className="lt-info-row lt-info-blue">
              <span className="lt-info-icon">$</span>
              <span><strong>BUY {shortStrike}{isCall ? 'C' : 'P'} @ ${credit.toFixed(2)}</strong> — you pay ${maxProfit} upfront. This is your max loss.</span>
            </div>
            <div className="lt-info-row lt-info-green">
              <span className="lt-info-icon">▲</span>
              <span><strong>Breakeven = ${ctx.breakeven}</strong> — {ticker} needs to move past here for you to profit.</span>
            </div>
            <div className="lt-info-row lt-info-amber">
              <span className="lt-info-icon">!</span>
              <span><strong>Risk is capped</strong> at ${maxProfit} paid. Reward is large if the ETF moves your way.</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Panel 2: Strike Zone Visualization ────────────────────────────────────
function PanelZones({ ctx }) {
  const [optType, setOptType] = useState(ctx.isCall ? 'call' : 'put');
  const { price, shortStrike, longStrike, breakeven, ticker, maxProfit } = ctx;
  const isCallMode = optType === 'call';

  // SVG dimensions
  const W = 500, PAD = 20;
  const IW = W - PAD * 2; // inner width

  // Display range — ensure all 4 markers have breathing room
  const rMin = Math.min(price * 0.91, shortStrike - ctx.width * 4);
  const rMax = Math.max(price * 1.09, longStrike + ctx.width * 3);
  const rSpan = rMax - rMin;
  const toX = v => PAD + ((v - rMin) / rSpan) * IW;

  const px = toX(price);
  const sx = toX(shortStrike);
  const bx = toX(breakeven);
  const lx = toX(longStrike);

  // Layout rows (y coords)
  const ZONE_Y = 0,  ZONE_H = 30;    // ITM/OTM color bands
  const PNL_Y  = 32, PNL_H  = 14;    // profit/loss bands
  const AX_Y   = 56;                  // axis line
  // Markers stagger: current+long go ABOVE axis, short goes BELOW, BE label further below
  const ABOVE_LINE_TOP = AX_Y - 28;   // top of upward line for above-axis markers
  const BELOW_LINE_BOT = AX_Y + 28;   // bottom of downward line for below-axis markers
  const BE_LINE_BOT    = AX_Y + 42;   // BE line goes even further so its label clears short
  const TOTAL_H = 102;

  // ATM band width in pixels
  const atmW = Math.max(10, IW * 0.025);

  // ITM/OTM colors depend on call vs put
  const itmFill = 'rgba(255,68,68,0.18)';
  const otmFill = 'rgba(0,200,150,0.13)';
  const atmFill = 'rgba(245,158,11,0.25)';

  // P/L fill: for sell_call profit is LEFT of BE, for sell_put profit is RIGHT
  const profitLeft  = isCallMode;
  const beX = bx;

  const mono = "'IBM Plex Mono', 'Courier New', monospace";

  return (
    <div className="lt-panel-body">
      <div className="lt-toggle-row">
        <button className={`lt-toggle-btn ${isCallMode ? 'lt-toggle-call' : ''}`} onClick={() => setOptType('call')}>
          CALL Spread (Bear)
        </button>
        <button className={`lt-toggle-btn ${!isCallMode ? 'lt-toggle-put' : ''}`} onClick={() => setOptType('put')}>
          PUT Spread (Bull)
        </button>
      </div>

      <svg
        viewBox={`0 0 ${W} ${TOTAL_H}`}
        width="100%"
        style={{ overflow: 'visible', display: 'block', margin: '4px 0' }}
      >
        {/* ── ITM / ATM / OTM zone bands ─────────────────────── */}
        {isCallMode ? (
          <>
            {/* ITM = left of price (call) */}
            <rect x={PAD} y={ZONE_Y} width={Math.max(0, px - PAD - atmW / 2)} height={ZONE_H} rx="5" fill={itmFill} />
            <text x={(PAD + px - atmW / 2) / 2} y={ZONE_Y + ZONE_H / 2 + 4} textAnchor="middle"
              fill="#FF4444" fontSize="9" fontWeight="700" letterSpacing="0.06em">ITM</text>
            {/* ATM sliver */}
            <rect x={px - atmW / 2} y={ZONE_Y} width={atmW} height={ZONE_H} rx="2" fill={atmFill} />
            {/* OTM = right of price (call) */}
            <rect x={px + atmW / 2} y={ZONE_Y} width={Math.max(0, W - PAD - px - atmW / 2)} height={ZONE_H} rx="5" fill={otmFill} />
            <text x={(px + atmW / 2 + W - PAD) / 2} y={ZONE_Y + ZONE_H / 2 + 4} textAnchor="middle"
              fill="#00C896" fontSize="9" fontWeight="700" letterSpacing="0.04em">OTM — strikes live here</text>
          </>
        ) : (
          <>
            {/* OTM = left of price (put) */}
            <rect x={PAD} y={ZONE_Y} width={Math.max(0, px - PAD - atmW / 2)} height={ZONE_H} rx="5" fill={otmFill} />
            <text x={(PAD + px - atmW / 2) / 2} y={ZONE_Y + ZONE_H / 2 + 4} textAnchor="middle"
              fill="#00C896" fontSize="9" fontWeight="700">OTM puts here</text>
            {/* ATM sliver */}
            <rect x={px - atmW / 2} y={ZONE_Y} width={atmW} height={ZONE_H} rx="2" fill={atmFill} />
            {/* ITM = right of price (put) */}
            <rect x={px + atmW / 2} y={ZONE_Y} width={Math.max(0, W - PAD - px - atmW / 2)} height={ZONE_H} rx="5" fill={itmFill} />
            <text x={(px + atmW / 2 + W - PAD) / 2} y={ZONE_Y + ZONE_H / 2 + 4} textAnchor="middle"
              fill="#FF4444" fontSize="9" fontWeight="700">ITM ← flipped for puts!</text>
          </>
        )}

        {/* ── P / L zone bands ───────────────────────────────── */}
        {profitLeft ? (
          <>
            <rect x={PAD} y={PNL_Y} width={Math.max(0, beX - PAD)} height={PNL_H} rx="3" fill="rgba(0,200,150,0.18)" />
            <text x={PAD + 6} y={PNL_Y + PNL_H / 2 + 4} fill="#00C896" fontSize="8" fontWeight="700">PROFIT ✓</text>
            <rect x={beX} y={PNL_Y} width={Math.max(0, W - PAD - beX)} height={PNL_H} rx="3" fill="rgba(255,68,68,0.18)" />
            <text x={W - PAD - 6} y={PNL_Y + PNL_H / 2 + 4} fill="#FF4444" fontSize="8" fontWeight="700" textAnchor="end">LOSS ✗</text>
          </>
        ) : (
          <>
            <rect x={PAD} y={PNL_Y} width={Math.max(0, beX - PAD)} height={PNL_H} rx="3" fill="rgba(255,68,68,0.18)" />
            <text x={PAD + 6} y={PNL_Y + PNL_H / 2 + 4} fill="#FF4444" fontSize="8" fontWeight="700">LOSS ✗</text>
            <rect x={beX} y={PNL_Y} width={Math.max(0, W - PAD - beX)} height={PNL_H} rx="3" fill="rgba(0,200,150,0.18)" />
            <text x={W - PAD - 6} y={PNL_Y + PNL_H / 2 + 4} fill="#00C896" fontSize="8" fontWeight="700" textAnchor="end">PROFIT ✓</text>
          </>
        )}

        {/* ── Axis ───────────────────────────────────────────── */}
        <line x1={PAD} y1={AX_Y} x2={W - PAD} y2={AX_Y} stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />
        {/* Range labels */}
        <text x={PAD} y={TOTAL_H} fill="rgba(255,255,255,0.2)" fontSize="7.5" fontFamily={mono}>${rMin.toFixed(0)}</text>
        <text x={W - PAD} y={TOTAL_H} fill="rgba(255,255,255,0.2)" fontSize="7.5" fontFamily={mono} textAnchor="end">${rMax.toFixed(0)}</text>

        {/* ── Marker: Current price — ABOVE axis (blue) ──────── */}
        <line x1={px} y1={ABOVE_LINE_TOP} x2={px} y2={AX_Y + 4} stroke="#3B82F6" strokeWidth="2" />
        <circle cx={px} cy={AX_Y} r="5" fill="#3B82F6" stroke="rgba(13,17,23,0.9)" strokeWidth="2" />
        <text x={px} y={ABOVE_LINE_TOP - 11} fill="#3B82F6" fontSize="9" fontWeight="700" textAnchor="middle" fontFamily={mono}>${price.toFixed(2)}</text>
        <text x={px} y={ABOVE_LINE_TOP - 2}  fill="rgba(255,255,255,0.4)" fontSize="7.5" textAnchor="middle">Current</text>

        {/* ── Marker: Long strike — ABOVE axis (green) ───────── */}
        <line x1={lx} y1={ABOVE_LINE_TOP} x2={lx} y2={AX_Y + 4} stroke="#00C896" strokeWidth="2" />
        <circle cx={lx} cy={AX_Y} r="5" fill="#00C896" stroke="rgba(13,17,23,0.9)" strokeWidth="2" />
        <text x={lx} y={ABOVE_LINE_TOP - 11} fill="#00C896" fontSize="9" fontWeight="700" textAnchor="middle" fontFamily={mono}>${longStrike}</text>
        <text x={lx} y={ABOVE_LINE_TOP - 2}  fill="rgba(255,255,255,0.4)" fontSize="7.5" textAnchor="middle">BUY {isCallMode ? 'C' : 'P'}</text>

        {/* ── Marker: Short strike — BELOW axis (red) ────────── */}
        <line x1={sx} y1={AX_Y - 4} x2={sx} y2={BELOW_LINE_BOT} stroke="#FF4444" strokeWidth="2" />
        <circle cx={sx} cy={AX_Y} r="5" fill="#FF4444" stroke="rgba(13,17,23,0.9)" strokeWidth="2" />
        <text x={sx} y={BELOW_LINE_BOT + 10} fill="#FF4444" fontSize="9" fontWeight="700" textAnchor="middle" fontFamily={mono}>${shortStrike}</text>
        <text x={sx} y={BELOW_LINE_BOT + 19} fill="rgba(255,255,255,0.4)" fontSize="7.5" textAnchor="middle">SELL {isCallMode ? 'C' : 'P'}</text>

        {/* ── Marker: Breakeven — BELOW axis (amber, dashed, further down) */}
        <line x1={bx} y1={AX_Y - 2} x2={bx} y2={BE_LINE_BOT} stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="3,2.5" />
        <text x={bx} y={BE_LINE_BOT + 10} fill="#F59E0B" fontSize="8.5" fontWeight="700" textAnchor="middle" fontFamily={mono}>BE ${breakeven}</text>
      </svg>

      <div className="lt-divider" />
      <div className="lt-legend-grid">
        <div className="lt-info-row">
          <span style={{ color: '#FF4444', fontWeight: 700, fontSize: 11, flexShrink: 0 }}>ITM</span>
          <span>{isCallMode ? 'Strike < Stock Price. The call has real value already. Bad for this credit trade.' : 'Strike > Stock Price. The put has intrinsic value.'}</span>
        </div>
        <div className="lt-info-row">
          <span style={{ color: '#00C896', fontWeight: 700, fontSize: 11, flexShrink: 0 }}>OTM</span>
          <span>{isCallMode ? 'Strike > Stock Price. No intrinsic value yet. Both sold strikes are here — good.' : 'Strike < Stock Price. No intrinsic value. Profit zone for bull put.'}</span>
        </div>
      </div>

      <div className="lt-info-row" style={{ marginTop: 4 }}>
        <span className="lt-info-icon">💡</span>
        <span>
          {isCallMode
            ? `For a bear call spread, you WANT ${ticker} to stay below $${shortStrike}. Both calls expire worthless — you keep the full $${maxProfit} credit.`
            : `For a bull put spread, you WANT ${ticker} to stay above $${shortStrike}. Both puts expire worthless — you keep the full credit.`}
        </span>
      </div>
    </div>
  );
}

// ── Panel 3: Breakeven ─────────────────────────────────────────────────────
function PanelBreakeven({ ctx }) {
  const { shortStrike, longStrike, credit, breakeven, maxProfit, maxLoss, price, dir, ticker, isCall } = ctx;
  const distBelow = Math.abs(price - shortStrike).toFixed(2);
  const distToBE  = Math.abs(price - breakeven).toFixed(2);
  const needsRise = isCall ? (breakeven > price) : (breakeven < price);
  const movePct   = ((Math.abs(breakeven - price) / price) * 100).toFixed(1);

  // SVG payoff diagram
  const W = 300, H = 100;
  const pMin = Math.min(price * 0.91, shortStrike - ctx.width * 3);
  const pMax = Math.max(price * 1.09, longStrike + ctx.width * 2);
  const pSpan = pMax - pMin;
  const pnlSpan = maxProfit + maxLoss;

  const toX = p => ((p - pMin) / pSpan) * W;
  const toY = pnl => H - ((pnl + maxLoss) / pnlSpan) * H;
  const zeroY = toY(0);

  let profitPts, lossPts;
  if (dir === 'sell_call') {
    profitPts = `${toX(pMin)},${toY(maxProfit)} ${toX(shortStrike)},${toY(maxProfit)} ${toX(breakeven)},${toY(0)}`;
    lossPts   = `${toX(breakeven)},${toY(0)} ${toX(longStrike)},${toY(-maxLoss)} ${toX(pMax)},${toY(-maxLoss)}`;
  } else if (dir === 'sell_put') {
    profitPts = `${toX(pMax)},${toY(maxProfit)} ${toX(shortStrike)},${toY(maxProfit)} ${toX(breakeven)},${toY(0)}`;
    lossPts   = `${toX(breakeven)},${toY(0)} ${toX(longStrike)},${toY(-maxLoss)} ${toX(pMin)},${toY(-maxLoss)}`;
  } else if (dir === 'buy_call') {
    profitPts = `${toX(breakeven)},${toY(0)} ${toX(pMax)},${toY(maxProfit * 2)}`;
    lossPts   = `${toX(pMin)},${toY(-maxLoss)} ${toX(shortStrike)},${toY(-maxLoss)} ${toX(breakeven)},${toY(0)}`;
  } else {
    profitPts = `${toX(breakeven)},${toY(0)} ${toX(pMin)},${toY(maxProfit * 2)}`;
    lossPts   = `${toX(pMax)},${toY(-maxLoss)} ${toX(shortStrike)},${toY(-maxLoss)} ${toX(breakeven)},${toY(0)}`;
  }

  return (
    <div className="lt-panel-body">
      <div className="lt-section-label">Breakeven Formula</div>
      <div className="lt-be-formula">
        <div className="lt-be-row">
          <span className="lt-be-key">{dir === 'sell_put' ? 'Short Strike' : 'Short Strike'}</span>
          <span className="lt-be-val">${shortStrike}</span>
        </div>
        <div className="lt-be-row">
          <span className="lt-be-key">{dir === 'sell_call' || dir === 'buy_call' ? '+ Net Credit / Premium' : '− Net Credit / Premium'}</span>
          <span className="lt-be-val" style={{ color: '#00C896' }}>{dir.includes('call') ? '+' : '−'}${credit.toFixed(2)}</span>
        </div>
        <hr className="lt-be-divider" />
        <div className="lt-be-row">
          <span className="lt-be-key">Breakeven Price</span>
          <span className="lt-be-result">${breakeven}</span>
        </div>
      </div>

      <div className="lt-divider" />
      <div className="lt-section-label">Payoff at Expiry</div>

      <div className="lt-payoff-wrap">
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {/* Zones */}
          {dir === 'sell_call' && (
            <>
              <rect x={0} y={0} width={toX(breakeven)} height={H} fill="rgba(0,200,150,0.08)" />
              <rect x={toX(breakeven)} y={0} width={W - toX(breakeven)} height={H} fill="rgba(255,68,68,0.08)" />
            </>
          )}
          {dir === 'sell_put' && (
            <>
              <rect x={toX(breakeven)} y={0} width={W - toX(breakeven)} height={H} fill="rgba(0,200,150,0.08)" />
              <rect x={0} y={0} width={toX(breakeven)} height={H} fill="rgba(255,68,68,0.08)" />
            </>
          )}
          {/* Zero axis */}
          <line x1={0} y1={zeroY} x2={W} y2={zeroY} stroke="rgba(255,255,255,0.12)" strokeWidth={1} strokeDasharray="4,3" />
          {/* Payoff lines */}
          <polyline points={profitPts} fill="none" stroke="#00C896" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          <polyline points={lossPts}   fill="none" stroke="#FF4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          {/* Current price */}
          <line x1={toX(price)} y1={0} x2={toX(price)} y2={H} stroke="#3B82F6" strokeWidth={1.5} strokeDasharray="3,3" />
          <text x={toX(price) + 2} y={12} fill="#3B82F6" fontSize="7" fontFamily="monospace" fontWeight="600">${price.toFixed(2)}</text>
          {/* Breakeven */}
          <line x1={toX(breakeven)} y1={0} x2={toX(breakeven)} y2={H} stroke="#F59E0B" strokeWidth={1.5} strokeDasharray="4,2" />
          <text x={toX(breakeven) + 2} y={22} fill="#F59E0B" fontSize="7" fontFamily="monospace" fontWeight="600">BE ${breakeven}</text>
          {/* P/L labels */}
          <text x={4} y={toY(maxProfit) - 3} fill="#00C896" fontSize="7" fontFamily="monospace" fontWeight="600">+${maxProfit} MAX</text>
          <text x={4} y={toY(-maxLoss) + 9}  fill="#FF4444" fontSize="7" fontFamily="monospace" fontWeight="600">−${maxLoss} MAX</text>
        </svg>
      </div>

      <div className="lt-info-row" style={{ marginTop: 8 }}>
        <span className="lt-info-icon">💡</span>
        <span>
          {ticker} is currently <strong>${distBelow} {needsRise ? 'below' : 'above'}</strong> your short strike and{' '}
          <strong>${distToBE} {needsRise ? 'below' : 'above'}</strong> breakeven. The stock needs to {needsRise ? 'rise' : 'fall'}{' '}
          <strong>{movePct}%</strong> before you start losing money.
        </span>
      </div>
    </div>
  );
}

// ── Panel 4: Timing / DTE ──────────────────────────────────────────────────
function PanelTiming({ ctx, data }) {
  const { dte, isSeller, ticker, shortStrike, isCall } = ctx;
  const idealMin = isSeller ? 21 : 45;
  const idealMax = isSeller ? 45 : 90;
  const dteMax = 90;
  const dteInRange = dte >= idealMin && dte <= idealMax;

  const optPosLeft  = (idealMin / dteMax) * 100;
  const optPosRight = ((dteMax - idealMax) / dteMax) * 100;
  const currPct     = Math.min(100, (dte / dteMax) * 100);

  // Pull events from gate data if available
  const gates = data?.gates || [];
  const eventsGate = gates.find(g => g.id === 'events' || g.id === 'fomc_imminent');
  const fomcGate   = gates.find(g => g.id === 'fomc_imminent');

  const defaultEvents = [
    { label: 'FOMC Meeting', detail: 'Fed rate decision', color: '#F59E0B', severity: 'MED' },
    { label: 'CPI Data', detail: 'Inflation print, affects sector ETFs', color: '#3B82F6', severity: 'LOW' },
  ];

  const realEvents = [];
  if (fomcGate && fomcGate.status !== 'pass') realEvents.push({ label: 'FOMC', detail: fomcGate.reason || 'Fed meeting imminent', color: '#FF4444', severity: 'HIGH' });
  if (eventsGate && eventsGate.status !== 'pass') realEvents.push({ label: 'Event Risk', detail: eventsGate.reason || 'Major event before expiry', color: '#FF4444', severity: 'HIGH' });
  const events = realEvents.length > 0 ? realEvents : defaultEvents;

  return (
    <div className="lt-panel-body">
      <div className="lt-section-label">Days to Expiry (DTE) — Optimal {isSeller ? 'Seller' : 'Buyer'} Range: {idealMin}–{idealMax} days</div>

      <div className="lt-dte-track">
        <div className="lt-dte-optimal" style={{ left: `${optPosLeft}%`, right: `${optPosRight}%` }} />
        <div className="lt-dte-cursor" style={{ left: `${currPct}%` }} />
        <span className="lt-dte-label" style={{ left: 4 }}>0</span>
        <span className="lt-dte-label" style={{ left: `${optPosLeft}%` }}>{idealMin}</span>
        <span className="lt-dte-label" style={{ left: `${(idealMax / dteMax) * 100}%` }}>{idealMax}</span>
        <span className="lt-dte-label" style={{ right: 4 }}>{dteMax}</span>
      </div>

      <div className="lt-stats-row" style={{ marginBottom: 10 }}>
        <div className="lt-stat lt-stat-blue">
          <div className="lt-stat-val">{dte}</div>
          <div className="lt-stat-lbl">Current DTE</div>
        </div>
        <div className="lt-stat lt-stat-green">
          <div className="lt-stat-val">{idealMin}–{idealMax}</div>
          <div className="lt-stat-lbl">Ideal Range</div>
        </div>
        <div className={`lt-stat ${dteInRange ? 'lt-stat-green' : 'lt-stat-red'}`}>
          <div className="lt-stat-val" style={{ fontSize: 11 }}>{dteInRange ? '✓ IN RANGE' : '✗ OUT'}</div>
          <div className="lt-stat-lbl">DTE Status</div>
        </div>
      </div>

      <div className="lt-info-row">
        <span className="lt-info-icon">⏱</span>
        <span>
          {isSeller
            ? `Time decay (theta) works in your favor as a credit seller. Every day ${ticker} stays ${isCall ? 'below' : 'above'} $${shortStrike}, the option loses value and you profit.`
            : `As a buyer, time works against you. The ETF must move enough to overcome daily theta decay. Act before the last 21 days when decay accelerates.`}
        </span>
      </div>

      <div className="lt-divider" />
      <div className="lt-section-label">Events Within Expiry Window</div>

      <div className="lt-event-list">
        {events.map((e, i) => (
          <div key={i} className="lt-event-item" style={{ borderColor: e.color + '55' }}>
            <div className="lt-event-dot" style={{ background: e.color }} />
            <div className="lt-event-text"><strong>{e.label}</strong> — {e.detail}</div>
            <div className="lt-event-flag" style={{ color: e.color }}>{e.severity}</div>
          </div>
        ))}
      </div>

      {realEvents.length > 0 && (
        <div className="lt-info-row lt-info-red" style={{ marginTop: 10 }}>
          <span className="lt-info-icon">⚠</span>
          <span><strong>Warning:</strong> Events inside your expiry window can cause large gap moves. IV spikes before the event and collapses after — a double-edged sword for credit sellers.</span>
        </div>
      )}
    </div>
  );
}

// ── Panel 5: Safety Gates ──────────────────────────────────────────────────
function PanelGates({ data }) {
  const [open, setOpen] = useState(null);
  const gates = data?.gates || [];

  const passCount = gates.filter(g => g.status === 'pass').length;
  const totalCount = gates.length || 7;
  const scorePct = totalCount > 0 ? ((passCount / totalCount) * 100).toFixed(0) : 0;
  const scoreColor = passCount === totalCount ? '#00C896' : passCount >= totalCount * 0.7 ? '#F59E0B' : '#FF4444';

  // Use real gates if available, otherwise show Perplexity default example
  const displayGates = gates.length > 0 ? gates.map((g, i) => {
    const kb = GATE_KB[g.id] || DEFAULT_GATE_KB;
    const statusColor = g.status === 'pass' ? '#00C896' : g.status === 'warn' ? '#F59E0B' : '#FF4444';
    const meter = g.status === 'pass' ? 80 : g.status === 'warn' ? 45 : 20;
    return { ...g, kb, statusColor, meter, num: i + 1, displayStatus: g.status?.toUpperCase() };
  }) : DEFAULT_GATES;

  return (
    <div className="lt-panel-body">
      <div style={{ marginBottom: 14 }}>
        <div className="lt-score-header">
          <span className="lt-score-label">Trade Readiness Score</span>
          <span className="lt-score-val" style={{ color: scoreColor }}>{passCount} / {totalCount} gates pass</span>
        </div>
        <div className="lt-score-track">
          <div className="lt-score-fill" style={{ width: `${scorePct}%`, background: `linear-gradient(90deg, #00C896, ${scoreColor})` }} />
        </div>
      </div>

      <div className="lt-gates-list">
        {displayGates.map((g, i) => {
          const isOpen = open === i;
          const sColor = g.statusColor || (g.status === 'pass' ? '#00C896' : g.status === 'warn' ? '#F59E0B' : '#FF4444');
          const sBg    = g.status === 'pass' ? 'rgba(0,200,150,0.12)' : g.status === 'warn' ? 'rgba(245,158,11,0.12)' : 'rgba(255,68,68,0.12)';
          const kb     = g.kb || DEFAULT_GATE_KB;
          return (
            <div key={i} className={`lt-gate-row ${isOpen ? 'lt-gate-open' : ''}`}>
              <div className="lt-gate-header" onClick={() => setOpen(isOpen ? null : i)}>
                <div className="lt-gate-num" style={{ background: sBg, color: sColor }}>{g.num || i+1}</div>
                <div className="lt-gate-name">{g.name}</div>
                <span className="lt-gate-detail">{g.reason?.slice(0, 40) || g.value || ''}</span>
                <div className="lt-gate-pill" style={{ background: sBg, color: sColor, border: `1px solid ${sColor}55` }}>
                  {g.displayStatus || (g.status || 'PASS').toUpperCase()}
                </div>
                <span className="lt-gate-chevron">{isOpen ? '▲' : '▼'}</span>
              </div>
              {isOpen && (
                <div className="lt-gate-detail-body">
                  <div className="lt-gate-q">❓ {kb.q}</div>
                  <div className="lt-gate-meter">
                    <div className="lt-gate-meter-fill" style={{ width: `${g.meter || 50}%`, background: sColor }} />
                  </div>
                  <div className="lt-gate-answers">
                    <div className="lt-gate-answer">
                      <div className="lt-gate-icon" style={{ background: 'rgba(0,200,150,0.15)', color: '#00C896' }}>✓</div>
                      <div><strong style={{ color: '#00C896' }}>PASS:</strong> {kb.pass}</div>
                    </div>
                    <div className="lt-gate-answer">
                      <div className="lt-gate-icon" style={{ background: 'rgba(255,68,68,0.15)', color: '#FF4444' }}>✗</div>
                      <div><strong style={{ color: '#FF4444' }}>FAIL:</strong> {kb.fail}</div>
                    </div>
                    <div className="lt-gate-answer">
                      <div className="lt-gate-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#F59E0B' }}>$</div>
                      <div><strong style={{ color: '#F59E0B' }}>WHY:</strong> {kb.why}</div>
                    </div>
                  </div>
                  {g.reason && <div className="lt-gate-reason">Actual result: {g.reason}</div>}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Default gates for when no real data is loaded (Perplexity example)
const DEFAULT_GATES = [
  { num:1, name:'IV Rank', status:'pass', statusColor:'#00C896', meter:68, reason:'IVR 68% — elevated, premium is well-rewarded', id:'ivr_seller' },
  { num:2, name:'Strike OTM %', status:'pass', statusColor:'#00C896', meter:70, reason:'Strike is 3.5% OTM — comfortable buffer', id:'strike_otm' },
  { num:3, name:'DTE', status:'pass', statusColor:'#00C896', meter:80, reason:'31 days — squarely in the 21–45 day sweet spot', id:'dte_seller' },
  { num:4, name:'Events', status:'fail', statusColor:'#FF4444', meter:30, reason:'Earnings inside expiry window — large gap risk', id:'events' },
  { num:5, name:'Liquidity', status:'pass', statusColor:'#00C896', meter:85, reason:'Spread $0.03, OI 4.2k — highly liquid', id:'liquidity' },
  { num:6, name:'Market Regime', status:'pass', statusColor:'#00C896', meter:65, reason:'SPY above 200d SMA — trend supportive', id:'market_regime_seller' },
  { num:7, name:'Risk Defined', status:'pass', statusColor:'#00C896', meter:100, reason:'Bear call spread — max loss $79 capped', id:'liquidity' },
].map(g => ({ ...g, kb: GATE_KB[g.id] || DEFAULT_GATE_KB, displayStatus: g.status.toUpperCase() }));

// ── Main component ─────────────────────────────────────────────────────────
const PANELS = [
  { label: 'Risk' },
  { label: 'Zones' },
  { label: 'B/E' },
  { label: 'Timing' },
  { label: 'Gates' },
];

export default function LearnTab({ ticker, direction, data }) {
  const [activePanel, setActivePanel] = useState(0);
  const ctx = useMemo(() => computeCtx(ticker, direction, data), [ticker, direction, data]);

  const gatesCount = data?.gates?.length || 0;
  const passCount  = data?.gates?.filter(g => g.status === 'pass').length || 0;
  const badgeLabel = {
    0: `RISK DEFINED ✓`,
    1: `${ctx.otmLabel} +${ctx.otmPct}%`,
    2: `BE = $${ctx.breakeven}`,
    3: ctx.dte <= 45 && ctx.dte >= 21 ? 'DTE ✓ IN RANGE' : `DTE ${ctx.dte}d`,
    4: gatesCount > 0 ? `${passCount}/${gatesCount} PASS` : '7 GATES',
  };
  const badgeColor = {
    0: 'lt-badge-pass',
    1: ctx.otmLabel === 'OTM' ? 'lt-badge-warn' : 'lt-badge-fail',
    2: 'lt-badge-warn',
    3: (ctx.dte >= 21 && ctx.dte <= 45) ? 'lt-badge-pass' : 'lt-badge-warn',
    4: gatesCount > 0 && passCount < gatesCount ? 'lt-badge-fail' : 'lt-badge-pass',
  };

  return (
    <div className="lt-wrap">
      {/* Header */}
      <div className="lt-header">
        <div className="lt-trade-badge">
          <span className="lt-sym">{ctx.ticker}</span>
          <span>${ctx.price.toFixed(2)}</span>
          <span className="lt-strat">{ctx.stratLabel}</span>
        </div>
        {!ctx.isReal && (
          <div className="lt-example-note">Example trade · Select an ETF for real values</div>
        )}
      </div>

      {/* Tab nav */}
      <nav className="lt-tab-nav">
        {PANELS.map((p, i) => (
          <button
            key={i}
            className={`lt-tab-btn ${activePanel === i ? 'lt-tab-active' : ''}`}
            onClick={() => setActivePanel(i)}
          >
            <span className="lt-tab-num">{i + 1}</span>
            {p.label}
          </button>
        ))}
      </nav>

      {/* Panel */}
      <div className="lt-panel">
        <div className="lt-panel-head">
          <div>
            <div className="lt-panel-title">
              {['Max Profit vs Max Loss', 'Strike Zone Visualization', 'Breakeven Point', 'Timing: DTE & Events', '7 Safety Gates'][activePanel]}
            </div>
            <div className="lt-panel-sub">
              {[
                'Your best case and worst case — defined before you place the trade',
                'Where each price level sits — and what it means for your trade',
                'The exact price where you neither profit nor lose at expiry',
                'Days to expiry and what scheduled events could move the stock',
                'All gates must pass before placing the trade',
              ][activePanel]}
            </div>
          </div>
          <div className={`lt-badge ${badgeColor[activePanel]}`}>{badgeLabel[activePanel]}</div>
        </div>

        {activePanel === 0 && <PanelRisk ctx={ctx} />}
        {activePanel === 1 && <PanelZones ctx={ctx} />}
        {activePanel === 2 && <PanelBreakeven ctx={ctx} />}
        {activePanel === 3 && <PanelTiming ctx={ctx} data={data} />}
        {activePanel === 4 && <PanelGates data={data} />}
      </div>

      {/* Progress dots */}
      <div className="lt-progress">
        {PANELS.map((_, i) => (
          <div
            key={i}
            className={`lt-dot ${activePanel === i ? 'lt-dot-active' : ''}`}
            onClick={() => setActivePanel(i)}
          />
        ))}
      </div>
    </div>
  );
}
