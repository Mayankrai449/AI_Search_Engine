import React, { useEffect, useRef } from 'react';
import './ChatPanel.css';

const ChatPanel = ({ messages, isTyping, uploadedFiles }) => {
  const chatLogRef = useRef(null);

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages, uploadedFiles]);

  return (
    <div className="chat-panel">
      <div className="chat-log" ref={chatLogRef}>
        {messages.length === 0 && (
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
    </div>
  );
};

export default ChatPanel;