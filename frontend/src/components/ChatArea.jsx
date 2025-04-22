import React, { useState, useRef } from 'react';
import './ChatArea.css';
import ResearchPanel from './ResearchPanel';
import ChatPanel from './ChatPanel';

const ChatArea = ({ activeChatId, isSidebarCollapsed }) => {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [deepSearch, setDeepSearch] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setMessages(prev => [{ sender: 'user', text: query }, ...prev]);
    setQuery('');
    setIsTyping(true);

    try {
      const response = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, deepSearch })
      });
      const data = await response.json();
      setMessages(prev => [{ sender: 'ai', text: data.response || 'NeoSearch response' }, ...prev]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [{ sender: 'ai', text: 'Search temporarily unavailable' }, ...prev]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleQuerySubmit(e);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const newFiles = files.map(file => ({
      name: file.name,
      type: file.type,
      size: file.size,
      id: Math.random().toString(36).substr(2, 9)
    }));
    setUploadedFiles(prev => [...newFiles, ...prev]);
    e.target.value = null;
  };

  return (
    <div className={`chat-area ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="panels-container">
        <ResearchPanel />
        <ChatPanel 
          messages={messages}
          isTyping={isTyping}
          uploadedFiles={uploadedFiles}
        />
      </div>
      
      <div className="query-container">
        <div className="query-box">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search through the data lake"
          />
          <button
            className="send-btn"
            type="submit"
            disabled={!query.trim()}
            onClick={handleQuerySubmit}
          >
            →
          </button>
        </div>
        
        <div className="extra-controls">
          <button className="upload-btn" type="button" onClick={handleUploadClick}>
            Upload
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            multiple
          />
          <button
            className={`deep-search-btn ${deepSearch ? 'active' : ''}`}
            type="button"
            onClick={() => setDeepSearch(prev => !prev)}
          >
            DeepSearch
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;