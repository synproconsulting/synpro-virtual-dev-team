import React from "react";

export const Button = ({ children, onClick, disabled, variant = "default", size = "default", className = "" }) => {
  const base = {
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.4 : 1,
    border: "none",
    borderRadius: "8px",
    fontFamily: "inherit",
    fontWeight: 500,
    transition: "opacity 0.15s",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
  };
  const variants = {
    default:   { background: "var(--accent)", color: "white", padding: "8px 16px", fontSize: "13px" },
    outline:   { background: "transparent", color: "var(--text)", border: "1px solid var(--border)", padding: "8px 16px", fontSize: "13px" },
    ghost:     { background: "transparent", color: "var(--muted)", padding: "8px 16px", fontSize: "13px" },
    destructive: { background: "var(--danger)", color: "white", padding: "8px 16px", fontSize: "13px" },
  };
  const sizes = {
    default: {},
    sm: { padding: "4px 10px", fontSize: "12px" },
    lg: { padding: "10px 20px", fontSize: "15px" },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{ ...base, ...variants[variant], ...sizes[size] }}
    >
      {children}
    </button>
  );
};

export default Button;
