import { useMemo, useState } from 'react';
import MetricCard from './Metriccard';
import StatusBadge from './Statusbadge';

const today = () => new Date().toISOString().slice(0, 10);
const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0));
const formatDateTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

function productName(product) {
  return product.name || `${product.brand || ''} ${product.item || ''}`.trim() || 'Product';
}

function rowTotal(row) {
  return (Number(row.quantity) || 0) * (Number(row.rate) || 0);
}

function useLineItem(products) {
  const [item, setItem] = useState({ product_id: products[0]?.id || '', quantity: 1, rate: products[0]?.purchasePrice || products[0]?.sellingPrice || 1 });
  const set = (key, value) => setItem((current) => ({ ...current, [key]: value }));
  return [item, set, setItem];
}

export function InventoryPage({ products, stockLog = [], onStockIn, onAdjustment }) {
  const [tab, setTab] = useState('in');
  const [stockIn, setStockIn] = useState({ product_id: products[0]?.id || '', quantity: 1, notes: '' });
  const [adjustment, setAdjustment] = useState({ product_id: products[0]?.id || '', actual_stock: 0, reason: 'Correction', notes: '' });
  const selected = products.find((product) => product.id === Number(adjustment.product_id));
  const recentTransactions = [...stockLog]
    .sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0))
    .slice(0, 10);

  const submitStockIn = async (event) => {
    event.preventDefault();
    await onStockIn({
      product_id: Number(stockIn.product_id),
      quantity: Number(stockIn.quantity),
      notes: stockIn.notes || null,
    });
  };

  const submitAdjustment = async (event) => {
    event.preventDefault();
    await onAdjustment({
      product_id: Number(adjustment.product_id),
      actual_stock: Number(adjustment.actual_stock),
      reason: adjustment.reason,
      notes: adjustment.notes || null,
    });
  };

  return (
    <section className="screen-stack">
      <div className="grid-3">
        <MetricCard label="Tracked SKUs" value={products.length} sub="available products" accent="indigo" />
        <MetricCard label="Units On Hand" value={products.reduce((sum, product) => sum + (product.stock || 0), 0)} sub="current stock" accent="green" />
        <MetricCard label="Low / Out" value={products.filter((product) => (product.stock || 0) <= (product.low || 5)).length} sub="need attention" accent="amber" />
      </div>

      <div className="segmented">
        <button className={tab === 'in' ? 'active' : ''} onClick={() => setTab('in')}>Stock In</button>
        <button className={tab === 'adjust' ? 'active' : ''} onClick={() => setTab('adjust')}>Stock Adjustment</button>
      </div>

      {tab === 'in' ? (
        <form className="card form-card" onSubmit={submitStockIn}>
          <div className="page-header compact">
            <div>
              <div className="page-title">Stock In</div>
              <div className="page-subtitle">Receive new quantity into inventory</div>
            </div>
            <button className="btn btn-primary" disabled={!products.length}>Save Stock In</button>
          </div>
          <div className="grid-2">
            <ProductSelect products={products} value={stockIn.product_id} onChange={(value) => setStockIn((f) => ({ ...f, product_id: value }))} />
            <Field label="Quantity" type="number" min="1" value={stockIn.quantity} onChange={(value) => setStockIn((f) => ({ ...f, quantity: value }))} />
          </div>
          <Field label="Notes" value={stockIn.notes} onChange={(value) => setStockIn((f) => ({ ...f, notes: value }))} />
        </form>
      ) : (
        <form className="card form-card" onSubmit={submitAdjustment}>
          <div className="page-header compact">
            <div>
              <div className="page-title">Stock Adjustment</div>
              <div className="page-subtitle">Set actual physical count after verification</div>
            </div>
            <button className="btn btn-primary" disabled={!products.length}>Save Adjustment</button>
          </div>
          <div className="grid-2">
            <ProductSelect products={products} value={adjustment.product_id} onChange={(value) => setAdjustment((f) => ({ ...f, product_id: value, actual_stock: products.find((p) => p.id === Number(value))?.stock || 0 }))} />
            <Field label="Actual Stock" type="number" min="0" value={adjustment.actual_stock} onChange={(value) => setAdjustment((f) => ({ ...f, actual_stock: value }))} />
          </div>
          <div className="grid-2">
            <label className="form-group">
              <span className="form-label">Reason</span>
              <select className="input select" value={adjustment.reason} onChange={(event) => setAdjustment((f) => ({ ...f, reason: event.target.value }))}>
                {['Correction', 'Damage', 'Missing', 'Counting Error', 'Other'].map((reason) => <option key={reason}>{reason}</option>)}
              </select>
            </label>
            <div className="stock-preview">
              <span>System stock</span>
              <strong>{selected?.stock ?? 0}</strong>
            </div>
          </div>
          <Field label="Notes" value={adjustment.notes} onChange={(value) => setAdjustment((f) => ({ ...f, notes: value }))} />
        </form>
      )}

      <div className="card">
        <div className="page-header compact">
          <div>
            <div className="page-title">Recent Stock Transactions</div>
            <div className="page-subtitle">{recentTransactions.length} recent movements from database</div>
          </div>
        </div>
        <div className="table-wrap report-table">
          <table>
            <thead><tr><th>Date</th><th>Product</th><th>Type</th><th style={{ textAlign: 'right' }}>Qty</th><th>Notes</th></tr></thead>
            <tbody>
              {recentTransactions.length ? recentTransactions.map((txn) => (
                <tr key={txn.id}>
                  <td>{formatDateTime(txn.date)}</td>
                  <td>{productName(txn) || txn.sku || txn.product_id}</td>
                  <td><StatusBadge status={txn.type === 'out' ? 'Stock Out' : txn.type === 'in' ? 'Stock In' : 'Adjusted'} /></td>
                  <td className="font-mono" style={{ textAlign: 'right' }}>{txn.type === 'out' ? '-' : '+'}{txn.qty}</td>
                  <td>{txn.notes || txn.reason || '-'}</td>
                </tr>
              )) : <tr><td colSpan="5"><Empty text="No stock transactions found." /></td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export function PurchasesPage({ products, suppliers, purchases, onCreate, searchQuery }) {
  const [tab, setTab] = useState('entry');
  const [header, setHeader] = useState({ supplier_id: suppliers[0]?.id || '', purchase_date: today(), invoice_number: '', tax_amount: 0, notes: '' });
  const [item, setItem, setItemState] = useLineItem(products);
  const [items, setItems] = useState([]);
  const filtered = filterRows(purchases, searchQuery, ['purchase_no', 'invoice_number', 'status']);

  const addItem = () => {
    if (!item.product_id) return;
    setItems((current) => [...current, { ...item, product_id: Number(item.product_id), quantity: Number(item.quantity), rate: Number(item.rate) }]);
    setItemState({ product_id: products[0]?.id || '', quantity: 1, rate: products[0]?.purchasePrice || 1 });
  };

  const submit = async (event) => {
    event.preventDefault();
    await onCreate({
      supplier_id: Number(header.supplier_id),
      purchase_date: header.purchase_date || null,
      invoice_number: header.invoice_number || null,
      tax_amount: Number(header.tax_amount) || 0,
      notes: header.notes || null,
      items,
    });
    setItems([]);
  };

  return (
    <LedgerPage
      title="Purchases"
      tab={tab}
      onTab={setTab}
      entryLabel="Purchase Entry"
      historyLabel="Purchase History"
      entry={(
        <form className="card form-card" onSubmit={submit}>
          <div className="grid-3">
            <SupplierSelect suppliers={suppliers} value={header.supplier_id} onChange={(value) => setHeader((f) => ({ ...f, supplier_id: value }))} />
            <Field label="Purchase Date" type="date" value={header.purchase_date} onChange={(value) => setHeader((f) => ({ ...f, purchase_date: value }))} />
            <Field label="Invoice Number" value={header.invoice_number} onChange={(value) => setHeader((f) => ({ ...f, invoice_number: value }))} />
          </div>
          <LineItemBuilder products={products} item={item} setItem={setItem} onAdd={addItem} rateLabel="Purchase Rate" />
          <LineItemsTable items={items} products={products} onRemove={(idx) => setItems((current) => current.filter((_, index) => index !== idx))} />
          <div className="grid-2">
            <Field label="Tax Amount" type="number" min="0" value={header.tax_amount} onChange={(value) => setHeader((f) => ({ ...f, tax_amount: value }))} />
            <Field label="Notes" value={header.notes} onChange={(value) => setHeader((f) => ({ ...f, notes: value }))} />
          </div>
          <FormTotal items={items} extra={Number(header.tax_amount) || 0} />
          <button className="btn btn-primary" disabled={!items.length || !header.supplier_id}>Save Purchase</button>
        </form>
      )}
      history={<HistoryTable rows={filtered} type="purchase" empty="No purchases found." />}
    />
  );
}

export function SalesPage({ products, sales, onCreate, searchQuery }) {
  const [tab, setTab] = useState('entry');
  const [header, setHeader] = useState({ customer_name: '', customer_mobile: '', sale_date: today(), discount_amount: 0, notes: '' });
  const [item, setItem, setItemState] = useLineItem(products);
  const [items, setItems] = useState([]);
  const filtered = filterRows(sales, searchQuery, ['sale_no', 'customer_name', 'status']);

  const addItem = () => {
    if (!item.product_id) return;
    setItems((current) => [...current, { ...item, product_id: Number(item.product_id), quantity: Number(item.quantity), rate: Number(item.rate) }]);
    setItemState({ product_id: products[0]?.id || '', quantity: 1, rate: products[0]?.sellingPrice || 1 });
  };

  const submit = async (event) => {
    event.preventDefault();
    await onCreate({
      customer_name: header.customer_name,
      customer_mobile: header.customer_mobile || null,
      sale_date: header.sale_date || null,
      discount_amount: Number(header.discount_amount) || 0,
      notes: header.notes || null,
      items,
    });
    setItems([]);
  };

  return (
    <LedgerPage
      title="Sales"
      tab={tab}
      onTab={setTab}
      entryLabel="Sales Entry"
      historyLabel="Sales History"
      entry={(
        <form className="card form-card" onSubmit={submit}>
          <div className="grid-3">
            <Field label="Customer Name" value={header.customer_name} onChange={(value) => setHeader((f) => ({ ...f, customer_name: value }))} />
            <Field label="Mobile" value={header.customer_mobile} onChange={(value) => setHeader((f) => ({ ...f, customer_mobile: value }))} />
            <Field label="Sale Date" type="date" value={header.sale_date} onChange={(value) => setHeader((f) => ({ ...f, sale_date: value }))} />
          </div>
          <LineItemBuilder products={products} item={item} setItem={setItem} onAdd={addItem} rateLabel="Sale Rate" />
          <LineItemsTable items={items} products={products} onRemove={(idx) => setItems((current) => current.filter((_, index) => index !== idx))} />
          <div className="grid-2">
            <Field label="Discount" type="number" min="0" value={header.discount_amount} onChange={(value) => setHeader((f) => ({ ...f, discount_amount: value }))} />
            <Field label="Notes" value={header.notes} onChange={(value) => setHeader((f) => ({ ...f, notes: value }))} />
          </div>
          <FormTotal items={items} extra={-(Number(header.discount_amount) || 0)} />
          <button className="btn btn-primary" disabled={!items.length || !header.customer_name.trim()}>Save Sale</button>
        </form>
      )}
      history={<HistoryTable rows={filtered} type="sale" empty="No sales found." />}
    />
  );
}

export function SuppliersPage({ suppliers, onSave, searchQuery }) {
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', contact_person: '', mobile: '', address: '', gst: '', notes: '' });
  const filtered = filterRows(suppliers, searchQuery, ['name', 'contact', 'mobile', 'gst']);
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const edit = (supplier) => {
    setEditing(supplier.id);
    setForm({
      name: supplier.name || '',
      contact_person: supplier.contact || '',
      mobile: supplier.mobile || '',
      address: supplier.address || '',
      gst: supplier.gst || '',
      notes: supplier.notes || '',
    });
  };

  const submit = async (event) => {
    event.preventDefault();
    await onSave(form, editing);
    setEditing(null);
    setForm({ name: '', contact_person: '', mobile: '', address: '', gst: '', notes: '' });
  };

  return (
    <section className="split-screen">
      <form className="card form-card" onSubmit={submit}>
        <div className="page-header compact">
          <div>
            <div className="page-title">{editing ? 'Edit Supplier' : 'Supplier Form'}</div>
            <div className="page-subtitle">Supplier contact and GST details</div>
          </div>
        </div>
        <Field label="Supplier Name" value={form.name} onChange={(value) => set('name', value)} />
        <div className="grid-2">
          <Field label="Contact Person" value={form.contact_person} onChange={(value) => set('contact_person', value)} />
          <Field label="Mobile" value={form.mobile} onChange={(value) => set('mobile', value)} />
        </div>
        <Field label="Address" value={form.address} onChange={(value) => set('address', value)} />
        <div className="grid-2">
          <Field label="GST" value={form.gst} onChange={(value) => set('gst', value)} />
          <Field label="Notes" value={form.notes} onChange={(value) => set('notes', value)} />
        </div>
        <button className="btn btn-primary" disabled={!form.name.trim()}>{editing ? 'Update Supplier' : 'Add Supplier'}</button>
      </form>

      <div className="card">
        <div className="page-header compact">
          <div>
            <div className="page-title">Supplier List</div>
            <div className="page-subtitle">{filtered.length} suppliers</div>
          </div>
        </div>
        <div className="supplier-list">
          {filtered.length ? filtered.map((supplier) => (
            <button className="supplier-row" key={supplier.id} onClick={() => edit(supplier)}>
              <span>
                <strong>{supplier.name}</strong>
                <small>{supplier.contact || supplier.mobile || 'No contact added'}</small>
              </span>
              <StatusBadge status={supplier.gst ? 'GST Verified' : 'No GST'} />
            </button>
          )) : <Empty text="No suppliers found." />}
        </div>
      </div>
    </section>
  );
}

export function ReportsPage({ products, purchases, sales, stockLog, onExport }) {
  const low = products.filter((product) => (product.stock || 0) <= (product.low || 5));
  const timeline = [
    ...purchases.map((item) => ({ type: 'Purchase', date: item.purchase_date, title: item.purchase_no, amount: item.total_amount })),
    ...sales.map((item) => ({ type: 'Sale', date: item.sale_date, title: item.sale_no, amount: item.total_amount })),
    ...stockLog.map((item) => ({ type: item.type || 'Stock', date: item.date, title: productName(item), amount: item.added })),
  ].sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0, 12);

  return (
    <section className="screen-stack">
      <div className="grid-4">
        <MetricCard label="Products" value={products.length} sub="active SKUs" accent="indigo" />
        <MetricCard label="Low/Out" value={low.length} sub="EOD focus" accent="amber" />
        <MetricCard label="Purchases" value={purchases.length} sub="history rows" accent="green" />
        <MetricCard label="Sales" value={sales.length} sub="history rows" accent="red" />
      </div>

      <div className="report-actions">
        <button className="btn btn-primary" onClick={onExport}>Export Workbook</button>
        <button className="btn btn-secondary" onClick={() => window.print()}>Print Report</button>
      </div>

      <div className="split-screen">
        <div className="card">
          <div className="page-title">EOD History</div>
          <div className="page-subtitle">Current exceptions for daily verification</div>
          <div className="table-wrap report-table">
            <table>
              <thead><tr><th>Product</th><th>Stock</th><th>Status</th></tr></thead>
              <tbody>
                {low.length ? low.map((product) => (
                  <tr key={product.id}>
                    <td>{productName(product)}</td>
                    <td className="font-mono">{product.stock}</td>
                    <td><StatusBadge status={(product.stock || 0) === 0 ? 'Out' : 'Low Stock'} /></td>
                  </tr>
                )) : <tr><td colSpan="3"><Empty text="No EOD exceptions." /></td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="page-title">Activity Timeline</div>
          <div className="timeline">
            {timeline.length ? timeline.map((item, index) => (
              <div className="timeline-item" key={`${item.type}-${index}`}>
                <span className="timeline-dot" />
                <div>
                  <strong>{item.title || item.type}</strong>
                  <small>{item.type} {item.date ? `on ${item.date}` : ''}</small>
                </div>
                <span>{typeof item.amount === 'number' ? money(item.amount) : item.amount}</span>
              </div>
            )) : <Empty text="No recent activity." />}
          </div>
        </div>
      </div>
    </section>
  );
}

function LedgerPage({ title, tab, onTab, entryLabel, historyLabel, entry, history }) {
  return (
    <section className="screen-stack">
      <div className="page-header">
        <div>
          <div className="page-title">{title}</div>
          <div className="page-subtitle">Entry workflow and searchable history</div>
        </div>
        <div className="segmented inline">
          <button className={tab === 'entry' ? 'active' : ''} onClick={() => onTab('entry')}>{entryLabel}</button>
          <button className={tab === 'history' ? 'active' : ''} onClick={() => onTab('history')}>{historyLabel}</button>
        </div>
      </div>
      {tab === 'entry' ? entry : history}
    </section>
  );
}

function LineItemBuilder({ products, item, setItem, onAdd, rateLabel }) {
  const selected = products.find((product) => product.id === Number(item.product_id));
  return (
    <div className="line-builder">
      <ProductSelect products={products} value={item.product_id} onChange={(value) => setItem('product_id', value)} />
      <Field label="Qty" type="number" min="1" value={item.quantity} onChange={(value) => setItem('quantity', value)} />
      <Field label={rateLabel} type="number" min="0.01" step="0.01" value={item.rate} onChange={(value) => setItem('rate', value)} />
      <div className="stock-preview">
        <span>Available</span>
        <strong>{selected?.stock ?? 0}</strong>
      </div>
      <button className="btn btn-secondary" type="button" onClick={onAdd}>Add Line</button>
    </div>
  );
}

function LineItemsTable({ items, products, onRemove }) {
  if (!items.length) return <Empty text="No line items added." />;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Product</th><th>Qty</th><th>Rate</th><th>Total</th><th></th></tr></thead>
        <tbody>
          {items.map((item, index) => {
            const product = products.find((entry) => entry.id === item.product_id);
            return (
              <tr key={`${item.product_id}-${index}`}>
                <td>{product ? productName(product) : item.product_id}</td>
                <td>{item.quantity}</td>
                <td>{money(item.rate)}</td>
                <td>{money(rowTotal(item))}</td>
                <td><button className="btn btn-ghost btn-sm" type="button" onClick={() => onRemove(index)}>Remove</button></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FormTotal({ items, extra = 0 }) {
  const subtotal = items.reduce((sum, item) => sum + rowTotal(item), 0);
  return (
    <div className="form-total">
      <span>Subtotal <strong>{money(subtotal)}</strong></span>
      <span>Total <strong>{money(subtotal + extra)}</strong></span>
    </div>
  );
}

function HistoryTable({ rows, type, empty }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>No</th><th>Date</th><th>Name</th><th>Status</th><th>Total</th></tr>
        </thead>
        <tbody>
          {rows.length ? rows.map((row) => (
            <tr key={row.id}>
              <td className="font-mono">{type === 'purchase' ? row.purchase_no : row.sale_no}</td>
              <td>{type === 'purchase' ? row.purchase_date : row.sale_date}</td>
              <td>{type === 'purchase' ? row.supplier?.name : row.customer_name}</td>
              <td><StatusBadge status={row.status === 'cancelled' ? 'Cancelled' : 'Completed'} /></td>
              <td>{money(row.total_amount)}</td>
            </tr>
          )) : <tr><td colSpan="5"><Empty text={empty} /></td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function ProductSelect({ products, value, onChange }) {
  return (
    <label className="form-group">
      <span className="form-label">Product</span>
      <select className="input select" value={value} onChange={(event) => onChange(event.target.value)}>
        {products.map((product) => <option key={product.id} value={product.id}>{productName(product)} - {product.unit}</option>)}
      </select>
    </label>
  );
}

function SupplierSelect({ suppliers, value, onChange }) {
  return (
    <label className="form-group">
      <span className="form-label">Supplier</span>
      <select className="input select" value={value} onChange={(event) => onChange(event.target.value)}>
        {suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}
      </select>
    </label>
  );
}

function Field({ label, value, onChange, ...props }) {
  return (
    <label className="form-group">
      <span className="form-label">{label}</span>
      <input className="input" value={value} onChange={(event) => onChange(event.target.value)} {...props} />
    </label>
  );
}

function Empty({ text }) {
  return <div className="empty-state compact-empty"><span>{text}</span></div>;
}

function filterRows(rows, query, fields) {
  if (!query) return rows;
  const q = query.toLowerCase();
  return rows.filter((row) => fields.some((field) => String(row[field] || '').toLowerCase().includes(q)));
}
