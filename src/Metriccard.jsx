export default function MetricCard({ label, value, sub, icon, accent, trend }) {
  // accent: 'indigo' | 'green' | 'amber' | 'red'
  const accentMap = {
    indigo: { color: 'var(--indigo-400)', bg: 'var(--indigo-subtle)', border: 'rgba(99,102,241,0.2)' },
    green:  { color: 'var(--success)',    bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)' },
    amber:  { color: 'var(--warning)',    bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
    red:    { color: 'var(--danger)',     bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)' },
  };
  const a = accentMap[accent] || accentMap.indigo;

  return (
    <div className="metric-card" style={{ '--accent': a.color, '--accent-bg': a.bg, '--accent-border': a.border }}>
      <div className="metric-card-top">
        {icon && (
          <div className="metric-card-icon">
            {icon}
          </div>
        )}
        {trend !== undefined && (
          <span className={`metric-card-trend ${trend >= 0 ? 'metric-card-trend--up' : 'metric-card-trend--down'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="metric-card-value">{value}</div>
      <div className="metric-card-label">{label}</div>
      {sub && <div className="metric-card-sub">{sub}</div>}
    </div>
  );
}