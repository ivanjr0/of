// Authentication utility functions

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_info';

// Token management
export const getAccessToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (error) {
    console.error('Error accessing localStorage:', error);
    return null;
  }
};

export const getRefreshToken = () => {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch (error) {
    console.error('Error accessing localStorage:', error);
    return null;
  }
};

export const getUserInfo = () => {
  try {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error('Error parsing user info:', error);
    return null;
  }
};

export const setTokens = (accessToken, refreshToken) => {
  try {
    if (!accessToken || !refreshToken) {
      throw new Error('Invalid tokens provided');
    }
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  } catch (error) {
    console.error('Error storing tokens:', error);
  }
};

export const setUserInfo = (user) => {
  try {
    if (!user || typeof user !== 'object') {
      throw new Error('Invalid user info provided');
    }
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (error) {
    console.error('Error storing user info:', error);
  }
};

export const clearAuth = () => {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch (error) {
    console.error('Error clearing auth data:', error);
  }
};

// Check if user is authenticated
export const isAuthenticated = () => {
  return !!getAccessToken();
};

// Get auth header for axios requests
export const getAuthHeader = () => {
  const token = getAccessToken();
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
};

// API request helper with authentication
export const authFetch = async (url, options = {}) => {
  const token = getAccessToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    console.error('Network error:', error);
    throw new Error('Network error. Please check your connection.');
  }
  
  // If unauthorized, try to refresh token
  if (response.status === 401 && getRefreshToken()) {
    try {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry the original request with new token
        headers['Authorization'] = `Bearer ${getAccessToken()}`;
        return fetch(url, {
          ...options,
          headers,
        });
      }
    } catch (refreshError) {
      console.error('Token refresh failed:', refreshError);
      clearAuth();
    }
  }
  
  return response;
};

// Refresh access token
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  
  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.access_token && data.refresh_token) {
        setTokens(data.access_token, data.refresh_token);
        setUserInfo({
          id: data.user_id,
          username: data.username,
          email: data.email,
        });
        return true;
      }
    }
    
    // If refresh fails, clear auth
    clearAuth();
    return false;
  } catch (error) {
    console.error('Token refresh failed:', error);
    clearAuth();
    return false;
  }
}; 