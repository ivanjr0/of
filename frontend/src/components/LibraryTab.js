import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getContents, deleteContent } from '../utils/api';
import ContentItem from './ContentItem';
import ContentModal from './ContentModal';
import EmptyState from './EmptyState';
import LoadingSpinner from './LoadingSpinner';

const LibraryTab = ({ refreshTrigger, onSwitchToUpload }) => {
  const [contents, setContents] = useState([]);
  const [filteredContents, setFilteredContents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedContent, setSelectedContent] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    difficulty: '',
    status: ''
  });

  const loadContents = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await getContents();
      // Ensure data is always an array
      const contentsArray = Array.isArray(data) ? data : (data?.contents || data?.results || []);
      setContents(contentsArray);
      setFilteredContents(contentsArray);
    } catch (error) {
      console.error('Error loading contents:', error);
      setError('Failed to load contents. Please check if the server is running.');
      // Set empty arrays on error to prevent map errors
      setContents([]);
      setFilteredContents([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadContents();
  }, [refreshTrigger]);

  useEffect(() => {
    filterContents();
  }, [contents, filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const filterContents = () => {
    let filtered = [...contents];
    
    // Filter by search term
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(content => 
        content.name.toLowerCase().includes(searchTerm) ||
        content.content.toLowerCase().includes(searchTerm) ||
        (content.key_concepts && content.key_concepts.some(concept => 
          concept.toLowerCase().includes(searchTerm)
        ))
      );
    }
    
    // Filter by difficulty
    if (filters.difficulty) {
      filtered = filtered.filter(content => 
        content.difficulty_level === filters.difficulty
      );
    }
    
    // Filter by status
    if (filters.status) {
      filtered = filtered.filter(content => {
        if (filters.status === 'processed') {
          return content.processed;
        } else if (filters.status === 'processing') {
          return !content.processed;
        }
        return true;
      });
    }
    
    setFilteredContents(filtered);
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleContentClick = (content) => {
    setSelectedContent(content);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedContent(null);
  };

  const handleDeleteContent = async (contentId) => {
    if (!window.confirm('Are you sure you want to delete this content? This action cannot be undone.')) {
      return;
    }
    
    try {
      await deleteContent(contentId);
      toast.success('Content deleted successfully');
      handleCloseModal();
      loadContents();
    } catch (error) {
      console.error('Error deleting content:', error);
      toast.error('Error deleting content. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="card">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <EmptyState 
          type="error"
          title="Error Loading Content"
          message={error}
          actionText="Retry"
          onAction={() => window.location.reload()}
        />
      </div>
    );
  }

  if (contents.length === 0) {
    return (
      <div className="card">
        <EmptyState 
          type="empty"
          title="No content yet"
          message="Upload your first piece of educational content to get started with AI-powered analysis!"
          actionText="Upload Content"
          onAction={onSwitchToUpload}
        />
      </div>
    );
  }

  return (
    <div className="card">
      <div className="library-header">
        <div className="header-content">
          <h2><i className="fas fa-book-open"></i> Content Library</h2>
          <p>Browse and manage your analyzed content</p>
        </div>
        <div className="header-actions">
          <button onClick={loadContents} className="btn btn-secondary">
            <i className="fas fa-sync-alt"></i> Refresh
          </button>
        </div>
      </div>
      
      <div className="library-controls">
        <div className="search-filter">
          <div className="search-group">
            <i className="fas fa-search search-icon"></i>
            <input 
              type="text" 
              placeholder="Search content..." 
              className="search-input"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>
          <select 
            className="filter-select"
            value={filters.difficulty}
            onChange={(e) => handleFilterChange('difficulty', e.target.value)}
          >
            <option value="">All Difficulties</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
            <option value="expert">Expert</option>
          </select>
          <select 
            className="filter-select"
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="">All Status</option>
            <option value="processed">Processed</option>
            <option value="processing">Processing</option>
          </select>
        </div>
      </div>
      
      <div className="content-list">
        {filteredContents.map(content => (
          <ContentItem 
            key={content.id} 
            content={content} 
            onClick={() => handleContentClick(content)}
          />
        ))}
      </div>

      {isModalOpen && selectedContent && (
        <ContentModal 
          content={selectedContent}
          onClose={handleCloseModal}
          onDelete={handleDeleteContent}
        />
      )}
    </div>
  );
};

export default LibraryTab; 