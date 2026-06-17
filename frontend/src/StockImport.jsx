import { useRef, useState } from 'react';
import { downloadSheet, parseSheet } from './utils/excel';

/**
 * Stock bulk update — Export Current Stock + Import Stock Update.
 *
 * Export: products → sheet with columns `product`, `current_stock`.
 * Import: user edits `current_stock`; we match rows back to products by name,
 *   diff old vs new, and (via onStockUpdate) create one stock-adjustment
 *   transaction per CHANGED product. Unchanged rows are skipped.
 *
 * Reuses the existing adjustment API — no new business logic.
 */

// Display label used as the `product` key in the export sheet.
function productLabel(p) {
  return `${p.brand || ''} ${p.item || ''}`.trim() || p.name || `#${p.id}`;
}

export function exportCurrentStock(products) {
  const rows = (products || []).map((p) => ({
    product: productLabel(p),
    current_stock: p.stock ?? p.qty ?? 0,
  }));
  downloadSheet(rows, 'Stock', 'current_stock.xlsx');
}

export default function StockImportModal({ products, onStockUpdate, onClose }) {
  const fileRef = useRef(null);
  const [fileName, setFileName] = useState('');
  const [diff, setDiff] = useState(null);   // [{ id, label, oldQty, newQty, changed, error }]
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  const [readError, setReadError] = useState('');

  const changed = diff ? diff.filter((r) => r.changed && !r.error) : [];
  const unmatched = diff ? diff.filter((r) => r.error) : [];

  const onPick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setReadError(''); setResult(null);
    setFileName(file.name);

    // Match by normalized product label.
    const byLabel = new Map(
      (products || []).map((p) => [productLabel(p).trim().toLowerCase(), p])
    );

    try {
      const rows = await parseSheet(file);
      if (!rows.length) { setReadError('The sheet has no data rows.'); setDiff([]); return; }
      const computed = rows.map((r) => {
        const name = String(r.product ?? '').trim();
        const rawNew = r.current_stock;
        const p = byLabel.get(name.toLowerCase());
        if (!name) return { label: '(blank)', error: 'missing product name' };
        if (!p) return { label: name, error: 'product not found' };
        const newQty = Number(rawNew);
        if (rawNew === '' || rawNew === null || rawNew === undefined || Number.isNaN(newQty) || newQty < 0) {
          return { label: name, error: 'current_stock must be a number ≥ 0' };
        }
        const oldQty = p.stock ?? p.qty ?? 0;
        return { id: p.id, label: name, oldQty, newQty, changed: newQty !== oldQty };
      });
      setDiff(computed);
    } catch (err) {
      setReadError(err.message || 'Could not read the file.');
      setDiff(null);
    }
  };

  const reset = () => {
    setDiff(null); setFileName(''); setResult(null); setReadError('');
    if (fileRef.current) fileRef.current.value = '';
  };

  const save = async () => {
    if (!changed.length) return;
    setSaving(true);
    const updates = changed.map((r) => ({ product_id: r.id, actual_stock: r.newQty, name: r.label }));
    const res = await onStockUpdate(updates);
    setSaving(false);
    setResult(res);
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && !saving && onClose()}>
      <div className="modal modal-lg">
        <div className="modal-header">
          <span className="modal-title">Import Stock Update</span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose} disabled={saving}>✕</button>
        </div>

        {!diff && !result && (
          <div className="import-dropzone">
            <p className="import-hint">
              Export current stock, edit the <code>current_stock</code> column, then re-upload.
              Only changed quantities create a stock-adjustment transaction.
            </p>
            <button className="btn btn-secondary" onClick={() => exportCurrentStock(products)}>Export Current Stock</button>
            <button className="btn btn-primary" onClick={() => fileRef.current?.click()}>Choose Updated File…</button>
            <input ref={fileRef} type="file" accept=".xlsx,.xls" hidden onChange={onPick} />
            {readError && <div className="form-error-msg">{readError}</div>}
          </div>
        )}

        {diff && !result && (
          <div className="import-preview">
            <div className="import-stats">
              <span className="import-stat"><b>{diff.length}</b> rows</span>
              <span className="import-stat import-stat--ok"><b>{changed.length}</b> changed</span>
              <span className="import-stat import-stat--bad"><b>{unmatched.length}</b> unmatched</span>
              <span className="import-file">{fileName}</span>
            </div>

            {unmatched.length > 0 && (
              <div className="import-errors">
                <div className="import-errors-title">Skipped rows:</div>
                <ul>
                  {unmatched.slice(0, 50).map((r, i) => <li key={i}>{r.label}: {r.error}</li>)}
                </ul>
              </div>
            )}

            <div className="table-wrap scrollable" style={{ maxHeight: 260 }}>
              <table>
                <thead><tr><th>Product</th><th style={{ textAlign: 'right' }}>Old</th><th style={{ textAlign: 'right' }}>New</th><th style={{ textAlign: 'right' }}>Δ</th></tr></thead>
                <tbody>
                  {changed.length ? changed.map((r) => {
                    const delta = r.newQty - r.oldQty;
                    return (
                      <tr key={r.id}>
                        <td>{r.label}</td>
                        <td className="font-mono" style={{ textAlign: 'right' }}>{r.oldQty}</td>
                        <td className="font-mono" style={{ textAlign: 'right' }}>{r.newQty}</td>
                        <td className="font-mono" style={{ textAlign: 'right', color: delta > 0 ? 'var(--success)' : 'var(--danger)' }}>
                          {delta > 0 ? '+' : ''}{delta}
                        </td>
                      </tr>
                    );
                  }) : <tr><td colSpan={4}><div className="empty-state compact-empty"><span>No quantity changes detected.</span></div></td></tr>}
                </tbody>
              </table>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={reset} disabled={saving}>Choose Different File</button>
              <button className="btn btn-primary" onClick={save} disabled={saving || changed.length === 0}>
                {saving ? 'Updating…' : `Update ${changed.length} Item(s)`}
              </button>
            </div>
          </div>
        )}

        {result && (
          <div className="import-result">
            <div className="import-stats">
              <span className="import-stat import-stat--ok"><b>{result.saved}</b> updated</span>
              <span className="import-stat import-stat--bad"><b>{result.failed}</b> failed</span>
            </div>
            {result.errors?.length > 0 && (
              <div className="import-errors">
                <div className="import-errors-title">Failed updates:</div>
                <ul>{result.errors.slice(0, 50).map((e, i) => <li key={i}>{e.product}: {e.message}</li>)}</ul>
              </div>
            )}
            <div className="modal-footer">
              <button className="btn btn-primary" onClick={onClose}>Done</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
