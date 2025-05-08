import React, { useState, useRef, useEffect } from 'react';
import { uploadFile, searchDocuments, updateChatWindowTitle } from '../api';
import './ChatArea.css';
import ChatPanel from './ChatPanel';
import ChunkPopup from './ChunkPopup';

const ChatArea = ({ 
  activeChatId, 
  documents, 
  updateDocuments, 
  isSidebarCollapsed, 
  isLoading 
}) => {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [popupChunks, setPopupChunks] = useState(null);
  const fileInputRef = useRef(null);

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || !activeChatId || documents.length === 0) return;

    const userMessage = { sender: 'user', text: query };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsTyping(true);

    try {
      const data = await searchDocuments(query, activeChatId);
      const aiMessage = {
        sender: 'ai',
        text: data.tailored_response,
        chunks: data.results || []
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = { sender: 'ai', text: 'Search temporarily unavailable' };
      setMessages(prev => [...prev, errorMessage]);
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
    if (!activeChatId) return;
    fileInputRef.current.click();
  };

  const handleFileUpload = async (e) => {
    if (!activeChatId) return;
    
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    setIsUploading(true);
    
    try {
      for (const file of files) {
        const response = await uploadFile(activeChatId, file);
        const newDoc = {
          uuid: response.doc_uuid,
          name: file.name
        };
        if (documents.length === 0) {
          await updateChatWindowTitle(activeChatId, file.name);
        }
        updateDocuments([...documents, newDoc]);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setIsUploading(false);
      e.target.value = null;
    }
  };

  useEffect(() => {
    setMessages([]);
  }, [activeChatId]);

  return (
    <div className={`chat-area ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <ChatPanel 
        messages={messages}
        isTyping={isTyping}
        isLoading={isLoading}
        onShowChunks={setPopupChunks}
      />
      {popupChunks && (
        <ChunkPopup chunks={popupChunks} onClose={() => setPopupChunks(null)} />
      )}
      <div className="query-container">
        <div className="query-box">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={documents.length > 0 ? "Search through your documents" : "Upload documents to start searching"}
            disabled={!activeChatId || documents.length === 0}
          />
          <button
            className="send-btn"
            type="submit"
            disabled={!query.trim() || !activeChatId || documents.length === 0}
            onClick={handleQuerySubmit}
          >
            →
          </button>
        </div>
        <div className="extra-controls">
          <button 
            className="upload-btn" 
            type="button" 
            onClick={handleUploadClick}
            disabled={!activeChatId || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            multiple
          />
        </div>
      </div>
    </div>
  );
};

export default ChatArea;