  
import { useMemo } from 'react';

export default function Dashboard({ data, storeName, onNavigate }) {
  const { products = [], purchases = [], sales = [], stockLog = [] } = data;

  // ── KPI derivations ──────────────────────────────────────
  const totalProducts = products.length;
  const totalStock    = products.reduce((s, p) => s + (p.stock || 0), 0);
  const lowStock      = products.filter(p => p.stock > 0 && p.stock <= (p.low || 5));
  const outOfStock    = products.filter(p => p.stock === 0);
  const reorderCount  = lowStock.length + outOfStock.length;

  const today = new Date().toISOString().slice(0, 10);
  const todayPurchases = purchases
    .filter(p => (p.purchase_date || '').slice(0, 10) === today && p.status !== 'cancelled')
    .reduce((sum, p) => sum + Number(p.total_amount || 0), 0);
  const todaySales = sales
    .filter(s => (s.sale_date || '').slice(0, 10) === today && s.status !== 'cancelled')
    .reduce((sum, s) => sum + Number(s.total_amount || 0), 0);

  // ── Status breakdown ─────────────────────────────────────
  const inStockCount = products.filter(p => p.stock > (p.low || 5)).length;
  const lowCount     = lowStock.length;
  const outCount     = outOfStock.length;
  const total        = totalProducts || 1;
  const pctIn        = Math.round((inStockCount / total) * 100);
  const pctLow       = Math.round((lowCount     / total) * 100);
  const pctOut       = Math.round((outCount     / total) * 100);

  // ── 7-day bar chart data ──────────────────────────────────
  const last7 = useMemo(() => {
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const label = i === 0 ? 'Today' : d.toLocaleDateString('en-IN', { weekday: 'short' });
      const dayLog = stockLog.filter(l => (l.date || '').slice(0, 10) === key);
      const inQty  = dayLog.filter(l => l.type === 'in').reduce((s, l)  => s + (l.qty || 0), 0);
      const outQty = dayLog.filter(l => l.type === 'out').reduce((s, l) => s + (l.qty || 0), 0);
      days.push({ label, inQty, outQty, key });
    }
    return days;
  }, [stockLog]);

  // ── Category stock overview ───────────────────────────────
  const catOverview = useMemo(() => {
    const map = {};
    products.forEach(p => {
      const cat = p.category || 'Uncategorised';
      if (!map[cat]) map[cat] = { total: 0, count: 0, low: 0 };
      map[cat].total += p.stock || 0;
      map[cat].count += 1;
      if (p.stock <= (p.low || 5)) map[cat].low += 1;
    });
    return Object.entries(map)
      .map(([cat, v]) => ({ cat, ...v }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 7);
  }, [products]);

  // ── Recent transactions ───────────────────────────────────
  const recent = useMemo(() =>
    [...stockLog]
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 6),
    [stockLog]
  );

  const fmtDate = (d) => {
    if (!d) return '—';
    const dt   = new Date(d);
    const now  = new Date();
    const diff = (now - dt) / 86400000;
    if (diff < 1) return dt.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    if (diff < 2) return 'Yesterday';
    return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  };
  
const money = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value || 0);
  return (
    <div className="db">

      {/* ── ROW 1 — KPI cards (5 cols) ────────────────────────── */}
      <div className="db-kpi-row">
        <KpiCard label="Total Products"   value={totalProducts}              accent="indigo" icon={<IBox />}   />
        <KpiCard label="Total Stock"      value={totalStock.toLocaleString()} accent="green"  icon={<IStack />} />
        <KpiCard label="Today's Purchases" value={money(todayPurchases)}      accent="green"  icon={<IIn />}    />
        <KpiCard label="Today's Sales"    value={money(todaySales)}           accent="red"    icon={<IOut />}   />
        <KpiCard label="Reorder Required" value={reorderCount}               accent="amber"  icon={<IAlert />} />
      </div>

      {/* ── ROW 2 — Bar chart (60%) + Donut (40%) ─────────────── */}
      <div className="db-row2">
        <div className="card db-bar-card">
          <div className="db-section-title">Daily Orders — Last 7 Days</div>
          <BarChart data={last7} />
        </div>
        <div className="card db-donut-card">
          <div className="db-section-title">Stock Status</div>
          <DonutChart inStock={inStockCount} low={lowCount} out={outCount} total={total} />
          <div className="status-legend">
            <LegendItem color="var(--success)" label="In Stock"  count={inStockCount} pct={pctIn}  />
            <LegendItem color="var(--warning)" label="Low Stock" count={lowCount}     pct={pctLow} />
            <LegendItem color="var(--danger)"  label="Out"       count={outCount}     pct={pctOut} />
          </div>
        </div>
      </div>

      {/* ── ROW 3 — Category table (50%) + Recent txns (50%) ───── */}
      <div className="db-row3">
        {/* Category overview */}
        <div className="card db-cat-card">
          <div className="db-section-title">Category Stock Overview</div>
          {catOverview.length === 0 ? (
            <div className="empty-state" style={{ padding: '20px 0' }}>
              <span className="empty-state-icon" style={{ fontSize: 24 }}>📦</span>
              <span style={{ fontSize: 12 }}>No products yet</span>
            </div>
          ) : (
            <table className="db-cat-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>SKUs</th>
                  <th>Stock</th>
                  <th>Low</th>
                </tr>
              </thead>
              <tbody>
                {catOverview.map((row, i) => (
                  <tr key={i}>
                    <td className="db-cat-name">{row.cat}</td>
                    <td>{row.count}</td>
                    <td className="font-mono" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{row.total.toLocaleString()}</td>
                    <td>
                      {row.low > 0
                        ? <span className="badge badge-low">{row.low}</span>
                        : <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>—</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Recent transactions */}
        <div className="card db-txn-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div className="db-section-title" style={{ marginBottom: 0 }}>Recent Transactions</div>
            <button className="btn btn-ghost btn-sm" onClick={() => onNavigate?.('stockin')} style={{ fontSize: 11 }}>
              View all →
            </button>
          </div>
          {recent.length === 0 ? (
            <div className="empty-state" style={{ padding: '20px 0' }}>
              <span className="empty-state-icon" style={{ fontSize: 24 }}>📋</span>
              <span style={{ fontSize: 12 }}>No transactions yet</span>
            </div>
          ) : (
            <div className="db-txn-list">
              {recent.map((log, i) => (
                <div key={i} className="db-txn-item">
                  <div className={`db-txn-dot db-txn-dot--${log.type || 'in'}`} />
                  <div className="db-txn-body">
                    <span className="db-txn-name">{log.name || log.product || '—'}</span>
                    {log.category && <span className="db-txn-cat">{log.category}</span>}
                  </div>
                  <div className="db-txn-right">
                    <span className={`db-txn-qty db-txn-qty--${log.type === 'out' ? 'out' : 'in'}`}>
                      {log.type === 'out' ? '−' : '+'}{log.qty || 0}
                    </span>
                    <span className="db-txn-time">{fmtDate(log.date)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Compact KPI card ─────────────────────────────────────────── */
function KpiCard({ label, value, accent, icon }) {
  const accentMap = {
    indigo: { color: 'var(--indigo-400)', bg: 'var(--indigo-subtle)', border: 'rgba(99,102,241,0.2)' },
    green:  { color: 'var(--success)',    bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)' },
    amber:  { color: 'var(--warning)',    bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
    red:    { color: 'var(--danger)',     bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)' },
  };
  const a = accentMap[accent] || accentMap.indigo;

  return (
    <div className="kpi-card" style={{ '--acc': a.color, '--acc-bg': a.bg, '--acc-bd': a.border }}>
      <div className="kpi-top">
        <div className="kpi-icon">{icon}</div>
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}

/* ── 7-day bar chart (pure SVG) ────────────────────────────────── */
function BarChart({ data }) {
  const W = 520, H = 100, pad = { l: 0, r: 0, t: 8, b: 24 };
  const chartW = W - pad.l - pad.r;
  const chartH = H - pad.t - pad.b;
  const maxVal = Math.max(...data.map(d => Math.max(d.inQty, d.outQty)), 1);
  const barW   = Math.floor(chartW / data.length);
  const bw     = Math.max(8, Math.floor(barW * 0.3));

  return (
    <div style={{ width: '100%' }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ overflow: 'visible' }}>
        {data.map((d, i) => {
          const x    = pad.l + i * barW + barW / 2;
          const inH  = (d.inQty  / maxVal) * chartH;
          const outH = (d.outQty / maxVal) * chartH;
          const inY  = pad.t + chartH - inH;
          const outY = pad.t + chartH - outH;

          return (
            <g key={i}>
              {/* In bar */}
              <rect
                x={x - bw - 1} y={inH  > 0 ? inY  : pad.t + chartH}
                width={bw} height={Math.max(inH,  2)}
                rx={2} fill="var(--success)" opacity="0.75"
                style={{ transition: 'opacity var(--t-fast)' }}
              >
                <title>{d.label} — Stock In: {d.inQty}</title>
              </rect>
              {/* Out bar */}
              <rect
                x={x + 1}      y={outH > 0 ? outY : pad.t + chartH}
                width={bw} height={Math.max(outH, 2)}
                rx={2} fill="var(--danger)" opacity="0.65"
              >
                <title>{d.label} — Sales Out: {d.outQty}</title>
              </rect>
              {/* Label */}
              <text
                x={x} y={H - 4}
                textAnchor="middle"
                fill="var(--text-muted)"
                fontSize="9"
                fontFamily="Inter,sans-serif"
              >{d.label}</text>
            </g>
          );
        })}
        {/* Baseline */}
        <line x1={pad.l} x2={W - pad.r} y1={pad.t + chartH} y2={pad.t + chartH}
              stroke="var(--border)" strokeWidth="1" />
      </svg>
      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 4 }}>
        <span style={{ fontSize: 10, color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, background: 'var(--success)', borderRadius: 2, display: 'inline-block', opacity: 0.75 }} />
          Stock In
        </span>
        <span style={{ fontSize: 10, color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, background: 'var(--danger)', borderRadius: 2, display: 'inline-block', opacity: 0.65 }} />
          Sales Out
        </span>
      </div>
    </div>
  );
}

/* ── Donut chart (pure SVG) ─────────────────────────────────────── */
function DonutChart({ inStock, low, out, total }) {
  const r = 38, cx = 48, cy = 48;
  const circ = 2 * Math.PI * r;

  const segs = [
    { value: inStock, color: 'var(--success)' },
    { value: low,     color: 'var(--warning)' },
    { value: out,     color: 'var(--danger)' },
  ];

  let offset = 0;
  const arcs = segs.map(s => {
    const pct  = total > 0 ? s.value / total : 0;
    const dash = pct * circ;
    const gap  = circ - dash;
    const arc  = { ...s, dash, gap, offset };
    offset += dash;
    return arc;
  });

  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 10 }}>
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--border)" strokeWidth="10" />
        {arcs.filter(a => a.dash > 0).map((a, i) => (
          <circle key={i} cx={cx} cy={cy} r={r}
            fill="none" stroke={a.color} strokeWidth="10"
            strokeDasharray={`${a.dash} ${a.gap}`}
            strokeDashoffset={-a.offset + circ / 4}
            style={{ transition: 'stroke-dasharray 0.5s ease' }}
          />
        ))}
        <text x={cx} y={cy - 4}  textAnchor="middle" fill="var(--text-primary)" fontSize="16" fontWeight="700" fontFamily="Inter,sans-serif">{total}</text>
        <text x={cx} y={cx + 10} textAnchor="middle" fill="var(--text-muted)"   fontSize="8"             fontFamily="Inter,sans-serif">products</text>
      </svg>
    </div>
  );
}

function LegendItem({ color, label, count, pct }) {
  return (
    <div className="legend-item">
      <span className="legend-dot" style={{ background: color }} />
      <span className="legend-label">{label}</span>
      <span className="legend-count">{count}</span>
      <span className="legend-pct">{pct}%</span>
    </div>
  );
}

/* ── Icons ─────────────────────────────────────────────────────── */
function IBox()   { return <svg viewBox="0 0 20 20" fill="none" width="14" height="14"><path d="M17 6l-7-4L3 6m14 0v8l-7 4m0-12L3 6m0 0v8l7 4" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>; }
function IStack() { return <svg viewBox="0 0 20 20" fill="none" width="14" height="14"><path d="M10 2L2 6l8 4 8-4-8-4zM2 10l8 4 8-4M2 14l8 4 8-4" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>; }
function IIn()    { return <svg viewBox="0 0 20 20" fill="none" width="14" height="14"><path d="M10 3v11m0 0l-4-4m4 4l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M4 17h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>; }
function IOut()   { return <svg viewBox="0 0 20 20" fill="none" width="14" height="14"><path d="M10 17V6m0 0l-4 4m4-4l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M4 3h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>; }
function IAlert() { return <svg viewBox="0 0 20 20" fill="none" width="14" height="14"><path d="M10 2L2 17h16L10 2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/><path d="M10 8v4M10 14.5v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>; }
