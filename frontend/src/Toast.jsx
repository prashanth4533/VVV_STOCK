import { useApp } from './AppContext';

const icons = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

export default function Toast() {
  const { toasts, dismissToast } = useApp();

  if (!toasts.length) return null;

  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`} onClick={() => dismissToast(t.id)}>
          <span style={{ fontSize: 14, flexShrink: 0 }}>{icons[t.type] || icons.info}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}
