/**
 * Maps your existing st() return values to styled pill badges.
 * Pass the result of st(product) directly as `status` prop.
 */
export default function StatusBadge({ status }) {
  const map = {
    // Stock levels
    'In Stock':     'badge-in',
    'Low Stock':    'badge-low',
    'Out':          'badge-out',
    'Out of Stock': 'badge-out',
    // Stock movements
    'Stock In':     'badge-in',
    'Stock Out':    'badge-out',
    'Adjusted':     'badge-ok',
    // Document / order states
    'Completed':    'badge-in',
    'Cancelled':    'badge-zero',
    // Supplier
    'GST Verified': 'badge-ok',
    'No GST':       'badge-zero',
  };

  const cls = map[status] || 'badge-ok';
  return <span className={`badge ${cls}`}>{status}</span>;
}