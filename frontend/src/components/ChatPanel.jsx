import React, { useEffect, useRef } from 'react';
import './ChatPanel.css';

const ChatPanel = ({ messages, isTyping, isLoading, onShowChunks }) => {
  const chatLogRef = useRef(null);

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

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
            {messages.map((message, index) => (
              <div key={index} className="message-wrapper">
                <div className={`chat-message ${message.sender}`}>
                  <p>{message.text}</p>
                </div>
                {message.sender === 'ai' && message.chunks && message.chunks.length > 0 && (
                  <button className="fetched-data-btn" onClick={() => onShowChunks(message.chunks)}>
                    Fetched Data
                  </button>
                )}
              </div>
            ))}
            {isTyping && <div className="typing-indicator">Searching...</div>}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatPanel;