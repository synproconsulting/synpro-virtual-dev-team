import React, { useState } from "react";
import { createProduct } from "../api/productsApi";

const EMPTY = {
  name: "", jira_project_key: "", jira_base_url: "", github_org: "", github_repo: "",
  railway_project_id: "", railway_backend_service_name: "", railway_frontend_service_name: "",
  railway_dev_service_id: "", railway_test_service_id: "", railway_prod_service_id: "",
};

export default function AddProductModal({ onClose, onAdded }) {
  const [form, setForm] = useState(EMPTY);
  const [token, setToken] = useState(() => {
    try { return localStorage.getItem("authToken") || ""; } catch { return ""; }
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const product = await createProduct(
        {
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
        },
        token,
      );
      try { if (token) localStorage.setItem("authToken", token); } catch {}
      onAdded(product);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const field = (label, key, required = false, placeholder = "") => (
    <div className="modal-field" key={key}>
      <label>{label}{required && " *"}</label>
      <input value={form[key]} onChange={set(key)} placeholder={placeholder} required={required} />
    </div>
  );

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-header">
          <h2>Add Product</h2>
          <button className="modal-close" onClick={onClose}>&#x2715;</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          {field("Product Name", "name", true, "e.g. My App")}
          {field("Jira Project Key", "jira_project_key", true, "e.g. APP1")}
          {field("Jira Base URL", "jira_base_url", true, "https://yourorg.atlassian.net")}
          {field("GitHub Org", "github_org", true, "e.g. myorg")}
          {field("GitHub Repo", "github_repo", true, "e.g. my-repo")}
          {field("Railway Project ID", "railway_project_id", false)}
          {field("Railway Backend Service", "railway_backend_service_name", false)}
          {field("Railway Frontend Service", "railway_frontend_service_name", false)}
          {field("Railway DEV Service ID", "railway_dev_service_id", false)}
          {field("Railway TEST Service ID", "railway_test_service_id", false)}
          {field("Railway PROD Service ID", "railway_prod_service_id", false)}
          <div className="modal-field">
            <label>Auth Token *</label>
            <input
              type="password"
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="Paste a valid JWT token"
              required
            />
          </div>
          {error && <p className="modal-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" onClick={onClose} disabled={saving}>Cancel</button>
            <button type="submit" disabled={saving}>{saving ? "Saving…" : "Add Product"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
