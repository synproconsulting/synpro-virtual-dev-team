import React, { useState } from "react";
import { useProduct } from "../contexts/ProductContext";
import { createProduct, updateProduct, deleteProduct } from "../api/productsApi";

const EMPTY = {
  name: "", jira_project_key: "", jira_base_url: "", github_org: "", github_repo: "",
  railway_project_id: "", railway_backend_service_name: "", railway_frontend_service_name: "",
  railway_dev_service_id: "", railway_test_service_id: "", railway_prod_service_id: "",
};

function getStoredToken() {
  try { return localStorage.getItem("token") || ""; } catch { return ""; }
}

function redirectToLogin() {
  try { localStorage.removeItem("token"); } catch {}
  window.location.reload();
}

export default function ProductsTab({ onProductsChanged }) {
  const { products } = useProduct();
  const [form, setForm] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const openAdd = () => { setForm({ ...EMPTY }); setEditingId(null); setError(""); };

  const openEdit = (p) => {
    setForm({
      name: p.name || "",
      jira_project_key: p.jira_project_key || "",
      jira_base_url: p.jira_base_url || "",
      github_org: p.github_org || "",
      github_repo: p.github_repo || "",
      railway_project_id: p.railway_project_id || "",
      railway_backend_service_name: p.railway_backend_service_name || "",
      railway_frontend_service_name: p.railway_frontend_service_name || "",
      railway_dev_service_id: p.railway_dev_service_id || "",
      railway_test_service_id: p.railway_test_service_id || "",
      railway_prod_service_id: p.railway_prod_service_id || "",
    });
    setEditingId(p.id);
    setError("");
  };

  const closeForm = () => { setForm(null); setEditingId(null); setError(""); };

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = getStoredToken();
    if (!token) {
      redirectToLogin();
      return;
    }
    setError("");
    setSaving(true);
    const payload = {
      name: form.name,
      jira_project_key: form.jira_project_key,
      jira_base_url: form.jira_base_url,
      github_org: form.github_org,
      github_repo: form.github_repo,
      ...(form.railway_project_id && { railway_project_id: form.railway_project_id }),
      ...(form.railway_backend_service_name && { railway_backend_service_name: form.railway_backend_service_name }),
      ...(form.railway_frontend_service_name && { railway_frontend_service_name: form.railway_frontend_service_name }),
      ...(form.railway_dev_service_id && { railway_dev_service_id: form.railway_dev_service_id }),
      ...(form.railway_test_service_id && { railway_test_service_id: form.railway_test_service_id }),
      ...(form.railway_prod_service_id && { railway_prod_service_id: form.railway_prod_service_id }),
    };
    try {
      if (editingId) {
        await updateProduct(editingId, payload, token);
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
    if (!token) {
      redirectToLogin();
      return;
    }
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

  const field = (label, key, required = false, placeholder = "") => (
    <div className="products-form-field" key={key}>
      <label>{label}{required && " *"}</label>
      <input value={form[key]} onChange={set(key)} placeholder={placeholder} required={required} />
    </div>
  );

  return (
    <div className="products-tab">
      <div className="products-tab-header">
        <h2>Products</h2>
        {!form && <button className="products-add-btn" onClick={openAdd}>+ Add Product</button>}
      </div>

      {error && !form && <p className="products-error">{error}</p>}

      {!form && (
        <table className="products-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Jira Project Key</th>
              <th>GitHub Repo</th>
              <th>Railway Project ID</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {products.length === 0 ? (
              <tr>
                <td colSpan={5} className="products-empty">No products configured.</td>
              </tr>
            ) : (
              products.map(p => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.jira_project_key}</td>
                  <td>{p.github_repo}</td>
                  <td>{p.railway_project_id || "—"}</td>
                  <td className="products-actions">
                    <button onClick={() => openEdit(p)}>Edit</button>
                    <button className="products-delete-btn" onClick={() => { setDeleteTarget(p); setError(""); }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {form && (
        <div className="products-form-wrapper">
          <h3>{editingId ? "Edit Product" : "Add Product"}</h3>
          <form onSubmit={handleSubmit} className="products-form">
            {field("Product Name", "name", true, "e.g. My App")}
            {field("Jira Project Key", "jira_project_key", true, "e.g. APP1")}
            {field("Jira Base URL", "jira_base_url", true, "https://yourorg.atlassian.net")}
            {field("GitHub Org", "github_org", true, "e.g. myorg")}
            {field("GitHub Repo", "github_repo", true, "e.g. my-repo")}
            {field("Railway Project ID", "railway_project_id")}
            {field("Railway Backend Service", "railway_backend_service_name")}
            {field("Railway Frontend Service", "railway_frontend_service_name")}
            {field("Railway DEV Service ID", "railway_dev_service_id")}
            {field("Railway TEST Service ID", "railway_test_service_id")}
            {field("Railway PROD Service ID", "railway_prod_service_id")}
            {error && <p className="products-error">{error}</p>}
            <div className="products-form-actions">
              <button type="button" onClick={closeForm} disabled={saving}>Cancel</button>
              <button type="submit" disabled={saving}>
                {saving ? "Saving…" : editingId ? "Save Changes" : "Add Product"}
              </button>
            </div>
          </form>
        </div>
      )}

      {deleteTarget && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setDeleteTarget(null)}>
          <div className="modal-box">
            <div className="modal-header">
              <h2>Delete Product</h2>
              <button className="modal-close" onClick={() => setDeleteTarget(null)}>&#x2715;</button>
            </div>
            <p>
              Delete <strong>{deleteTarget.name}</strong>? This cannot be undone.
            </p>
            {error && <p className="products-error">{error}</p>}
            <div className="modal-actions">
              <button onClick={() => setDeleteTarget(null)} disabled={saving}>Cancel</button>
              <button className="products-delete-btn" onClick={handleDelete} disabled={saving}>
                {saving ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
