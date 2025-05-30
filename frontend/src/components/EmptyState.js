import React from 'react';

const EmptyState = ({ type = 'empty', title, message, actionText, onAction }) => {
  const getIcon = () => {
    switch (type) {
      case 'error':
        return 'fas fa-exclamation-triangle';
      case 'empty':
      default:
        return 'fas fa-book-open';
    }
  };

  return (
    <div className={`empty-state ${type === 'error' ? 'error' : ''}`}>
      <div className="empty-icon">
        <i className={getIcon()}></i>
      </div>
      <h3>{title}</h3>
      <p>{message}</p>
      {actionText && onAction && (
        <button 
          className={`btn ${type === 'error' ? 'btn-secondary' : 'btn-primary'}`}
          onClick={onAction}
        >
          {type === 'error' ? (
            <i className="fas fa-refresh"></i>
          ) : (
            <i className="fas fa-plus"></i>
          )}
          {' '}
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState; 