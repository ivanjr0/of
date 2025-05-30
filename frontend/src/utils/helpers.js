// Date formatting utility
export const formatDate = (dateString) => {
  if (!dateString) return 'Unknown';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

// Text truncation utility
export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  
  if (text.length <= maxLength) {
    return text;
  }
  
  return text.substring(0, maxLength).trim() + '...';
};

// Escape HTML to prevent XSS
export const escapeHtml = (text) => {
  if (!text) return '';
  
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

// Validate file type
export const isValidFileType = (file, allowedTypes = ['.txt', '.md']) => {
  if (!file || !file.name) return false;
  
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
  return allowedTypes.includes(fileExtension);
};

// Validate file size
export const isValidFileSize = (file, maxSizeInMB = 10) => {
  if (!file) return false;
  
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return file.size <= maxSizeInBytes;
};

// Format file size for display
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Debounce function for search inputs
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Generate a random ID
export const generateId = () => {
  return Math.random().toString(36).substr(2, 9);
};

// Check if object is empty
export const isEmpty = (obj) => {
  if (!obj) return true;
  return Object.keys(obj).length === 0;
};

// Deep clone an object
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (typeof obj === 'object') {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
};

// Capitalize first letter
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

// Convert camelCase to Title Case
export const camelToTitle = (str) => {
  if (!str) return '';
  return str
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

// Get difficulty level color
export const getDifficultyColor = (level) => {
  const colors = {
    beginner: '#059669',
    intermediate: '#d97706',
    advanced: '#dc2626',
    expert: '#3730a3'
  };
  return colors[level?.toLowerCase()] || '#64748b';
};

// Format study time
export const formatStudyTime = (minutes) => {
  if (!minutes || minutes === 0) return 'TBD';
  
  if (minutes < 60) {
    return `${minutes} min`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  if (remainingMinutes === 0) {
    return `${hours}h`;
  }
  
  return `${hours}h ${remainingMinutes}m`;
};

const helpers = {
  formatDate,
  truncateText,
  escapeHtml,
  isValidFileType,
  isValidFileSize,
  formatFileSize,
  debounce,
  generateId,
  isEmpty,
  deepClone,
  capitalize,
  camelToTitle,
  getDifficultyColor,
  formatStudyTime
};

export default helpers; 