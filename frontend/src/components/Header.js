import React from 'react';
import { GraduationCap, LogOut, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <GraduationCap size={40} className="header-icon" />
          <div>
            <h1>Educational Content Analysis System</h1>
            <p>AI-powered learning assistant with smart content analysis</p>
          </div>
        </div>
        {isAuthenticated && user && (
          <div className="header-right">
            <div className="user-info">
              <User size={20} />
              <span>{user.username}</span>
            </div>
            <button className="logout-button" onClick={handleLogout}>
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header; 