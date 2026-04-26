import React from "react";

export const Input = ({ value, onChange, placeholder, type = "text", className = "", disabled }) => (
  <input
    type={type}
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    disabled={disabled}
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
    }}
  />
);

export default Input;
