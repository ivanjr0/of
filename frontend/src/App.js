import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/Header';
import TabNavigation from './components/TabNavigation';
import UploadTab from './components/UploadTab';
import LibraryTab from './components/LibraryTab';
import ChatTab from './components/ChatTab';
import AuthPage from './components/AuthPage';
import './App.css';
import './styles/DebugToolbar.css';

function AppContent() {
  const { isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('upload');
  const [refreshLibrary, setRefreshLibrary] = useState(0);
  const [sessions, setSessions] = useState([]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handleUploadSuccess = () => {
    setActiveTab('library');
    setRefreshLibrary(prev => prev + 1);
  };

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Show auth page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  // Show main app if authenticated
  return (
    <div className="container">
      <Header />
      
      <main>
        <TabNavigation 
          activeTab={activeTab} 
          onTabChange={handleTabChange} 
        />
        
        <div className={`tab-content ${activeTab === 'upload' ? 'active' : ''}`}>
          {activeTab === 'upload' && (
            <UploadTab onUploadSuccess={handleUploadSuccess} />
          )}
        </div>
        
        <div className={`tab-content ${activeTab === 'library' ? 'active' : ''}`}>
          {activeTab === 'library' && (
            <LibraryTab 
              refreshTrigger={refreshLibrary}
              onSwitchToUpload={() => setActiveTab('upload')}
            />
          )}
        </div>

        <div className={`tab-content ${activeTab === 'chat' ? 'active' : ''}`}>
          {activeTab === 'chat' && (
            <ChatTab 
              sessions={sessions}
              setSessions={setSessions}
            />
          )}
        </div>
      </main>
      
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            borderRadius: '12px',
            fontWeight: '600',
          },
          success: {
            style: {
              background: '#059669',
              color: 'white',
            },
          },
          error: {
            style: {
              background: '#ef4444',
              color: 'white',
            },
          },
        }}
      />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App; 