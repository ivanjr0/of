import React, { useState, useEffect } from 'react';
import { formatDate } from '../utils/helpers';

const ContentModal = ({ content, onClose, onDelete }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    
    // Handle escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    
    return () => {
      document.body.style.overflow = 'auto';
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(content.id);
    } finally {
      setIsDeleting(false);
    }
  };

  const getDifficultyClass = (level) => {
    if (!level) return 'meta-tag processing';
    return `difficulty-badge difficulty-${level}`;
  };

  const renderConcepts = () => {
    if (!content.key_concepts || content.key_concepts.length === 0) {
      return (
        <span className="meta-tag processing">
          <i className="fas fa-cog fa-spin"></i> Analyzing concepts...
        </span>
      );
    }

    return content.key_concepts.map((concept, index) => (
      <span key={index} className="concept-tag">{concept}</span>
    ));
  };

  return (
    <div className="modal show" onClick={handleBackdropClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h3>{content.name}</h3>
          <span className="close" onClick={onClose}>&times;</span>
        </div>
        
        <div className="modal-body">
          <div className="content-meta">
            <div className="meta-grid">
              <div className="meta-item">
                <strong><i className="fas fa-signal"></i> Difficulty Level</strong>
                {content.difficulty_level ? (
                  <span className={getDifficultyClass(content.difficulty_level)}>
                    {content.difficulty_level}
                  </span>
                ) : (
                  <span className="meta-tag processing">
                    <i className="fas fa-cog fa-spin"></i> Analyzing...
                  </span>
                )}
              </div>
              
              <div className="meta-item">
                <strong><i className="fas fa-clock"></i> Study Time</strong>
                <span>
                  {content.estimated_study_time ? 
                    `${content.estimated_study_time} minutes` : 
                    'Calculating...'
                  }
                </span>
              </div>
              
              <div className="meta-item">
                <strong><i className="fas fa-calendar"></i> Created</strong>
                <span>{formatDate(content.created_at)}</span>
              </div>
              
              <div className="meta-item">
                <strong><i className="fas fa-cogs"></i> Status</strong>
                <span>
                  {content.processed ? (
                    <>
                      <i className="fas fa-check-circle" style={{color: '#059669'}}></i> Analyzed
                    </>
                  ) : (
                    <>
                      <i className="fas fa-spinner fa-spin" style={{color: '#d97706'}}></i> Analyzing...
                    </>
                  )}
                </span>
              </div>
              
              <div className="meta-item concepts-section">
                <strong><i className="fas fa-lightbulb"></i> Key Concepts</strong>
                <div className="concepts-list">
                  {renderConcepts()}
                </div>
              </div>
            </div>
          </div>
          
          <div className="content-text">
            <h4><i className="fas fa-file-text"></i> Content</h4>
            <div id="modalContent">{content.content}</div>
          </div>
        </div>
        
        <div className="modal-footer">
          <button 
            onClick={handleDelete}
            className="btn btn-danger"
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <i className="fas fa-spinner fa-spin"></i> Deleting...
              </>
            ) : (
              <>
                <i className="fas fa-trash"></i> Delete
              </>
            )}
          </button>
          <button onClick={onClose} className="btn btn-secondary">
            <i className="fas fa-times"></i> Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContentModal; 