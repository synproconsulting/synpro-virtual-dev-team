import React, { useState } from "react";
import { useProduct } from "../contexts/ProductContext";
import { createProduct, updateProduct, deleteProduct } from "../api/productsApi";
import ProductForm, { productToFormState } from "./ProductForm";
import "./ProductsTab.css";

function getStoredToken() {
  try { return localStorage.getItem("token") || ""; } catch { return ""; }
}

function redirectToLogin() {
  try { localStorage.removeItem("token"); } catch {}
  window.location.reload();
}

export default function ProductsTab({ onProductsChanged }) {
  const { products } = useProduct();
  const [mode, setMode] = useState("list"); // "list" | "add" | "edit"
  const [editingProduct, setEditingProduct] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const openAdd = () => { setMode("add"); setEditingProduct(null); setError(""); };
  const openEdit = (p) => { setMode("edit"); setEditingProduct(p); setError(""); };
  const closeForm = () => { setMode("list"); setEditingProduct(null); setError(""); };

  const handleSubmit = async (payload) => {
    const token = getStoredToken();
    if (!token) { redirectToLogin(); return; }
    setError("");
    setSaving(true);
    try {
      if (mode === "edit" && editingProduct) {
        await updateProduct(editingProduct.id, payload, token);
      } else {
        await createProduct(payload, token);
      }
      closeForm();
      onProductsChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    const token = getStoredToken();
    if (!token) { redirectToLogin(); return; }
    setSaving(true);
    setError("");
    try {
      await deleteProduct(deleteTarget.id, token);
      setDeleteTarget(null);
      onProductsChanged();
    } catch (err) {
      setError(err.message);
      setDeleteTarget(null);
    } finally {
      setSaving(false);
    }
  };

  const isFormOpen = mode !== "list";
  const initial = mode === "edit" ? productToFormState(editingProduct) : productToFormState(null);

  return (
    <div className="products-tab">
      <div className="products-tab-header">
        <h2 className="products-tab-title">Products</h2>
        {!isFormOpen && (
          <button className="prod-btn-primary" onClick={openAdd}>
            + Add Product
          </button>
        )}
      </div>

      {error && !isFormOpen && <p className="prod-form-error">{error}</p>}

      {!isFormOpen && (
        <div className="products-table-wrap">
          <table className="products-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Jira Project Key</th>
                <th>GitHub Repo</th>
                <th className="products-actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan={4} className="products-empty">No products configured.</td>
                </tr>
              ) : (
                products.map(p => (
                  <tr key={p.id}>
                    <td className="products-name">{p.name}</td>
                    <td className="products-mono">{p.jira_project_key}</td>
                    <td className="products-mono">{p.github_repo}</td>
                    <td className="products-actions">
                      <button className="prod-btn-link" onClick={() => openEdit(p)}>
                        Edit
                      </button>
                      <button
                        className="prod-btn-link prod-btn-link-danger"
                        onClick={() => { setDeleteTarget(p); setError(""); }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {isFormOpen && (
        <div className="products-form-wrapper">
          <h3 className="products-form-heading">
            {mode === "edit" ? `Edit Product - ${editingProduct?.name || ""}` : "Add Product"}
          </h3>
          {mode === "edit" && (
            <p className="products-form-hint">
              Leave secret fields blank to keep the current stored values.
            </p>
          )}
          <ProductForm
            key={editingProduct?.id || "add"}
            initial={initial}
            isEdit={mode === "edit"}
            saving={saving}
            error={error}
            onSubmit={handleSubmit}
            onCancel={closeForm}
          />
        </div>
      )}

      {deleteTarget && (
        <div
          className="modal-overlay"
          onClick={(e) => e.target === e.currentTarget && setDeleteTarget(null)}
        >
          <div className="modal-box">
            <div className="modal-header">
              <h2>Delete Product</h2>
              <button className="modal-close"
                      onClick={() => setDeleteTarget(null)} aria-label="Close">
                &#x2715;
              </button>
            </div>
            <p className="modal-body">
              Delete <strong>{deleteTarget.name}</strong>? This cannot be undone.
            </p>
            {error && <p className="prod-form-error">{error}</p>}
            <div className="modal-actions">
              <button className="prod-btn-secondary"
                      onClick={() => setDeleteTarget(null)} disabled={saving}>
                Cancel
              </button>
              <button className="prod-btn-danger"
                      onClick={handleDelete} disabled={saving}>
                {saving ? "Deleting." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
