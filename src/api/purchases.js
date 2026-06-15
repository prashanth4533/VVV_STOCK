import { api } from "./apiClient";

/**
 * PurchasesAPI
 * Purchase lifecycle integration for backend routes.
 */
export const PurchasesAPI = {
  async getAll(params = {}) {
    const qs = new URLSearchParams({ per_page: params.per_page ?? 50 });
    if (params.supplier_id) qs.set("supplier_id", params.supplier_id);
    if (params.from_date)   qs.set("from_date",   params.from_date);
    if (params.to_date)     qs.set("to_date",     params.to_date);
    if (params.search)      qs.set("search",      params.search);
    const res = await api.get(`/purchases?${qs}`);
    return { data: res.data ?? [], meta: res.meta ?? {} };
  },

  async getById(id) {
    const res = await api.get(`/purchases/${id}`);
    return res.data;
  },

  async nextNumber() {
    const res = await api.get("/purchases/next-number");
    return res.data.purchase_no;
  },

  async create(body) {
    const res = await api.post("/purchases", body);
    return res.data;
  },

  async cancel(id) {
    const res = await api.patch(`/purchases/${id}/cancel`);
    return res.data;
  },
};
