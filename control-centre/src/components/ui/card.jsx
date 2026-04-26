import React from "react";

export const Card = ({ children, className = "" }) => (
  <div className={`card ${className}`}>{children}</div>
);

export const CardHeader = ({ children, className = "" }) => (
  <div className={`card-header ${className}`} style={{marginBottom:"1rem"}}>{children}</div>
);

export const CardTitle = ({ children, className = "" }) => (
  <h3 className={`card-title ${className}`} style={{fontSize:"15px",fontWeight:600,margin:0}}>{children}</h3>
);

export const CardContent = ({ children, className = "" }) => (
  <div className={`card-content ${className}`}>{children}</div>
);

export const CardDescription = ({ children, className = "" }) => (
  <p className={`card-description ${className}`} style={{fontSize:"13px",color:"var(--muted)",margin:"4px 0 0"}}>{children}</p>
);

export default Card;
