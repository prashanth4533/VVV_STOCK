import { useRef, useState } from 'react';
import { downloadTemplate, parseSheet } from './utils/excel';

/**
 * Product bulk import — Download Template + Import Excel.
 * Flow: Upload → Validate (client-side) → Preview → Save (backend bulkImport) → refresh.
 *
 * Validation here is a pre-check for the preview; the backend re-validates and
 * resolves category/supplier names, returning authoritative per-row errors on save.
 */

const COLUMNS = [
  'brand', 'item', 'pack_size', 'category', 'supplier',
  'opening_stock', 'reorder_level', 'purchase_price', 'selling_price',
];

const TEMPLATE_EXAMPLE = {
  brand: 'MATHURA',
  item: 'Toor Dal',
  pack_size: '1kg',
  category: 'Toor Dal',
  supplier: 'ABC Traders',
  opening_stock: 100,
  reorder_level: 10,
  purchase_price: 120,
  selling_price: 140,
};

export function downloadProductTemplate() {
  downloadTemplate(COLUMNS, TEMPLATE_EXAMPLE, 'Products', 'product_import_template.xlsx');
}

function validateRows(rows, categories, suppliers) {
  const catSet = new Set((categories || []).map((c) => String(c).trim().toLowerCase()));
  const supSet = new Set((suppliers || []).map((s) => String(s.name || s).trim().toLowerCase()));
  const num = (v) => (v === '' || v === null || v === undefined ? 0 : Number(v));

  return rows.map((r, i) => {
    const errs = [];
    const get = (k) => String(r[k] ?? '').trim();
    if (!get('brand')) errs.push('brand is required');
    if (!get('item')) errs.push('item is required');
    if (!get('pack_size')) errs.push('pack_size is required');
    const cat = get('category');
    if (!cat) errs.push('category is required');
    else if (!catSet.has(cat.toLowerCase())) errs.push(`category "${cat}" not found`);
    const sup = get('supplier');
    if (sup && !supSet.has(sup.toLowerCase())) errs.push(`supplier "${sup}" not found`);
    if (get('opening_stock') && Number.isNaN(num(r.opening_stock))) errs.push('opening_stock must be a number');
    if (get('reorder_level') && Number.isNaN(num(r.reorder_level))) errs.push('reorder_level must be a number');
    if (get('purchase_price') && Number.isNaN(num(r.purchase_price))) errs.push('purchase_price must be a number');
    if (get('selling_price') && Number.isNaN(num(r.selling_price))) errs.push('selling_price must be a number');
    return { excelRow: i + 2, data: r, errors: errs, valid: errs.length === 0 };
  });
}

export default function ProductImportModal({ categories, suppliers, onImport, onClose }) {
  const fileRef = useRef(null);
  const [fileName, setFileName] = useState('');
  const [checked, setChecked] = useState(null);   // validated rows
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);      // backend result
  const [readError, setReadError] = useState('');

  const validRows = checked ? checked.filter((r) => r.valid) : [];
  const invalidRows = checked ? checked.filter((r) => !r.valid) : [];

  const onPick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setReadError(''); setResult(null);
    setFileName(file.name);
    try {
      const rows = await parseSheet(file);
      if (!rows.length) { setReadError('The sheet has no data rows.'); setChecked([]); return; }
      setChecked(validateRows(rows, categories, suppliers));
    } catch (err) {
      setReadError(err.message || 'Could not read the file.');
      setChecked(null);
    }
  };

  const reset = () => {
    setChecked(null); setFileName(''); setResult(null); setReadError('');
    if (fileRef.current) fileRef.current.value = '';
  };

  const save = async () => {
    if (!validRows.length) return;
    setSaving(true);
    const payload = validRows.map((r) => ({
      brand: r.data.brand, item: r.data.item, pack_size: r.data.pack_size,
      category: r.data.category, supplier: r.data.supplier,
      opening_stock: r.data.opening_stock, reorder_level: r.data.reorder_level,
      purchase_price: r.data.purchase_price, selling_price: r.data.selling_price,
    }));
    try {
      const res = await onImport(payload);
      setResult(res ?? { total: payload.length, saved: 0, failed: payload.length, errors: [{ row: '-', message: 'No response from server.' }] });
    } catch (err) {
      setResult({ total: payload.length, saved: 0, failed: payload.length, errors: [{ row: '-', message: err.message || 'Import failed.' }] });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && !saving && onClose()}>
      <div className="modal modal-lg">
        <div className="modal-header">
          <span className="modal-title">Import Products</span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose} disabled={saving}>✕</button>
        </div>

        {/* Step 1: pick file */}
        {!checked && !result && (
          <div className="import-dropzone">
            <p className="import-hint">
              Upload an .xlsx file using the template columns:
              <code>brand, item, pack_size, category, supplier, opening_stock, reorder_level, purchase_price, selling_price</code>
            </p>
            <button className="btn btn-secondary" onClick={() => downloadProductTemplate()}>Download Template</button>
            <button className="btn btn-primary" onClick={() => fileRef.current?.click()}>Choose Excel File…</button>
            <input ref={fileRef} type="file" accept=".xlsx,.xls" hidden onChange={onPick} />
            {readError && <div className="form-error-msg">{readError}</div>}
          </div>
        )}

        {/* Step 2: preview */}
        {checked && !result && (
          <div className="import-preview">
            <div className="import-stats">
              <span className="import-stat"><b>{checked.length}</b> total</span>
              <span className="import-stat import-stat--ok"><b>{validRows.length}</b> valid</span>
              <span className="import-stat import-stat--bad"><b>{invalidRows.length}</b> invalid</span>
              <span className="import-file">{fileName}</span>
            </div>

            {invalidRows.length > 0 && (
              <div className="import-errors">
                <div className="import-errors-title">Validation errors (these rows are skipped):</div>
                <ul>
                  {invalidRows.slice(0, 50).map((r) => (
                    <li key={r.excelRow}>Row {r.excelRow}: {r.errors.join('; ')}</li>
                  ))}
                  {invalidRows.length > 50 && <li>…and {invalidRows.length - 50} more</li>}
                </ul>
              </div>
            )}

            <div className="table-wrap scrollable" style={{ maxHeight: 240 }}>
              <table>
                <thead><tr><th>Row</th><th>Brand</th><th>Item</th><th>Category</th><th>Supplier</th><th style={{ textAlign: 'right' }}>Stock</th><th>Status</th></tr></thead>
                <tbody>
                  {checked.slice(0, 200).map((r) => (
                    <tr key={r.excelRow}>
                      <td className="font-mono">{r.excelRow}</td>
                      <td>{r.data.brand}</td>
                      <td>{r.data.item}</td>
                      <td>{r.data.category}</td>
                      <td>{r.data.supplier || '—'}</td>
                      <td className="font-mono" style={{ textAlign: 'right' }}>{r.data.opening_stock || 0}</td>
                      <td>{r.valid ? <span className="badge badge-in">Valid</span> : <span className="badge badge-out">Invalid</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={reset} disabled={saving}>Choose Different File</button>
              <button className="btn btn-primary" onClick={save} disabled={saving || validRows.length === 0}>
                {saving ? 'Importing…' : `Import ${validRows.length} Product(s)`}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: result */}
        {result && (
          <div className="import-result">
            <div className="import-stats">
              <span className="import-stat import-stat--ok"><b>{result.saved}</b> imported</span>
              <span className="import-stat import-stat--bad"><b>{result.failed}</b> failed</span>
            </div>
            {result.errors?.length > 0 && (
              <div className="import-errors">
                <div className="import-errors-title">Rows the server could not save:</div>
                <ul>
                  {result.errors.slice(0, 50).map((e, i) => (
                    <li key={i}>Row {e.row} ({e.field}): {e.message}</li>
                  ))}
                </ul>
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
