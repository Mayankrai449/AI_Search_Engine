import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { fetchChatWindows, selectChatWindow, deleteChatWindow } from './api';
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
        const windowsArray = data.map(chat => ({
          id: chat.id,
          title: chat.title,
          documents: [],
          isActive: false
        }));
        
        setChatWindows(windowsArray);

        if (windowsArray.length > 0) {
          const lastWindow = windowsArray[windowsArray.length - 1];
          handleSelectChatWindow(lastWindow.id);
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
      { ...newChatWindowData, isActive: true, documents: [] }
    ]);
    setActiveChatWindowId(newChatWindowData.id);
    setDocuments([]);
  };

  const removeChatWindow = async (id) => {
    try {
      await deleteChatWindow(id);
      setChatWindows(prev => {
        const updatedWindows = prev.filter(chat => chat.id !== id);
        if (id === activeChatWindowId) {
          if (updatedWindows.length > 0) {
            const nextWindow = updatedWindows[0];
            handleSelectChatWindow(nextWindow.id);
          } else {
            setActiveChatWindowId(null);
            setDocuments([]);
          }
        }
        return updatedWindows;
      });
    } catch (error) {
      console.error('Failed to delete chat window:', error);
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
          const updatedDocuments = documents.filter(doc => doc.uuid !== docId);
          updateDocuments(updatedDocuments);
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