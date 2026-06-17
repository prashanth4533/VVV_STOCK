import { useRef, useState } from 'react';
import { downloadTemplate, parseSheet } from './utils/excel';

const COLUMNS = ['invoice_no', 'purchase_date', 'supplier', 'product', 'quantity', 'purchase_price', 'notes'];

export function downloadPurchaseTemplate(products = [], suppliers = []) {
  const firstProduct = products[0];
  const firstSupplier = suppliers[0];
  const productName = firstProduct
    ? `${firstProduct.brand || ''} ${firstProduct.item || ''} ${firstProduct.pack || firstProduct.unit || ''}`.trim()
    : 'MATHURA Toor Dal 1kg';
  const example = {
    invoice_no: 'INV-001',
    purchase_date: new Date().toISOString().slice(0, 10),
    supplier: firstSupplier?.name ?? 'ABC Traders',
    product: productName,
    quantity: 50,
    purchase_price: firstProduct?.purchasePrice ?? 120,
    notes: '',
  };
  downloadTemplate(COLUMNS, example, 'Purchases', 'purchase_import_template.xlsx');
}

function validateRows(rows, supplierNames, productNames) {
  const supSet = new Set((supplierNames || []).map((s) => s.trim().toLowerCase()));
  const prodSet = new Set((productNames || []).map((p) => p.trim().toLowerCase()));

  return rows.map((r, i) => {
    const errs = [];
    const get = (k) => String(r[k] ?? '').trim();

    if (!get('supplier')) errs.push('supplier is required');
    else if (supSet.size && !supSet.has(get('supplier').toLowerCase()))
      errs.push(`supplier "${get('supplier')}" not found`);

    if (!get('product')) errs.push('product is required');
    else if (prodSet.size && !prodSet.has(get('product').replace(/\s+/g, ' ').toLowerCase()))
      errs.push(`product "${get('product')}" not found`);

    const qty = Number(r.quantity);
    if (!get('quantity') || Number.isNaN(qty) || qty <= 0) errs.push('quantity must be > 0');

    const price = Number(r.purchase_price);
    if (!get('purchase_price') || Number.isNaN(price) || price <= 0) errs.push('purchase_price must be > 0');

    if (get('purchase_date') && !/^\d{4}-\d{2}-\d{2}$/.test(get('purchase_date')))
      errs.push('purchase_date must be YYYY-MM-DD');

    return { excelRow: i + 2, data: r, errors: errs, valid: errs.length === 0 };
  });
}

export default function PurchaseImportModal({ suppliers, products, onImport, onClose }) {
  const fileRef = useRef(null);
  const [fileName, setFileName] = useState('');
  const [checked, setChecked] = useState(null);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  const [readError, setReadError] = useState('');

  const supplierNames = (suppliers || []).map((s) => s.name || s);
  // Build product label list matching backend resolver: "brand item pack_size" and "brand item"
  const productNames = (products || []).flatMap((p) => {
    const norm = (s) => String(s || '').trim().replace(/\s+/g, ' ').toLowerCase();
    return [
      norm(`${p.brand} ${p.item} ${p.pack}`),
      norm(`${p.brand} ${p.item}`),
      norm(p.item),
      norm(`${p.brand} ${p.item} ${p.unit}`),
    ].filter(Boolean);
  });

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
      setChecked(validateRows(rows, supplierNames, productNames));
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
      invoice_no: r.data.invoice_no,
      purchase_date: r.data.purchase_date,
      supplier: r.data.supplier,
      product: r.data.product,
      quantity: r.data.quantity,
      purchase_price: r.data.purchase_price,
      notes: r.data.notes,
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
          <span className="modal-title">Import Purchases</span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose} disabled={saving}>✕</button>
        </div>

        {/* Step 1 — pick file */}
        {!checked && !result && (
          <div className="import-dropzone">
            <p className="import-hint">
              Download the template, fill in your purchase rows, then upload the file.
              Multiple products under the same <b>invoice_no</b> + <b>supplier</b> + <b>date</b> are saved as one purchase.
            </p>
            <button className="btn btn-secondary" onClick={() => downloadPurchaseTemplate(products, suppliers)}>Download Template</button>
            <button className="btn btn-primary" onClick={() => fileRef.current?.click()}>Choose Excel File…</button>
            <input ref={fileRef} type="file" accept=".xlsx,.xls" hidden onChange={onPick} />
            {readError && <div className="form-error-msg">{readError}</div>}
          </div>
        )}

        {/* Step 2 — preview */}
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

            <div className="table-wrap scrollable" style={{ maxHeight: 260 }}>
              <table>
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Supplier</th>
                    <th>Product</th>
                    <th>Invoice</th>
                    <th>Date</th>
                    <th style={{ textAlign: 'right' }}>Qty</th>
                    <th style={{ textAlign: 'right' }}>Rate</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {checked.slice(0, 200).map((r) => (
                    <tr key={r.excelRow}>
                      <td className="font-mono">{r.excelRow}</td>
                      <td>{r.data.supplier || '—'}</td>
                      <td>{r.data.product || '—'}</td>
                      <td>{r.data.invoice_no || '—'}</td>
                      <td>{r.data.purchase_date || '—'}</td>
                      <td className="font-mono" style={{ textAlign: 'right' }}>{r.data.quantity}</td>
                      <td className="font-mono" style={{ textAlign: 'right' }}>{r.data.purchase_price}</td>
                      <td>{r.valid ? <span className="badge badge-in">Valid</span> : <span className="badge badge-out">Invalid</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={reset} disabled={saving}>Choose Different File</button>
              <button className="btn btn-primary" onClick={save} disabled={saving || validRows.length === 0}>
                {saving ? 'Importing…' : `Import ${validRows.length} Row(s)`}
              </button>
            </div>
          </div>
        )}

        {/* Step 3 — result */}
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
                    <li key={i}>Row {e.row}: {e.message}</li>
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
