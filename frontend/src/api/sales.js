import { api } from "./apiClient";

/**
 * SalesAPI
 * Sales lifecycle integration for backend routes.
 */
export const SalesAPI = {
  async getAll(params = {}) {
    const qs = new URLSearchParams({ per_page: params.per_page ?? 50 });
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date)   qs.set("to_date",   params.to_date);
    if (params.search)    qs.set("search",    params.search);
    const res = await api.get(`/sales?${qs}`);
    return { data: res.data ?? [], meta: res.meta ?? {} };
  },

  async getById(id) {
    const res = await api.get(`/sales/${id}`);
    return res.data;
  },

  async nextNumber() {
    const res = await api.get("/sales/next-number");
    return res.data.sale_no;
  },

  async create(body) {
    const res = await api.post("/sales", body);
    return res.data;
  },

  async cancel(id) {
    const res = await api.patch(`/sales/${id}/cancel`);
    return res.data;
  },

  async bulkImport(rows) {
    const res = await api.post("/sales/bulk-import", { rows });
    return res.data;
  },
};
