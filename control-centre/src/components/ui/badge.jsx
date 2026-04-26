import React from 'react';

export const Badge = ({ children, className = '', variant = 'default' }) => {
  const baseClasses = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2';
  
  const variantClasses = {
    default: 'bg-gray-100 text-gray-900',
    secondary: 'bg-gray-100 text-gray-900',
    destructive: 'bg-red-100 text-red-900',
    outline: 'border border-gray-200 text-gray-900'
  };

  return (
    <span className={`${baseClasses} ${variantClasses[variant] || variantClasses.default} ${className}`}>
      {children}
    </span>
  );
};