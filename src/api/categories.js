import { api } from "./apiClient";

/**
 * CategoriesAPI
 * Read categories (used to build the name → id map for product create/update).
 */
export const CategoriesAPI = {
  /**
   * Fetch all categories ordered by sort_order.
   * Returns raw backend objects: { id, name, sku_prefix, display_color, display_bg, sort_order }
   */
  async getAll() {
    const res = await api.get("/categories");
    return res.data ?? [];
  },
};
