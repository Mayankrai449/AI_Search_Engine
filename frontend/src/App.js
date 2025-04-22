import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import './App.css';

const App = () => {
  const [chatWindows, setChatWindows] = useState([{ id: 'chat-1', isActive: true }]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const addChatWindow = () => {
    const newChatId = `chat-${chatWindows.length + 1}`;
    setChatWindows(prev => 
      prev.map(chat => ({ ...chat, isActive: false }))
        .concat({ id: newChatId, isActive: true })
    );
  };

  const selectChatWindow = (id) => {
    setChatWindows(prev => 
      prev.map(chat => ({ ...chat, isActive: chat.id === id }))
    );
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(prev => !prev);
  };

  const activeChatWindow = chatWindows.find(chat => chat.isActive);

  return (
    <div className="app-container">
      <Navbar />
      <div className="main-content">
        <Sidebar 
          chatWindows={chatWindows}
          addChatWindow={addChatWindow}
          selectChatWindow={selectChatWindow}
          isCollapsed={isSidebarCollapsed}
          toggleSidebar={toggleSidebar}
        />
        <ChatArea 
          activeChatId={activeChatWindow?.id}
          isSidebarCollapsed={isSidebarCollapsed}
        />
      </div>
    </div>
  );
};

export default App;