//chatpanel.jsx
import React, { useEffect, useRef } from 'react';
import './ChatPanel.css';

const ChatPanel = ({ messages, isTyping, isLoading }) => {
  const chatLogRef = useRef(null);

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-log" ref={chatLogRef}>
        {isLoading ? (
          <div className="loading-indicator">Loading chat history...</div>
        ) : messages.length === 0 ? (
          <div className="default-text">
            Unleash NeoSearch: Upload your data galaxy and explore insights from the vast universe of information at your fingertips.
          </div>
        ) : (
          <>
            {isTyping && <div className="typing-indicator">Searching...</div>}
            {messages.slice().reverse().map((message, index) => (
              <div key={index} className={`chat-message ${message.sender}`}>
                {message.text}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatPanel;