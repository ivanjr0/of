import React from 'react';
import { formatDate, truncateText } from '../utils/helpers';

const ContentItem = ({ content, onClick }) => {
  const getDifficultyClass = (level) => {
    if (!level) return 'meta-tag processing';
    return `difficulty-badge difficulty-${level}`;
  };

  const renderConcepts = () => {
    if (!content.key_concepts || content.key_concepts.length === 0) {
      return null;
    }

    const visibleConcepts = content.key_concepts.slice(0, 3);
    const remainingCount = content.key_concepts.length - 3;

    return (
      <div className="concepts-preview">
        <i className="fas fa-lightbulb"></i>
        {visibleConcepts.map((concept, index) => (
          <span key={index} className="concept-tag">{concept}</span>
        ))}
        {remainingCount > 0 && (
          <span className="concept-more">+{remainingCount} more</span>
        )}
      </div>
    );
  };

  return (
    <div className="content-item" onClick={onClick}>
      <div className="content-header">
        <h3 className="content-title">{content.name}</h3>
        <div className="content-status">
          {content.processed ? (
            <>
              <i className="fas fa-check-circle status-processed"></i>
              <span className="status-text">Analyzed</span>
            </>
          ) : (
            <>
              <i className="fas fa-spinner fa-spin status-processing"></i>
              <span className="status-text">Analyzing...</span>
            </>
          )}
        </div>
      </div>
      
      <div className="content-meta">
        {content.difficulty_level ? (
          <span className={getDifficultyClass(content.difficulty_level)}>
            <i className="fas fa-signal"></i> {content.difficulty_level}
          </span>
        ) : (
          <span className="meta-tag processing">
            <i className="fas fa-cog fa-spin"></i> Analyzing...
          </span>
        )}
        <span className="meta-tag">
          <i className="fas fa-clock"></i> 
          {content.estimated_study_time ? `${content.estimated_study_time} min` : 'TBD'}
        </span>
        <span className="meta-tag">
          <i className="fas fa-calendar"></i> {formatDate(content.created_at)}
        </span>
      </div>
      
      {renderConcepts()}
      
      <div className="content-preview">
        {truncateText(content.content, 150)}
      </div>
      
      <div className="content-actions">
        <span className="view-details">
          <i className="fas fa-eye"></i> View Details
        </span>
      </div>
    </div>
  );
};

export default ContentItem; 