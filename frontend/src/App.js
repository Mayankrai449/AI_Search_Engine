import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { fetchChatWindows, selectChatWindow } from './api';
import './App.css';

const App = () => {
  const [chatWindows, setChatWindows] = useState([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeChatWindowId, setActiveChatWindowId] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAllChatWindows = async () => {
      try {
        setIsLoading(true);
        const data = await fetchChatWindows();

        const windowsArray = Object.entries(data).map(([uuid, details]) => ({
          id: uuid,
          title: details.title,
          documents: details.documents || [],
        }));
        
        setChatWindows(windowsArray);

        if (windowsArray.length > 0) {
          const lastWindow = windowsArray[windowsArray.length - 1];
          setActiveChatWindowId(lastWindow.id);
          setDocuments(lastWindow.documents || []);
        }
      } catch (error) {
        console.error('Failed to fetch chat windows:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllChatWindows();
  }, []);

  const handleSelectChatWindow = async (id) => {
    try {
      setIsLoading(true);
      const response = await selectChatWindow(id);

      setActiveChatWindowId(response.chatwindow_uuid);
      setDocuments(response.documents || []);
      
      setChatWindows(prev => 
        prev.map(chat => ({
          ...chat,
          isActive: chat.id === id
        }))
      );
    } catch (error) {
      console.error('Failed to select chat window:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const addChatWindow = (newChatWindowData) => {
    setChatWindows(prev => [
      ...prev.map(chat => ({ ...chat, isActive: false })),
      { ...newChatWindowData, isActive: true }
    ]);
    setActiveChatWindowId(newChatWindowData.id);
    setDocuments([]);
  };

  const removeChatWindow = (id) => {
    setChatWindows(prev => prev.filter(chat => chat.id !== id));

    if (id === activeChatWindowId && chatWindows.length > 1) {
      const remainingWindows = chatWindows.filter(chat => chat.id !== id);
      const nextWindow = remainingWindows[0];
      handleSelectChatWindow(nextWindow.id);
    } else if (chatWindows.length <= 1) {

      setActiveChatWindowId(null);
      setDocuments([]);
    }
  };

  const updateDocuments = (newDocuments) => {
    setDocuments(newDocuments);
    setChatWindows(prev =>
      prev.map(chat => 
        chat.id === activeChatWindowId 
          ? { ...chat, documents: newDocuments }
          : chat
      )
    );
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(prev => !prev);
  };

  const activeChatWindow = chatWindows.find(chat => chat.id === activeChatWindowId);

  return (
    <div className="app-container">
      <Navbar 
        title="NeoSearch ᯓ★" 
        documents={documents}
        activeWindowId={activeChatWindowId}
        onDeleteDocument={(docId) => {
        }}
      />
      <div className="main-content">
        <Sidebar 
          chatWindows={chatWindows}
          addChatWindow={addChatWindow}
          selectChatWindow={handleSelectChatWindow}
          removeChatWindow={removeChatWindow}
          isCollapsed={isSidebarCollapsed}
          toggleSidebar={toggleSidebar}
        />
        <ChatArea 
          activeChatId={activeChatWindowId}
          documents={documents}
          updateDocuments={updateDocuments}
          isSidebarCollapsed={isSidebarCollapsed}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default App;