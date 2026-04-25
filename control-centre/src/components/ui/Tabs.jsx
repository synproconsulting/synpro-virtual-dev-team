import React from 'react';

export const Tabs = ({ children, value, onValueChange }) => (
  <div className="w-full" data-value={value}>
    {React.Children.map(children, child =>
      React.cloneElement(child, { activeTab: value, onTabChange: onValueChange })
    )}
  </div>
);

export const TabsList = ({ children, className = '', activeTab, onTabChange }) => (
  <div className={`flex border-b ${className}`}>
    {React.Children.map(children, child =>
      React.cloneElement(child, { activeTab, onTabChange })
    )}
  </div>
);

export const TabsTrigger = ({ children, value, activeTab, onTabChange, className = '' }) => (
  <button
    onClick={() => onTabChange(value)}
    className={`px-4 py-2 font-medium transition-colors ${
      activeTab === value
        ? 'border-b-2 border-blue-600 text-blue-600'
        : 'text-gray-600 hover:text-gray-900'
    } ${className}`}
  >
    {children}
  </button>
);

export const TabsContent = ({ children, value, activeTab, className = '' }) => (
  activeTab === value ? <div className={`mt-4 ${className}`}>{children}</div> : null
);
