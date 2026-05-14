import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";

const API_URL = import.meta.env.VITE_API_URL || "";

const ProductContext = createContext({
  selectedProduct: null,
  productCredentials: null,
  setSelectedProduct: () => {},
  loadingCredentials: false,
  credentialsError: null,
  products: [],
});

export function ProductProvider({ children, products = [] }) {
  const [selectedProduct, setSelectedProductState] = useState(null);
  const [productCredentials, setProductCredentials] = useState(null);
  const [loadingCredentials, setLoadingCredentials] = useState(false);
  const [credentialsError, setCredentialsError] = useState(null);
  const restoredRef = useRef(false);

  const fetchCredentials = useCallback(async (product) => {
    if (!product?.id) {
      setProductCredentials(null);
      setCredentialsError(null);
      setLoadingCredentials(false);
      return;
    }
    if (!API_URL) {
      setProductCredentials(null);
      setCredentialsError("VITE_API_URL is not configured");
      setLoadingCredentials(false);
      return;
    }
    setLoadingCredentials(true);
    setCredentialsError(null);
    setProductCredentials(null);
    try {
      const token = (() => {
        try { return localStorage.getItem("token") || ""; } catch { return ""; }
      })();
      const r = await fetch(`${API_URL}/api/products/${product.id}/credentials`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to load credentials: HTTP ${r.status}`);
      }
      const data = await r.json();
      setProductCredentials(data);
    } catch (err) {
      setCredentialsError(err.message || String(err));
      setProductCredentials(null);
    } finally {
      setLoadingCredentials(false);
    }
  }, []);

  const setSelectedProduct = useCallback((product) => {
    setSelectedProductState(product || null);
    try {
      if (product?.id) localStorage.setItem("selectedProductId", product.id);
      else localStorage.removeItem("selectedProductId");
    } catch { /* localStorage unavailable */ }
    fetchCredentials(product);
  }, [fetchCredentials]);

  // Restore selection from localStorage once products are loaded.
  // Runs at most once per session, then again only if the saved product
  // disappears from the list.
  useEffect(() => {
    if (!products.length) return;
    if (restoredRef.current && selectedProduct &&
        products.find(p => p.id === selectedProduct.id)) return;
    let savedId = null;
    try { savedId = localStorage.getItem("selectedProductId"); } catch { /* ignore */ }
    const restored = (savedId && products.find(p => p.id === savedId)) || null;
    restoredRef.current = true;
    if (restored) {
      setSelectedProductState(restored);
      fetchCredentials(restored);
    } else if (selectedProduct && !products.find(p => p.id === selectedProduct.id)) {
      setSelectedProductState(null);
      setProductCredentials(null);
    }
  }, [products, selectedProduct, fetchCredentials]);

  return (
    <ProductContext.Provider value={{
      selectedProduct,
      productCredentials,
      setSelectedProduct,
      loadingCredentials,
      credentialsError,
      products,
    }}>
      {children}
    </ProductContext.Provider>
  );
}

export function useProduct() {
  return useContext(ProductContext);
}

export default ProductContext;
