import { useState, useMemo } from 'react';
import StatusBadge from './Statusbadge';

export default function Products({ data, CATS, st, onAddProduct, searchQuery }) {
  const { products = [] } = data;

  const [catFilter, setCatFilter] = useState('All');
  const [sortKey, setSortKey] = useState('name');
  const [sortDir, setSortDir] = useState('asc');
  const [showAddModal, setShowAddModal] = useState(false);

  // ── Filter + sort ────────────────────────────────────────
  const filtered = useMemo(() => {
    let list = products;
    if (catFilter !== 'All') list = list.filter(p => p.category === catFilter);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(p =>
        (p.name || '').toLowerCase().includes(q) ||
        (p.category || '').toLowerCase().includes(q) ||
        (p.supplier || '').toLowerCase().includes(q)
      );
    }
    return [...list].sort((a, b) => {
      let av = a[sortKey] ?? '', bv = b[sortKey] ?? '';
      if (typeof av === 'string') av = av.toLowerCase();
      if (typeof bv === 'string') bv = bv.toLowerCase();
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [products, catFilter, sortKey, sortDir, searchQuery]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <span className="sort-icon sort-icon--idle">↕</span>;
    return <span className="sort-icon sort-icon--active">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  const categories = ['All', ...(CATS || [])];

  return (
    <div>
      {/* ── Page header ──────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <div className="page-title">Products</div>
          <div className="page-subtitle">{filtered.length} of {products.length} products</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
          <svg viewBox="0 0 16 16" fill="none" width="13" height="13">
            <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          Add Product
        </button>
      </div>

      {/* ── Category filter pills ─────────────────────────────── */}
      <div className="cat-pills">
        {categories.map(cat => (
          <button
            key={cat}
            className={`cat-pill ${catFilter === cat ? 'cat-pill--active' : ''}`}
            onClick={() => setCatFilter(cat)}
          >
            {cat}
            {cat !== 'All' && (
              <span className="cat-pill-count">
                {products.filter(p => p.category === cat).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Table ────────────────────────────────────────────── */}
      <div className="table-wrap scrollable products-table">
        <table>
          <thead>
            <tr>
              <th onClick={() => toggleSort('name')} style={{ cursor: 'pointer' }}>
                Product <SortIcon col="name" />
              </th>
              <th onClick={() => toggleSort('category')} style={{ cursor: 'pointer' }}>
                Category <SortIcon col="category" />
              </th>
              <th onClick={() => toggleSort('stock')} style={{ cursor: 'pointer', textAlign: 'right' }}>
                Current Stock <SortIcon col="stock" />
              </th>
              <th style={{ textAlign: 'right' }}>Reorder Level</th>
              <th>Status</th>
              <th>Supplier</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state">
                    <span className="empty-state-icon">📦</span>
                    <span>{products.length === 0 ? 'Add your first product to get started.' : 'No products match the current filter.'}</span>
                  </div>
                </td>
              </tr>
            ) : filtered.map((p, i) => {
              const status = st ? st(p) : (p.stock === 0 ? 'Out' : p.stock <= (p.low || 5) ? 'Low Stock' : 'In Stock');
              const stockClass = status === 'Out' ? 'stock-qty--out' : status === 'Low Stock' ? 'stock-qty--low' : 'stock-qty--ok';
              return (
                <tr key={i}>
                  <td>
                    <div className="product-name">{p.name}</div>
                    {p.unit && <div className="product-unit">{p.unit}</div>}
                  </td>
                  <td>
                    <span className="category-tag">{p.category || '—'}</span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`font-mono stock-qty ${stockClass}`}>{p.stock ?? 0}</span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className="font-mono reorder-level">{p.low ?? 5}</span>
                  </td>
                  <td>
                    <StatusBadge status={status} />
                  </td>
                  <td className="supplier-cell">{p.supplier || '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── Add product modal ─────────────────────────────────── */}
      {showAddModal && (
        <AddProductModal
          CATS={CATS}
          onClose={() => setShowAddModal(false)}
          onAdd={(product) => { onAddProduct?.(product); setShowAddModal(false); }}
        />
      )}
    </div>
  );
}

function AddProductModal({ CATS, onClose, onAdd }) {
  const [form, setForm] = useState({
    name: '', category: (CATS || [])[0] || '', stock: '', low: '5', unit: '', supplier: '',
  });
  const [errors, setErrors] = useState({});

  const set = (k, v) => {
    setForm(f => ({ ...f, [k]: v }));
    if (errors[k]) setErrors(e => ({ ...e, [k]: '' }));
  };

  const validate = () => {
    const next = {};
    if (!form.name.trim()) next.name = 'Product name is required';
    return next;
  };

  const handleSubmit = () => {
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    onAdd({
      ...form,
      stock: parseInt(form.stock) || 0,
      low: parseInt(form.low) || 5,
    });
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">Add New Product</span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="modal-form-body">
          <div className="form-group">
            <label className="form-label">Product Name <span className="form-required">*</span></label>
            <input
              className={`input${errors.name ? ' input--error' : ''}`}
              placeholder="e.g. Basmati Rice 5kg"
              value={form.name}
              onChange={e => set('name', e.target.value)}
              autoFocus
            />
            {errors.name && <span className="form-error-msg">{errors.name}</span>}
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Category</label>
              <select className="input select" value={form.category} onChange={e => set('category', e.target.value)}>
                {(CATS || []).map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Unit</label>
              <input className="input" placeholder="kg, pcs, ltr…" value={form.unit} onChange={e => set('unit', e.target.value)} />
            </div>
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Opening Stock</label>
              <input className="input" type="number" min="0" placeholder="0" value={form.stock} onChange={e => set('stock', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Reorder Level</label>
              <input className="input" type="number" min="0" placeholder="5" value={form.low} onChange={e => set('low', e.target.value)} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Supplier</label>
            <input className="input" placeholder="Optional" value={form.supplier} onChange={e => set('supplier', e.target.value)} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit}>
            Add Product
          </button>
        </div>
      </div>
    </div>
  );
}
