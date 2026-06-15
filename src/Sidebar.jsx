import { useApp } from './AppContext';

const NAV_ITEMS = [
  { key: 'dashboard',  label: 'Dashboard',   icon: <IcGrid /> },
  { key: 'products',   label: 'Products',    icon: <IcBox /> },
  { key: 'stockin',    label: 'Inventory',   icon: <IcArrowDown /> },
  { key: 'purchases',  label: 'Purchases',   icon: <IcCart /> },
  { key: 'sales',      label: 'Sales',       icon: <IcTag /> },
  { key: 'suppliers',  label: 'Suppliers',   icon: <IcTruck /> },
  { key: 'reports',    label: 'Reports',     icon: <IcChart /> },
];

// One entry per destination — guard against accidental duplicates
const NAV_UNIQUE = NAV_ITEMS.reduce((acc, item) => {
  if (!acc.find(a => a.key === item.key)) acc.push(item);
  return acc;
}, []);

export default function Sidebar({ activePage, onNavigate }) {
  const { sidebarExpanded, setSidebarExpanded, setMobileDrawerOpen } = useApp();

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className="sidebar"
        style={{ width: sidebarExpanded ? 'var(--sidebar-expanded)' : 'var(--sidebar-collapsed)' }}
        onMouseEnter={() => setSidebarExpanded(true)}
        onMouseLeave={() => setSidebarExpanded(false)}
      >
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-mark">
            <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
              <rect x="3"  y="3"  width="7" height="7" rx="2" fill="#6366f1" />
              <rect x="14" y="3"  width="7" height="7" rx="2" fill="#818cf8" opacity="0.7" />
              <rect x="3"  y="14" width="7" height="7" rx="2" fill="#818cf8" opacity="0.7" />
              <rect x="14" y="14" width="7" height="7" rx="2" fill="#a5b4fc" opacity="0.5" />
            </svg>
          </div>
          {sidebarExpanded && (
            <div className="sidebar-logo-text-group">
              <span className="sidebar-logo-text">VVV Stock</span>
              <span className="sidebar-logo-badge">Pro</span>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="sidebar-divider" />

        {/* Nav */}
        <nav className="sidebar-nav">
          {NAV_UNIQUE.map(item => (
            <NavItem
              key={`${item.key}-${item.label}`}
              item={item}
              active={activePage === item.key}
              expanded={sidebarExpanded}
              onClick={() => onNavigate(item.key)}
            />
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <NavItem
            item={{ key: 'settings', label: 'Settings', icon: <IcSettings /> }}
            active={activePage === 'settings'}
            expanded={sidebarExpanded}
            onClick={() => {}}
          />
        </div>
      </aside>

      {/* Mobile drawer */}
      <MobileDrawer activePage={activePage} onNavigate={onNavigate} />
    </>
  );
}

function NavItem({ item, active, expanded, onClick }) {
  return (
    <button
      className={`sidebar-item ${active ? 'sidebar-item--active' : ''}`}
      onClick={onClick}
      title={!expanded ? item.label : undefined}
    >
      <span className="sidebar-item-icon">{item.icon}</span>
      {expanded && <span className="sidebar-item-label">{item.label}</span>}
      {active && <span className="sidebar-item-indicator" />}
    </button>
  );
}

function MobileDrawer({ activePage, onNavigate }) {
  const { mobileDrawerOpen, setMobileDrawerOpen } = useApp();
  if (!mobileDrawerOpen) return null;

  return (
    <>
      <div className="mobile-overlay" onClick={() => setMobileDrawerOpen(false)} />
      <aside className="mobile-drawer">
        <div className="sidebar-logo" style={{ padding: '0 16px', height: 56 }}>
          <div className="sidebar-logo-mark">
            <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
              <rect x="3"  y="3"  width="7" height="7" rx="2" fill="#6366f1" />
              <rect x="14" y="3"  width="7" height="7" rx="2" fill="#818cf8" opacity="0.7" />
              <rect x="3"  y="14" width="7" height="7" rx="2" fill="#818cf8" opacity="0.7" />
              <rect x="14" y="14" width="7" height="7" rx="2" fill="#a5b4fc" opacity="0.5" />
            </svg>
          </div>
          <div className="sidebar-logo-text-group">
            <span className="sidebar-logo-text">VVV Stock</span>
            <span className="sidebar-logo-badge">Pro</span>
          </div>
        </div>
        <div className="sidebar-divider" />
        <nav className="sidebar-nav">
          {NAV_UNIQUE.map(item => (
            <button
              key={`${item.key}-${item.label}`}
              className={`sidebar-item sidebar-item--expanded ${activePage === item.key ? 'sidebar-item--active' : ''}`}
              onClick={() => { onNavigate(item.key); setMobileDrawerOpen(false); }}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              <span className="sidebar-item-label">{item.label}</span>
              {activePage === item.key && <span className="sidebar-item-indicator" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="sidebar-item sidebar-item--expanded" onClick={() => setMobileDrawerOpen(false)}>
            <span className="sidebar-item-icon"><IcSettings /></span>
            <span className="sidebar-item-label">Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
}

/* ── SVG Icons ─────────────────────────────────────────────── */
function IcGrid() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <rect x="2" y="2" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
    <rect x="11" y="2" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
    <rect x="2" y="11" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
    <rect x="11" y="11" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
  </svg>;
}
function IcBox() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <path d="M17 6l-7-4L3 6m14 0v8l-7 4m0-12L3 6m0 0v8l7 4" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    <path d="M10 10l7-4M10 10v8M10 10L3 6" stroke="currentColor" strokeWidth="1.5"/>
  </svg>;
}
function IcArrowDown() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <path d="M10 3v11m0 0l-4-4m4 4l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M4 17h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>;
}
function IcTag() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <path d="M3 3h6l8 8-6 6-8-8V3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    <circle cx="7" cy="7" r="1.2" fill="currentColor"/>
  </svg>;
}
function IcCart() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <path d="M2 2h2l.8 4M4.8 6h12.6l-1.8 7H6L4.8 6z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    <circle cx="8" cy="16.5" r="1" stroke="currentColor" strokeWidth="1.5"/>
    <circle cx="15" cy="16.5" r="1" stroke="currentColor" strokeWidth="1.5"/>
  </svg>;
}
function IcChart() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <rect x="3" y="11" width="3" height="6" rx="1" stroke="currentColor" strokeWidth="1.5"/>
    <rect x="8.5" y="7" width="3" height="10" rx="1" stroke="currentColor" strokeWidth="1.5"/>
    <rect x="14" y="3" width="3" height="14" rx="1" stroke="currentColor" strokeWidth="1.5"/>
  </svg>;
}
function IcTruck() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <path d="M1 4h11v9H1V4z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    <path d="M12 7h4l3 4v2h-7V7z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    <circle cx="4.5" cy="14.5" r="1.5" stroke="currentColor" strokeWidth="1.5"/>
    <circle cx="15.5" cy="14.5" r="1.5" stroke="currentColor" strokeWidth="1.5"/>
  </svg>;
}
function IcSettings() {
  return <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
    <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M10 2v1.5M10 16.5V18M18 10h-1.5M3.5 10H2M15.36 4.64l-1.06 1.06M5.7 14.3l-1.06 1.06M15.36 15.36l-1.06-1.06M5.7 5.7L4.64 4.64" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>;
}
