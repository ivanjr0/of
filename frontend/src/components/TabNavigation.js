import React from 'react';
import { Upload, Library, MessageCircle } from 'lucide-react';

function TabNavigation({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'upload', label: 'Upload Content', icon: Upload },
    { id: 'library', label: 'Content Library', icon: Library },
    { id: 'chat', label: 'AI Assistant', icon: MessageCircle }
  ];

  return (
    <nav className="tab-navigation">
      {tabs.map(tab => {
        const IconComponent = tab.icon;
        return (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <IconComponent size={20} />
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}

export default TabNavigation; 