import { api } from "./apiClient";

/**
 * SuppliersAPI
 * Supplier CRUD integration for backend routes.
 */
export const SuppliersAPI = {
  async getAll(params = {}) {
    const qs = new URLSearchParams({ per_page: params.per_page ?? 200 });
    const res = await api.get(`/suppliers?${qs}`);
    return res.data ?? [];
  },

  async getById(id) {
    const res = await api.get(`/suppliers/${id}`);
    return res.data;
  },

  async create(body) {
    const res = await api.post("/suppliers", body);
    return res.data;
  },

  async update(id, body) {
    const res = await api.put(`/suppliers/${id}`, body);
    return res.data;
  },

  async delete(id) {
    await api.delete(`/suppliers/${id}`);
  },
};
