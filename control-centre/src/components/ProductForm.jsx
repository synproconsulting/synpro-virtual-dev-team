import React, { useState } from "react";

const EYE_OPEN = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EYE_OFF = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
);

const EMPTY = {
  name: "",
  jira_base_url: "",
  jira_project_key: "",
  jira_email: "",
  jira_api_token: "",
  github_org: "",
  github_repo: "",
  github_token: "",
  anthropic_api_key: "",
  resend_api_key: "",
  resend_from_email: "",
  railway_project_id: "",
  dev_backend_service_id: "",
  dev_frontend_service_id: "",
  test_backend_service_id: "",
  test_frontend_service_id: "",
  prod_backend_service_id: "",
  prod_frontend_service_id: "",
};

const SECRET_KEYS = ["jira_api_token", "github_token", "anthropic_api_key", "resend_api_key"];

// Build the initial form state from a product record. Secret columns are
// intentionally left blank - the credentials endpoint is never called from
// this UI so plaintext secrets never reach the browser.
export function productToFormState(product) {
  if (!product) return { ...EMPTY };
  const state = { ...EMPTY };
  for (const key of Object.keys(EMPTY)) {
    if (SECRET_KEYS.includes(key)) continue;
    if (product[key] != null) state[key] = product[key];
  }
  return state;
}

// Strip empty strings from the payload so unmodified secret fields are not
// overwritten with "" on the backend. Non-secret optional fields also
// participate - a blanked-out optional value is treated as "leave unchanged"
// rather than "clear", which matches the existing API behaviour.
export function formStateToPayload(form) {
  const payload = {};
  for (const [key, value] of Object.entries(form)) {
    if (value === null || value === undefined) continue;
    const trimmed = typeof value === "string" ? value.trim() : value;
    if (trimmed === "") continue;
    payload[key] = trimmed;
  }
  return payload;
}

function Asterisk() {
  return <span className="prod-required" aria-hidden="true">*</span>;
}

function TextField({ label, name, value, onChange, required, placeholder, type = "text", autoComplete }) {
  return (
    <div className="prod-field">
      <label htmlFor={`prod-${name}`}>
        {label}{required && <Asterisk />}
      </label>
      <input
        id={`prod-${name}`}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        required={required}
        placeholder={placeholder}
        autoComplete={autoComplete || "off"}
        spellCheck={false}
      />
    </div>
  );
}

function SecretField({ label, name, value, onChange, required, placeholder }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="prod-field">
      <label htmlFor={`prod-${name}`}>
        {label}{required && <Asterisk />}
      </label>
      <div className="prod-secret-wrap">
        <input
          id={`prod-${name}`}
          name={name}
          type={visible ? "text" : "password"}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          autoComplete="new-password"
          spellCheck={false}
        />
        <button
          type="button"
          className="prod-secret-toggle"
          onClick={() => setVisible(v => !v)}
          aria-label={visible ? "Hide value" : "Show value"}
          tabIndex={-1}
        >
          {visible ? EYE_OFF : EYE_OPEN}
        </button>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <fieldset className="prod-section">
      <legend className="prod-section-header">{title}</legend>
      <div className="prod-section-body">{children}</div>
    </fieldset>
  );
}

function EnvGroup({ title, optional, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen);
  if (!optional) {
    return (
      <div className="prod-env-block prod-env-required">
        <div className="prod-env-header">
          <span className="prod-env-title">{title}</span>
          <span className="prod-env-tag prod-env-tag-required">required</span>
        </div>
        <div className="prod-env-body">{children}</div>
      </div>
    );
  }
  return (
    <div className={`prod-env-block prod-env-collapsible ${open ? "open" : "closed"}`}>
      <button
        type="button"
        className="prod-env-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <span className="prod-env-arrow" aria-hidden="true">{open ? "?" : "?"}</span>
        <span className="prod-env-title">{title}</span>
        <span className="prod-env-tag prod-env-tag-optional">optional</span>
      </button>
      {open && <div className="prod-env-body">{children}</div>}
    </div>
  );
}

export default function ProductForm({ initial, isEdit, saving, error, onSubmit, onCancel }) {
  const [form, setForm] = useState(() => initial || { ...EMPTY });
  const set = (key) => (e) => {
    const v = e.target.value;
    setForm(prev => ({ ...prev, [key]: v }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formStateToPayload(form));
  };

  const secretRequired = !isEdit;
  const secretPlaceholder = isEdit ? "........" : "";

  const testOpen = Boolean(form.test_backend_service_id || form.test_frontend_service_id);
  const prodOpen = Boolean(form.prod_backend_service_id || form.prod_frontend_service_id);

  return (
    <form onSubmit={handleSubmit} className="prod-form" noValidate={false}>
      <Section title="Product Identity">
        <TextField label="Product Name" name="name" value={form.name}
                   onChange={set("name")} required placeholder="e.g. My App" />
      </Section>

      <Section title="Jira">
        <TextField label="Jira Base URL" name="jira_base_url" value={form.jira_base_url}
                   onChange={set("jira_base_url")} required type="url"
                   placeholder="https://yourorg.atlassian.net" />
        <TextField label="Jira Project Key" name="jira_project_key" value={form.jira_project_key}
                   onChange={set("jira_project_key")} required placeholder="SDT1" />
        <TextField label="Jira Email" name="jira_email" value={form.jira_email}
                   onChange={set("jira_email")} required type="email"
                   placeholder="you@yourdomain.com" />
        <SecretField label="Jira API Token" name="jira_api_token" value={form.jira_api_token}
                     onChange={set("jira_api_token")} required={secretRequired}
                     placeholder={secretPlaceholder} />
      </Section>

      <Section title="GitHub">
        <TextField label="GitHub Org" name="github_org" value={form.github_org}
                   onChange={set("github_org")} required placeholder="e.g. myorg" />
        <TextField label="GitHub Repo" name="github_repo" value={form.github_repo}
                   onChange={set("github_repo")} required placeholder="e.g. my-repo" />
        <SecretField label="GitHub Token" name="github_token" value={form.github_token}
                     onChange={set("github_token")} required={secretRequired}
                     placeholder={secretPlaceholder} />
      </Section>

      <Section title="Anthropic">
        <SecretField label="Anthropic API Key" name="anthropic_api_key"
                     value={form.anthropic_api_key} onChange={set("anthropic_api_key")}
                     required={secretRequired} placeholder={secretPlaceholder} />
      </Section>

      <Section title="Resend (Email)">
        <SecretField label="Resend API Key" name="resend_api_key" value={form.resend_api_key}
                     onChange={set("resend_api_key")} required={secretRequired}
                     placeholder={secretPlaceholder} />
        <TextField label="Resend From Email" name="resend_from_email"
                   value={form.resend_from_email} onChange={set("resend_from_email")}
                   required type="email" placeholder="noreply@yourdomain.com" />
      </Section>

      <Section title="Railway">
        <TextField label="Railway Project ID" name="railway_project_id"
                   value={form.railway_project_id} onChange={set("railway_project_id")}
                   required />

        <EnvGroup title="DEV Environment" optional={false}>
          <TextField label="Backend Service ID" name="dev_backend_service_id"
                     value={form.dev_backend_service_id}
                     onChange={set("dev_backend_service_id")} required />
          <TextField label="Frontend Service ID" name="dev_frontend_service_id"
                     value={form.dev_frontend_service_id}
                     onChange={set("dev_frontend_service_id")} required />
        </EnvGroup>

        <EnvGroup title="TEST Environment" optional defaultOpen={testOpen}>
          <TextField label="Backend Service ID" name="test_backend_service_id"
                     value={form.test_backend_service_id}
                     onChange={set("test_backend_service_id")} />
          <TextField label="Frontend Service ID" name="test_frontend_service_id"
                     value={form.test_frontend_service_id}
                     onChange={set("test_frontend_service_id")} />
        </EnvGroup>

        <EnvGroup title="PROD Environment" optional defaultOpen={prodOpen}>
          <TextField label="Backend Service ID" name="prod_backend_service_id"
                     value={form.prod_backend_service_id}
                     onChange={set("prod_backend_service_id")} />
          <TextField label="Frontend Service ID" name="prod_frontend_service_id"
                     value={form.prod_frontend_service_id}
                     onChange={set("prod_frontend_service_id")} />
        </EnvGroup>
      </Section>

      {error && <p className="prod-form-error" role="alert">{error}</p>}

      <div className="prod-form-actions">
        <button type="button" className="prod-btn-secondary"
                onClick={onCancel} disabled={saving}>
          Cancel
        </button>
        <button type="submit" className="prod-btn-primary" disabled={saving}>
          {saving ? "Saving." : (isEdit ? "Save Changes" : "Add Product")}
        </button>
      </div>
    </form>
  );
}
