import Sidebar from './Sidebar';
import Header from './Header';
import Toast from './Toast';
import { useApp } from './AppContext';

export default function Layout({ activePage, onNavigate, storeName, onEOD, onSearch, children }) {
  const { sidebarExpanded } = useApp();

  return (
    <div className="layout">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />

      <div
        className="layout-main"
        style={{
          marginLeft: 'var(--sidebar-collapsed)',
          // On desktop, shift content when sidebar expands on hover
        }}
      >
        <Header
          activePage={activePage}
          storeName={storeName}
          onEOD={onEOD}
          onSearch={onSearch}
        />
        <main className="layout-content">
          {children}
        </main>
      </div>

      <Toast />
    </div>
  );
}
