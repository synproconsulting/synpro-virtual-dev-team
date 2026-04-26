import React from "react";

export const ScrollArea = ({ children, className = "", style = {} }) => (
  <div
    className={className}
    style={{ overflowY: "auto", ...style }}
  >
    {children}
  </div>
);

export default ScrollArea;
