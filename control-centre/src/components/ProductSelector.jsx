import React from "react";
import { useProduct } from "../contexts/ProductContext";

export default function ProductSelector({ onAddProduct }) {
  const { selectedProduct, selectProduct, products } = useProduct();

  if (!products.length) return null;

  return (
    <div className="product-selector">
      <label className="product-selector-label">Product:</label>
      <select
        className="product-selector-select"
        value={selectedProduct?.id || ""}
        onChange={e => {
          const product = products.find(p => p.id === e.target.value);
          if (product) selectProduct(product);
        }}
      >
        {products.map(p => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
      <button className="product-selector-add" onClick={onAddProduct} title="Add new product">
        + Add
      </button>
    </div>
  );
}