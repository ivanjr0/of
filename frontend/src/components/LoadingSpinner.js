import React from 'react';

function LoadingSpinner({ size = 'normal' }) {
  const sizeClass = size === 'small' ? 'spinner-small' : 'spinner-normal';
  
  return (
    <div className={`loading-spinner ${sizeClass}`}>
      <div className="spinner"></div>
    </div>
  );
}

export default LoadingSpinner; 