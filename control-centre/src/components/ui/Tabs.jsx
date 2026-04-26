import React, { createContext, useContext, useState } from 'react';

const TabsContext = createContext();

export const Tabs = ({ children, value, onValueChange, defaultValue, className = '' }) => {
  const [internalValue, setInternalValue] = useState(defaultValue || '');
  const activeValue = value !== undefined ? value : internalValue;
  const handleChange = value !== undefined ? onValueChange : setInternalValue;

  return (
    <TabsContext.Provider value={{ activeValue, onChange: handleChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
};

export const TabsList = ({ children, className = '' }) => {
  return (
    <div
      className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-600 ${className}`}
      role="tablist"
    >
      {children}
    </div>
  );
};

export const TabsTrigger = ({ children, value, className = '' }) => {
  const { activeValue, onChange } = useContext(TabsContext);
  const isActive = activeValue === value;

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => onChange(value)}
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        isActive
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-600 hover:bg-gray-200 hover:text-gray-900'
      } ${className}`}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({ children, value, className = '' }) => {
  const { activeValue } = useContext(TabsContext);
  const isActive = activeValue === value;

  if (!isActive) return null;

  return (
    <div
      role="tabpanel"
      className={`mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${className}`}
    >
      {children}
    </div>
  );
};