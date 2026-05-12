const API_URL = import.meta.env.VITE_API_URL || "";

export const fetchProducts = async () => {
  if (!API_URL) return [];
  try {
    const r = await fetch(`${API_URL}/api/products`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.products || [];
  } catch (e) {
    console.error("Products fetch error:", e);
    return [];
  }
};

export const createProduct = async (product, token) => {
  const r = await fetch(`${API_URL}/api/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(product),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
  return r.json();
};

export const updateProduct = async (productId, product, token) => {
  const r = await fetch(`${API_URL}/api/products/${productId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(product),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
  return r.json();
};

export const deleteProduct = async (productId, token) => {
  const r = await fetch(`${API_URL}/api/products/${productId}`, {
    method: "DELETE",
    headers: {
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    },
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
};