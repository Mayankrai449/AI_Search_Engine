import React, { useState, useRef, useEffect } from 'react';
import { uploadFile, searchDocuments, updateChatWindowTitle } from '../api';
import './ChatArea.css';
import ResearchPanel from './ResearchPanel';
import ChatPanel from './ChatPanel';

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
  const [deepSearch, setDeepSearch] = useState(false);
  const [researchResults, setResearchResults] = useState([]);
  const fileInputRef = useRef(null);

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || !activeChatId || documents.length === 0) return;

    setMessages(prev => [{ sender: 'user', text: query }, ...prev]);
    setQuery('');
    setIsTyping(true);

    try {

      if (messages.length === 0) {
        const firstDocName = documents[0]?.name || "Untitled Chat";
        const titlePromise = updateChatWindowTitle(activeChatId, firstDocName);
        const searchPromise = searchDocuments(query, activeChatId);

        const [_, data] = await Promise.all([titlePromise, searchPromise]);
        
        setResearchResults(data.results || []);
        
        setMessages(prev => [
          { 
            sender: 'ai', 
            text: `I've found ${data.results?.length || 0} relevant results from your documents.` 
          }, 
          ...prev
        ]);
      } else {
        const data = await searchDocuments(query, activeChatId);

        setResearchResults(data.results || []);

        setMessages(prev => [
          { 
            sender: 'ai', 
            text: `I've found ${data.results?.length || 0} relevant results from your documents.` 
          }, 
          ...prev
        ]);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [
        { sender: 'ai', text: 'Search temporarily unavailable' }, 
        ...prev
      ]);
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
    
    setIsTyping(true);
    
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

        setMessages(prev => [
          { 
            sender: 'ai',
            text: `File "${file.name}" has been uploaded and processed into ${response.chunks_added} chunks.` 
          }, 
          ...prev
        ]);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessages(prev => [
        { sender: 'ai', text: 'File upload failed. Please try again.' }, 
        ...prev
      ]);
    } finally {
      setIsTyping(false);
      e.target.value = null;
    }
  };

  useEffect(() => {
    setMessages([]);
    setResearchResults([]);
  }, [activeChatId]);

  return (
    <div className={`chat-area ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="panels-container">
        <ResearchPanel results={researchResults} isLoading={isLoading} />
        <ChatPanel 
          messages={messages}
          isTyping={isTyping}
          isLoading={isLoading}
        />
      </div>
      
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
            disabled={!activeChatId}
          >
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
            disabled={!activeChatId || documents.length === 0}
          >
            DeepSearch
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;