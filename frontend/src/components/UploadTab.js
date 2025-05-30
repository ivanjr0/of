import React, { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import { uploadContent } from '../utils/api';

const UploadTab = ({ onUploadSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    content: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileSelect = (file) => {
    // Validate file type
    const allowedTypes = ['.txt', '.md'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      toast.error('Please select a .txt or .md file');
      return;
    }
    
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      toast.error('File size must be less than 10MB');
      return;
    }
    
    // Read file content
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      setFormData(prev => ({
        ...prev,
        content,
        name: prev.name || file.name.replace(/\.[^/.]+$/, "") // Auto-fill name if empty
      }));
      toast.success('File loaded successfully');
    };
    
    reader.onerror = () => {
      toast.error('Error reading file');
    };
    
    reader.readAsText(file);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.content.trim()) {
      toast.error('Please fill in both name and content');
      return;
    }
    
    setIsLoading(true);
    
    try {
      await uploadContent(formData);
      toast.success('Content uploaded successfully! AI analysis in progress...');
      
      // Reset form
      setFormData({ name: '', content: '' });
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Switch to library tab
      onUploadSuccess();
      
    } catch (error) {
      console.error('Error uploading content:', error);
      toast.error('Error uploading content. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setFormData({ name: '', content: '' });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    toast('Form cleared', { icon: 'ℹ️' });
  };

  return (
    <div className="card">
      <div className="upload-header">
        <h2><i className="fas fa-cloud-upload-alt"></i> Upload New Content</h2>
        <p>Add educational content for AI-powered analysis and insights</p>
      </div>
      
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="contentName">
              <i className="fas fa-tag"></i> Content Name
            </label>
            <input 
              type="text" 
              id="contentName" 
              name="name" 
              value={formData.name}
              onChange={handleInputChange}
              required 
              placeholder="Enter a descriptive name for your content..."
            />
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="contentText">
            <i className="fas fa-edit"></i> Content Text
          </label>
          <textarea 
            id="contentText" 
            name="content" 
            value={formData.content}
            onChange={handleInputChange}
            required 
            placeholder="Paste or type your educational content here..."
          />
        </div>
        
        <div className="upload-options">
          <div className="option-divider">
            <span>OR</span>
          </div>
          
          <div className="form-group">
            <label htmlFor="fileUpload">
              <i className="fas fa-file-upload"></i> Upload File
            </label>
            <input 
              type="file" 
              id="fileUpload" 
              ref={fileInputRef}
              accept=".txt,.md" 
              className="file-input"
              onChange={handleFileInputChange}
            />
            <div 
              className={`file-upload-area ${isDragOver ? 'dragover' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="upload-icon">
                <i className="fas fa-cloud-upload-alt"></i>
              </div>
              <div className="upload-text">
                <p><strong>Click to select a file</strong> or drag and drop</p>
                <small>Supported formats: TXT, MD (Max 10MB)</small>
              </div>
            </div>
          </div>
        </div>
        
        <div className="form-actions">
          <button 
            type="submit" 
            className="btn btn-primary btn-large"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <i className="fas fa-spinner fa-spin"></i> Analyzing...
              </>
            ) : (
              <>
                <i className="fas fa-magic"></i> Analyze Content
              </>
            )}
          </button>
          <button 
            type="button" 
            onClick={handleClear}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            <i className="fas fa-times"></i> Clear
          </button>
        </div>
      </form>
    </div>
  );
};

export default UploadTab; 