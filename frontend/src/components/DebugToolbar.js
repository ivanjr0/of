import React, { useState } from 'react';
import { Settings, ChevronDown, ChevronUp, X, Search, FileText, Brain } from 'lucide-react';

function DebugToolbar({ debugInfo }) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        className="debug-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="Toggle Debug Toolbar"
      >
        <Settings size={20} />
      </button>

      {/* Debug Panel */}
      {isOpen && (
        <div className="debug-toolbar">
          <div className="debug-header">
            <h3>Debug Information</h3>
            <button onClick={() => setIsOpen(false)} className="debug-close-btn">
              <X size={20} />
            </button>
          </div>

          <div className="debug-content">
            {/* Relevant Passages Section */}
            {debugInfo?.relevant_passages && Array.isArray(debugInfo.relevant_passages) && (
              <div className="debug-section">
                <div 
                  className="debug-section-header"
                  onClick={() => toggleSection('passages')}
                >
                  <div className="debug-section-title">
                    <Search size={16} />
                    <span>Top Passages Found ({debugInfo.relevant_passages.length})</span>
                  </div>
                  {expandedSections.passages ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>

                {expandedSections.passages && (
                  <div className="debug-section-content">
                    {debugInfo.relevant_passages.map((passage, index) => (
                      <div key={index} className="debug-passage">
                        <div className="debug-passage-header">
                          <span className="debug-passage-title">
                            <FileText size={14} />
                            {passage.name}
                          </span>
                          <span className="debug-passage-score">
                            Score: {passage.score.toFixed(3)}
                          </span>
                        </div>
                        <div className="debug-passage-meta">
                          <span>Difficulty: {passage.difficulty_level}</span>
                          <span>•</span>
                          <span>Concepts: {passage.key_concepts.join(', ')}</span>
                        </div>
                        <div className="debug-passage-content">
                          {passage.content}
                        </div>
                        {passage.chunk_info && (
                          <div className="debug-chunk-info">
                            <span>Chunk ID: {passage.chunk_info.chunk_id}</span>
                            <span>•</span>
                            <span>Position: {passage.chunk_info.position}/{passage.chunk_info.total_chunks}</span>
                            <span>•</span>
                            <span>Content ID: {passage.chunk_info.content_id}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Query Analysis Section */}
            {debugInfo?.query_analysis && (
              <div className="debug-section">
                <div 
                  className="debug-section-header"
                  onClick={() => toggleSection('query')}
                >
                  <div className="debug-section-title">
                    <Brain size={16} />
                    <span>Query Analysis</span>
                  </div>
                  {expandedSections.query ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>

                {expandedSections.query && (
                  <div className="debug-section-content">
                    <div className="debug-info-item">
                      <strong>Original Query:</strong> {debugInfo.query_analysis.original_query}
                    </div>
                    {debugInfo.query_analysis.extracted_keywords && debugInfo.query_analysis.extracted_keywords.length > 0 && (
                      <div className="debug-info-item">
                        <strong>Extracted Keywords:</strong> {debugInfo.query_analysis.extracted_keywords.join(', ')}
                      </div>
                    )}
                    <div className="debug-info-item">
                      <strong>Embedding Model:</strong> {debugInfo.query_analysis.embedding_model}
                    </div>
                    <div className="debug-info-item">
                      <strong>Total Search Time:</strong> {debugInfo.query_analysis.search_time_ms}ms
                    </div>
                    {debugInfo.query_analysis.keyword_search_time_ms !== undefined && (
                      <div className="debug-info-item">
                        <strong>Keyword Search Time:</strong> {debugInfo.query_analysis.keyword_search_time_ms}ms
                      </div>
                    )}
                    {debugInfo.query_analysis.vector_search_time_ms !== undefined && (
                      <div className="debug-info-item">
                        <strong>Vector Search Time:</strong> {debugInfo.query_analysis.vector_search_time_ms}ms
                      </div>
                    )}
                    <div className="debug-info-item">
                      <strong>Total Indexed Contents:</strong> {debugInfo.query_analysis.total_indexed_contents}
                    </div>
                    {debugInfo.query_analysis.error && (
                      <div className="debug-info-item" style={{ color: 'red' }}>
                        <strong>Error:</strong> {debugInfo.query_analysis.error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Processing Info Section */}
            {debugInfo?.processing_info && (
              <div className="debug-section">
                <div 
                  className="debug-section-header"
                  onClick={() => toggleSection('processing')}
                >
                  <div className="debug-section-title">
                    <Settings size={16} />
                    <span>Processing Information</span>
                  </div>
                  {expandedSections.processing ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>

                {expandedSections.processing && (
                  <div className="debug-section-content">
                    <div className="debug-info-item">
                      <strong>Response Generation Time:</strong> {debugInfo.processing_info.generation_time_ms}ms
                    </div>
                    <div className="debug-info-item">
                      <strong>Model:</strong> {debugInfo.processing_info.model}
                    </div>
                    <div className="debug-info-item">
                      <strong>Tokens Used:</strong> {debugInfo.processing_info.tokens_used}
                    </div>
                    <div className="debug-info-item">
                      <strong>Context Length:</strong> {debugInfo.processing_info.context_length} chars
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default DebugToolbar; 