import React from "react";

export const Textarea = ({ value, onChange, placeholder, rows = 4, className = "" }) => (
  <textarea
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    rows={rows}
    className={className}
    style={{
      background: "var(--bg)",
      border: "1px solid var(--border)",
      borderRadius: "8px",
      color: "var(--text)",
      padding: "8px 12px",
      fontSize: "13px",
      width: "100%",
      outline: "none",
      fontFamily: "inherit",
      resize: "vertical",
    }}
  />
);

export default Textarea;
