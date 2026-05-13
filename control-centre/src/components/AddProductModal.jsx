import React, { useState } from "react";
import { createProduct } from "../api/productsApi";
import ProductForm, { productToFormState } from "./ProductForm";
import "./ProductsTab.css";

function readAuthToken() {
  try { return localStorage.getItem("token") || ""; } catch { return ""; }
}

function redirectToLogin() {
  try { localStorage.removeItem("token"); } catch {}
  window.location.reload();
}

export default function AddProductModal({ onClose, onAdded }) {
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (payload) => {
    const token = readAuthToken();
    if (!token) { redirectToLogin(); return; }
    setError("");
    setSaving(true);
    try {
      const product = await createProduct(payload, token);
      onAdded(product);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box modal-box-wide">
        <div className="modal-header">
          <h2>Add Product</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            &#x2715;
          </button>
        </div>
        <div className="modal-body">
          <ProductForm
            initial={productToFormState(null)}
            isEdit={false}
            saving={saving}
            error={error}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        </div>
      </div>
    </div>
  );
}
