import { useCallback, useEffect, useMemo, useState } from 'react';
import * as XLSX from 'xlsx';
import { AppProvider, useApp } from './Appcontext';
import Layout from './Layout';
import Dashboard from './Dashboard';
import Products from './Products';
import { ProductsAPI } from './api/products';
import { CategoriesAPI } from './api/categories';
import { SuppliersAPI } from './api/suppliers';
import { PurchasesAPI } from './api/purchases';
import { SalesAPI } from './api/sales';
import { StockTransactionsAPI } from './api/stock_transactions';
import {
  InventoryPage,
  PurchasesPage,
  SalesPage,
  SuppliersPage,
  ReportsPage,
} from './Screens';

function normalizeSupplier(supplier) {
  return {
    id: supplier.id,
    name: supplier.name || '',
    contact: supplier.contact || supplier.contact_person || '',
    mobile: supplier.mobile || supplier.phone || '',
    address: supplier.address || '',
    gst: supplier.gst || supplier.gst_no || '',
    notes: supplier.notes || '',
  };
}

function makeUiProduct(product, suppliers) {
  const supplier = suppliers.find((item) => item.id === product.supplierId);
  return {
    ...product,
    name: `${product.brand || ''} ${product.item || ''}`.trim(),
    category: product.cat,
    stock: product.qty,
    low: product.reorderLevel,
    unit: product.pack,
    supplier: supplier?.name || '',
  };
}

function normalizeTransactionType(entry) {
  const rawType = String(entry.transaction_type || entry.type || '').toUpperCase();
  const change = Number(entry.quantity_change ?? entry.added ?? entry.qty ?? 0);
  if (rawType === 'STOCK_OUT' || change < 0) return 'out';
  if (rawType === 'STOCK_IN' || rawType === 'NEW_PRODUCT' || change > 0) return 'in';
  return 'adjust';
}

function normalizeTransaction(entry) {
  const product = entry.product || {};
  const transactionDate = entry.transaction_date || entry.date || entry.created_at;
  const transactionTime = entry.transaction_time || entry.time;
  return {
    ...entry,
    rawType: entry.transaction_type || entry.type,
    type: normalizeTransactionType(entry),
    qty: Math.abs(entry.quantity_change ?? entry.qty ?? 0),
    added: entry.quantity_change ?? entry.added ?? 0,
    oldQty: entry.previous_qty,
    newQty: entry.new_qty,
    date: transactionDate && transactionTime ? `${transactionDate}T${transactionTime}` : transactionDate,
    time: transactionTime,
    brand: product.brand || entry.brand,
    item: product.item || entry.item,
    pack: product.pack_size || entry.pack,
    sku: product.sku || entry.sku,
    name: `${product.brand || entry.brand || ''} ${product.item || entry.item || ''}`.trim(),
    notes: entry.notes || entry.reason || '',
  };
}

function stockStatus(product) {
  const qty = product.stock ?? product.qty ?? 0;
  const low = product.low ?? product.reorderLevel ?? 5;
  if (qty === 0) return 'Out';
  if (qty <= low) return 'Low Stock';
  return 'In Stock';
}

function apiCount(result) {
  if (Array.isArray(result)) return result.length;
  if (Array.isArray(result?.data)) return result.data.length;
  if (result?.meta?.total !== undefined) return result.meta.total;
  if (result?.data && typeof result.data === 'object') return 1;
  return 0;
}

function logScreenBindings(report) {
  console.table(report.map((row) => ({
    'Screen Name': row.screen,
    'API Used': row.api,
    'Records Returned': row.records,
    'UI Component Updated': row.component,
  })));

  report.forEach((row) => {
    if (row.records > 0 && row.uiRows === 0) {
      console.warn('[UI Data Binding] API returned data but UI rows are empty:', row);
    }
  });
}

function exportWorkbook({ products, suppliers, purchases, sales, stockLog }) {
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(products), 'Products');
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(suppliers), 'Suppliers');
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(purchases), 'Purchases');
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(sales), 'Sales');
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(stockLog), 'Activity');
  XLSX.writeFile(wb, `VVV_Stock_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

export default function App() {
  return (
    <AppProvider>
      <RedesignedApp />
    </AppProvider>
  );
}

function RedesignedApp() {
  const { toast } = useApp();
  const [activePage, setActivePage] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [sales, setSales] = useState([]);
  const [stockLog, setStockLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const supplierOptions = useMemo(() => suppliers.map(normalizeSupplier), [suppliers]);
  const uiProducts = useMemo(() => products.map((product) => makeUiProduct(product, supplierOptions)), [products, supplierOptions]);
  const data = useMemo(() => ({
    products: uiProducts,
    suppliers: supplierOptions,
    purchases,
    sales,
    stockLog,
    eodHistory: [],
  }), [uiProducts, supplierOptions, purchases, sales, stockLog]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [nextProducts, nextCategories, nextSuppliers, nextPurchases, nextSales, nextTransactions] = await Promise.all([
        ProductsAPI.getAll(),
        CategoriesAPI.getAll(),
        SuppliersAPI.getAll(),
        PurchasesAPI.getAll({ per_page: 100 }),
        SalesAPI.getAll({ per_page: 100 }),
        StockTransactionsAPI.getAll({ per_page: 100 }),
      ]);
      const purchaseRows = nextPurchases.data || [];
      const saleRows = nextSales.data || [];
      const transactionRows = (nextTransactions?.data || []).map(normalizeTransaction);
      const normalizedSuppliers = nextSuppliers.map(normalizeSupplier);
      const uiProductRows = nextProducts.map((product) => makeUiProduct(product, normalizedSuppliers));

      setProducts(nextProducts);
      setCategories(nextCategories);
      setSuppliers(nextSuppliers);
      setPurchases(purchaseRows);
      setSales(saleRows);
      setStockLog(transactionRows);

      logScreenBindings([
        { screen: 'Dashboard', api: 'GET /api/v1/products, GET /api/v1/stock-transactions', records: apiCount(nextProducts) + apiCount(nextTransactions), uiRows: uiProductRows.length + transactionRows.length, component: 'MetricCard, Stock Status, Activity Log' },
        { screen: 'Products', api: 'GET /api/v1/products', records: apiCount(nextProducts), uiRows: uiProductRows.length, component: 'Products table and category filters' },
        { screen: 'Suppliers', api: 'GET /api/v1/suppliers', records: apiCount(nextSuppliers), uiRows: normalizedSuppliers.length, component: 'Supplier List' },
        { screen: 'Purchases', api: 'GET /api/v1/purchases', records: apiCount(nextPurchases), uiRows: purchaseRows.length, component: 'Purchase History table' },
        { screen: 'Sales', api: 'GET /api/v1/sales', records: apiCount(nextSales), uiRows: saleRows.length, component: 'Sales History table' },
        { screen: 'Stock In', api: 'GET /api/v1/products, GET /api/v1/stock-transactions', records: apiCount(nextProducts) + apiCount(nextTransactions), uiRows: uiProductRows.length + transactionRows.length, component: 'Stock forms and Recent Stock Transactions' },
        { screen: 'Reports', api: 'GET /api/v1/products, GET /api/v1/purchases, GET /api/v1/sales, GET /api/v1/stock-transactions', records: apiCount(nextProducts) + apiCount(nextPurchases) + apiCount(nextSales) + apiCount(nextTransactions), uiRows: uiProductRows.length + purchaseRows.length + saleRows.length + transactionRows.length, component: 'EOD History and Activity Timeline' },
      ]);
    } catch (err) {
      setError(err.message || 'Unable to load data');
      toast(err.message || 'Unable to load data', 'error');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const catMap = useMemo(() => {
    return categories.reduce((acc, category) => {
      acc[category.name] = category.id;
      return acc;
    }, {});
  }, [categories]);

  const handleAddProduct = async (form) => {
    const [brand, ...rest] = form.name.trim().split(' ');
    try {
      await ProductsAPI.create({
        brand: brand || form.name,
        item: rest.join(' ') || form.name,
        pack: form.unit || 'Unit',
        cat: form.category,
        qty: form.stock,
        reorderLevel: form.low,
        supplierId: '',
      }, catMap);
      toast('Product added');
      loadAll();
    } catch (err) {
      toast(err.message || 'Product could not be added', 'error');
    }
  };

  const handleStockIn = async (payload) => {
    await StockTransactionsAPI.stockIn(payload);
    toast('Stock received');
    await loadAll();
  };

  const handleAdjustment = async (payload) => {
    await StockTransactionsAPI.adjustment(payload);
    toast('Stock adjusted');
    await loadAll();
  };

  const handleCreatePurchase = async (payload) => {
    await PurchasesAPI.create(payload);
    toast('Purchase saved');
    await loadAll();
  };

  const handleCreateSale = async (payload) => {
    await SalesAPI.create(payload);
    toast('Sale saved');
    await loadAll();
  };

  const handleSaveSupplier = async (payload, id) => {
    if (id) await SuppliersAPI.update(id, payload);
    else await SuppliersAPI.create(payload);
    toast(id ? 'Supplier updated' : 'Supplier added');
    await loadAll();
  };

  const handleExport = () => exportWorkbook({ products: uiProducts, suppliers: supplierOptions, purchases, sales, stockLog });

  const renderPage = () => {
    if (loading) return <StatePanel loading title="Loading stock data" text="Fetching products, suppliers, purchases, and sales." />;
    if (error) return <StatePanel title="Backend unavailable" text={error} action={<button className="btn btn-primary" onClick={loadAll}>Retry</button>} />;

    switch (activePage) {
      case 'products':
        return <Products data={data} CATS={categories.map((c) => c.name)} st={stockStatus} onAddProduct={handleAddProduct} searchQuery={searchQuery} />;
      case 'stockin':
        return <InventoryPage products={uiProducts} stockLog={stockLog} onStockIn={handleStockIn} onAdjustment={handleAdjustment} />;
      case 'purchases':
        return <PurchasesPage products={uiProducts} suppliers={supplierOptions} purchases={purchases} onCreate={handleCreatePurchase} searchQuery={searchQuery} />;
      case 'sales':
        return <SalesPage products={uiProducts} sales={sales} onCreate={handleCreateSale} searchQuery={searchQuery} />;
      case 'suppliers':
        return <SuppliersPage suppliers={supplierOptions} onSave={handleSaveSupplier} searchQuery={searchQuery} />;
      case 'reports':
        return <ReportsPage products={uiProducts} purchases={purchases} sales={sales} stockLog={stockLog} onExport={handleExport} />;
      case 'dashboard':
      default:
        return <Dashboard data={data} storeName="VVV Traders" onNavigate={setActivePage} />;
    }
  };

  return (
    <Layout
      activePage={activePage}
      onNavigate={setActivePage}
      storeName="VVV Traders"
      onEOD={handleExport}
      onSearch={setSearchQuery}
    >
      {renderPage()}
    </Layout>
  );
}

function StatePanel({ title, text, action, loading }) {
  return (
    <div className="card state-panel">
      {loading && <div className="spinner" />}
      <div className="state-title">{title}</div>
      <div className="state-text">{text}</div>
      {action && <div>{action}</div>}
    </div>
  );
}
