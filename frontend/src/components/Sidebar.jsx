import React from 'react';
import './Sidebar.css';

const Sidebar = ({ chatWindows, addChatWindow, selectChatWindow, isCollapsed, toggleSidebar }) => {
  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="collapse-btn" onClick={toggleSidebar}>
          {isCollapsed ? '>' : '<'}
        </button>
        {!isCollapsed && <h3 className="sidebar-title">Windows</h3>}
      </div>
      
      <div className="sidebar-content">
        <button className="new-chat-btn" onClick={addChatWindow}>
          <span className="plus-icon">+</span>
          {!isCollapsed && <span className="new-chat-text">New Window</span>}
        </button>
        
        <div className="chat-list">
          {chatWindows.map(chat => (
            <div 
              key={chat.id}
              className={`chat-item ${chat.isActive ? 'active' : ''}`} 
              onClick={() => selectChatWindow(chat.id)}
            >
              {!isCollapsed && `Chat ${chat.id.split('-')[1]}`}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;