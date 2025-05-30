import React, { createContext, useState, useContext, useEffect } from 'react';
import { 
  getAccessToken, 
  getUserInfo, 
  setTokens, 
  setUserInfo, 
  clearAuth,
  isAuthenticated as checkAuth,
  authFetch 
} from '../utils/auth';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      if (checkAuth()) {
        const userInfo = getUserInfo();
        if (userInfo) {
          setUser(userInfo);
          setIsAuthenticated(true);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username, password) => {
    try {
      // Input validation
      if (!username || !username.trim()) {
        return { success: false, error: 'Username is required' };
      }
      
      if (!password) {
        return { success: false, error: 'Password is required' };
      }

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username.trim(), password }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Login failed' }));
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();
      
      // Validate response data
      if (!data.access_token || !data.refresh_token || !data.user_id) {
        throw new Error('Invalid response from server');
      }
      
      // Store tokens and user info
      setTokens(data.access_token, data.refresh_token);
      const userInfo = {
        id: data.user_id,
        username: data.username,
        email: data.email,
      };
      setUserInfo(userInfo);
      
      // Update state
      setUser(userInfo);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const signup = async (username, email, password, firstName = '', lastName = '') => {
    try {
      // Input validation
      if (!username || !username.trim()) {
        return { success: false, error: 'Username is required' };
      }
      
      if (!email || !email.trim()) {
        return { success: false, error: 'Email is required' };
      }
      
      if (!password || password.length < 8) {
        return { success: false, error: 'Password must be at least 8 characters long' };
      }
      
      if (!email.includes('@')) {
        return { success: false, error: 'Please provide a valid email address' };
      }

      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim().toLowerCase(),
          password,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Signup failed' }));
        throw new Error(error.error || 'Signup failed');
      }

      const data = await response.json();
      
      // Validate response data
      if (!data.access_token || !data.refresh_token || !data.user_id) {
        throw new Error('Invalid response from server');
      }
      
      // Store tokens and user info
      setTokens(data.access_token, data.refresh_token);
      const userInfo = {
        id: data.user_id,
        username: data.username,
        email: data.email,
      };
      setUserInfo(userInfo);
      
      // Update state
      setUser(userInfo);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    signup,
    logout,
    authFetch, // Expose authFetch for authenticated API calls
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 