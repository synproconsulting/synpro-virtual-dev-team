import React from "react";

export const Separator = ({ className = "", orientation = "horizontal" }) => (
  <div
    className={className}
    style={{
      background: "var(--border)",
      height: orientation === "horizontal" ? "1px" : "100%",
      width: orientation === "horizontal" ? "100%" : "1px",
      margin: "12px 0",
    }}
  />
);

export default Separator;
