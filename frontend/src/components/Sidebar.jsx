import React from 'react';
import { createChatWindow, deleteChatWindow } from '../api';
import './Sidebar.css';

const Sidebar = ({ 
  chatWindows, 
  addChatWindow, 
  selectChatWindow, 
  removeChatWindow,
  isCollapsed, 
  toggleSidebar 
}) => {
  const handleNewChatWindow = async () => {
    try {
      const response = await createChatWindow();
      addChatWindow({
        id: response.chatwindow_uuid,
        title: `Chat ${chatWindows.length + 1}`,
        documents: [],
        isActive: true
      });
    } catch (error) {
      console.error('Failed to create new chat window:', error);
    }
  };

  const handleDeleteChatWindow = async (e, id) => {
    e.stopPropagation();
    try {
      await deleteChatWindow(id);
      removeChatWindow(id);
    } catch (error) {
      console.error('Failed to delete chat window:', error);
    }
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="collapse-btn" onClick={toggleSidebar}>
          {isCollapsed ? '>' : '<'}
        </button>
        {!isCollapsed && <h3 className="sidebar-title">Windows</h3>}
      </div>
      
      <div className="sidebar-content">
        <button className="new-chat-btn" onClick={handleNewChatWindow}>
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
              {!isCollapsed && (
                <>
                  <span className="chat-title">{chat.title}</span>
                  <button 
                    className="delete-btn"
                    onClick={(e) => handleDeleteChatWindow(e, chat.id)}
                  >
                    ×
                  </button>
                </>
              )}
              {}
              {isCollapsed && <span className="chat-text-icon">C</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;