import { authFetch } from './auth';

// Helper function to handle API responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// API functions
export const uploadContent = async (contentData) => {
  try {
    const response = await authFetch(`/api/content`, {
      method: 'POST',
      body: JSON.stringify(contentData),
    });
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to upload content');
  }
};

export const getContents = async () => {
  try {
    const response = await authFetch(`/api/content`);
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to fetch contents');
  }
};

export const getContent = async (id) => {
  try {
    const response = await authFetch(`/api/content/${id}`);
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to fetch content');
  }
};

export const deleteContent = async (id) => {
  try {
    const response = await authFetch(`/api/content/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to delete content');
  }
};

// Session API functions
export const createSession = async (title = null) => {
  try {
    const response = await authFetch(`/api/sessions`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to create session');
  }
};

export const getSessions = async () => {
  try {
    const response = await authFetch(`/api/sessions`);
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to fetch sessions');
  }
};

export const getSessionMessages = async (sessionId) => {
  try {
    const response = await authFetch(`/api/sessions/${sessionId}/messages`);
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to fetch messages');
  }
};

export const sendMessage = async (sessionId, content) => {
  try {
    const response = await authFetch(`/api/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to send message');
  }
};

export const deleteSession = async (sessionId) => {
  try {
    const response = await authFetch(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  } catch (error) {
    throw new Error(error.message || 'Failed to delete session');
  }
};

// Health check function
export const healthCheck = async () => {
  try {
    const response = await fetch(`/api/health`);
    return handleResponse(response);
  } catch (error) {
    throw new Error('Health check failed');
  }
}; 