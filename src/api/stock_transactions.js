import { api } from "./apiClient";

export const StockTransactionsAPI = {
  async getAll(params = {}) {
    const qs = new URLSearchParams({ per_page: params.per_page ?? 100 });
    if (params.product_id) qs.set("product_id", params.product_id);
    if (params.transaction_type) qs.set("transaction_type", params.transaction_type);
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    const res = await api.get(`/stock-transactions?${qs}`);
    return { data: res.data ?? [], meta: res.meta ?? {} };
  },

  async stockIn(body) {
    const res = await api.post("/stock-transactions/stock-in", body);
    return res.data;
  },

  async stockInBatch(body) {
    const res = await api.post("/stock-transactions/stock-in/batch", body);
    return res.data;
  },

  async adjustment(body) {
    const res = await api.post("/stock-transactions/adjustment", body);
    return res.data;
  },
};
