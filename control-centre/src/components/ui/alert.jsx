import React from "react";

export const Alert = ({ children, className = "", variant = "default" }) => {
  const colors = {
    default: "rgba(99,102,241,0.1)",
    destructive: "rgba(239,68,68,0.1)",
    warning: "rgba(245,158,11,0.1)",
  };
  return (
    <div className={`alert ${className}`} style={{
      background: colors[variant] || colors.default,
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: "8px",
      padding: "12px 16px",
      marginBottom: "12px",
    }}>
      {children}
    </div>
  );
};

export const AlertDescription = ({ children, className = "" }) => (
  <p className={`alert-description ${className}`} style={{fontSize:"13px",margin:0}}>{children}</p>
);

export default Alert;
