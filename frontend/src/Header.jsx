import { useApp } from './AppContext';

const TITLES = {
  dashboard: ['Dashboard', 'Live stock overview'],
  products: ['Products', 'SKU catalog and stock status'],
  stockin: ['Inventory', 'Stock receiving and adjustments'],
  purchases: ['Purchases', 'Purchase entry and supplier history'],
  sales: ['Sales', 'Sales entry and customer history'],
  reports: ['Reports', 'EOD history, exports, and activity'],
  suppliers: ['Suppliers', 'Supplier records and contacts'],
};

export default function Header({ activePage, storeName, onEOD, onSearch }) {
  const { setMobileDrawerOpen } = useApp();
  const [title, subtitle] = TITLES[activePage] || TITLES.dashboard;

  return (
    <header className="app-header">
      <div className="header-left">
        <button
          className="btn btn-ghost btn-icon header-menu"
          onClick={() => setMobileDrawerOpen(true)}
          aria-label="Open navigation"
        >
          <IconMenu />
        </button>
        <div>
          <div className="header-title">{title}</div>
          <div className="header-subtitle">{subtitle}</div>
        </div>
      </div>

      <div className="header-actions">
        <div className="header-search">
          <IconSearch />
          <input
            className="header-search-input"
            placeholder="Search products, suppliers, history"
            onChange={(event) => onSearch?.(event.target.value)}
          />
        </div>
        <button className="btn btn-secondary header-store" type="button">
          {storeName || 'VVV Traders'}
        </button>
        <button className="btn btn-primary" type="button" onClick={onEOD}>
          EOD Export
        </button>
      </div>
    </header>
  );
}

function IconMenu() {
  return (
    <svg viewBox="0 0 20 20" fill="none" width="18" height="18">
      <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function IconSearch() {
  return (
    <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
      <circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="m13.5 13.5 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
