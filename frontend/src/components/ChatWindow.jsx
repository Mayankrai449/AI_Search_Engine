import React, { useState, useEffect, useRef } from 'react';
import './ChatWindow.css';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [deepSearch, setDeepSearch] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const chatLogRef = useRef(null);
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

  const handleKeyPress = (e) => {
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

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages, uploadedFiles]);

  return (
    <div className="chat-container">
      <div className="chat-window">
        <div className="chat-log" ref={chatLogRef}>
          {messages.length === 0 && uploadedFiles.length === 0 && (
            <div className="default-text">
              Unleash NeoSearch: Upload your data galaxy and explore insights from the vast universe of information at your fingertips.
            </div>
          )}
          {isTyping && <div className="typing-indicator">Searching...</div>}
          {messages.slice().reverse().map((message, index) => (
            <div key={index} className={`chat-message ${message.sender}`}>
              {message.text}
            </div>
          ))}
        </div>
        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            {uploadedFiles.map(file => (
              <div key={file.id} className="file-item">
                <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            ))}
          </div>
        )}
        <div className="query-box">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search through the data lake"
          />
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
          <button
            className="send-btn"
            type="submit"
            disabled={!query.trim()}
            onClick={handleQuerySubmit}
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;