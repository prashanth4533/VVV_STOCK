import { api } from "./apiClient";

/**
 * normalizeProduct
 * Converts a backend Product object (snake_case, nested category/supplier)
 * to the flat camelCase shape that the React frontend uses.
 *
 * Backend shape:
 *   { id, sku, brand, item, pack_size, current_stock, reorder_level,
 *     purchase_price, selling_price, notes, is_active,
 *     category: { id, name, … },
 *     supplier: { id, name, … } | null }
 *
 * Frontend shape:
 *   { id, sku, brand, item, pack, qty, cat, categoryId,
 *     reorderLevel, supplierId, purchasePrice, sellingPrice, notes }
 */
export function normalizeProduct(p) {
  return {
    id:            p.id,
    sku:           p.sku,
    brand:         p.brand,
    item:          p.item,
    pack:          p.pack_size,
    cat:           p.category?.name  ?? "",
    categoryId:    p.category?.id    ?? null,
    qty:           p.current_stock,
    reorderLevel:  p.reorder_level,
    supplierId:    p.supplier?.id    ?? null,
    purchasePrice: p.purchase_price  ?? 0,
    sellingPrice:  p.selling_price   ?? 0,
    notes:         p.notes           ?? "",
  };
}

/**
 * ProductsAPI
 * All product CRUD operations.
 */
export const ProductsAPI = {
  /**
   * Fetch all active products.
   * Requests up to 200 per page — sufficient for this app's scale.
   * Returns an array of normalised frontend-shape objects.
   */
  async getAll(params = {}) {
    const qs = new URLSearchParams({ per_page: params.per_page ?? 200 });
    const res = await api.get(`/products?${qs}`);
    return (res.data ?? []).map(normalizeProduct);
  },

  /**
   * Create a new product.
   * @param {object} form    — frontend newProd form state
   * @param {object} catMap  — { [categoryName]: categoryId }
   * Returns the normalised created product.
   */
  async create(form, catMap) {
    const body = {
      brand:         form.brand,
      item:          form.item,
      pack_size:     form.pack,
      category_id:   catMap[form.cat],
      supplier_id:   form.supplierId ? parseInt(form.supplierId) : null,
      reorder_level: parseInt(form.reorderLevel)  || 5,
      purchase_price: parseFloat(form.purchasePrice) || 0,
      selling_price:  parseFloat(form.sellingPrice)  || 0,
      notes:          form.notes || null,
      opening_stock:  parseInt(form.qty) || 0,
    };
    const res = await api.post("/products", body);
    return normalizeProduct(res.data);
  },

  /**
   * Update an existing product's master data.
   * Only sends fields that are present in `form`.
   * @param {number} id      — product id
   * @param {object} form    — editForm state (frontend field names)
   * @param {object} catMap  — { [categoryName]: categoryId }
   */
  async update(id, form, catMap) {
    const body = {};
    if (form.brand         !== undefined) body.brand          = form.brand;
    if (form.item          !== undefined) body.item           = form.item;
    if (form.pack          !== undefined) body.pack_size      = form.pack;
    if (form.cat           !== undefined && catMap[form.cat])
                                          body.category_id    = catMap[form.cat];
    if (form.supplierId    !== undefined) body.supplier_id    = form.supplierId
                                            ? parseInt(form.supplierId) : null;
    if (form.reorderLevel  !== undefined) body.reorder_level  = parseInt(form.reorderLevel) || 5;
    if (form.purchasePrice !== undefined) body.purchase_price = parseFloat(form.purchasePrice) || 0;
    if (form.sellingPrice  !== undefined) body.selling_price  = parseFloat(form.sellingPrice)  || 0;
    if (form.notes         !== undefined) body.notes          = form.notes || null;
    const res = await api.put(`/products/${id}`, body);
    return normalizeProduct(res.data);
  },

  /** Soft-delete a product. Returns null (204). */
  async delete(id) {
    await api.delete(`/products/${id}`);
  },

  /**
   * Bulk-import products from parsed Excel rows.
   * @param {Array<object>} rows — each: { brand, item, pack_size, category,
   *   supplier, opening_stock, reorder_level, purchase_price, selling_price }
   * Returns { total, saved, failed, errors: [{row, field, message}] }.
   */
  async bulkImport(rows) {
    const res = await api.post("/suppliers/import-products", { rows });
    return res.data;
  },
};
