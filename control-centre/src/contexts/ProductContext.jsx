import React, { createContext, useContext, useState, useEffect } from "react";

const ProductContext = createContext({ selectedProduct: null, selectProduct: () => {}, products: [] });

export function ProductProvider({ children, products = [] }) {
  const [selectedProductId, setSelectedProductId] = useState(() => {
    try { return localStorage.getItem("selectedProductId") || null; } catch { return null; }
  });

  // Derive selected product from persisted ID; fall back to first product
  const selectedProduct =
    (selectedProductId && products.find(p => p.id === selectedProductId)) ||
    products[0] ||
    null;

  useEffect(() => {
    try {
      if (selectedProduct?.id) localStorage.setItem("selectedProductId", selectedProduct.id);
    } catch { /* ignore */ }
  }, [selectedProduct?.id]);

  const selectProduct = (product) => setSelectedProductId(product?.id ?? null);

  return (
    <ProductContext.Provider value={{ selectedProduct, selectProduct, products }}>
      {children}
    </ProductContext.Provider>
  );
}

export function useProduct() {
  return useContext(ProductContext);
}

export default ProductContext;