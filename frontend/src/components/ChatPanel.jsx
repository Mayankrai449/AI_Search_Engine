import React, { useEffect, useRef } from 'react';
import './ChatPanel.css';

const ChatPanel = ({ messages, isTyping, isLoading, onShowChunks }) => {
  const chatLogRef = useRef(null);

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const formatImageUrl = (imagePath) => {
    const normalizedPath = imagePath.replace(/\\/g, '/');
    const baseUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
    return `${baseUrl}/${normalizedPath}`;
  };

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

                {message.sender === 'ai' && (
                  <div className="message-extras">
                    {message.chunks && message.chunks.length > 0 && (
                      <button className="fetched-data-btn" onClick={() => onShowChunks(message.chunks)}>
                        Fetched Data
                      </button>
                    )}

                    {message.imageSearch && message.images && Array.isArray(message.images) && (
                      <div className="image-results-container">
                        {message.images.length === 0 ? (
                          <div className="no-images-message">No relevant images found</div>
                        ) : (
                          message.images.map((image, imgIndex) => (
                            <div key={imgIndex} className="image-result">
                              <div className="image-frame">
                                <img
                                  src={formatImageUrl(image.image_path)}
                                  alt={`Result from ${image.pdf_name}`}
                                  onError={(e) => {
                                    console.error(`Failed to load image: ${e.target.src}`);
                                  }}
                                />
                              </div>
                              <div className="image-metadata">
                                <span className="pdf-name">{image.pdf_name}</span>
                                <span className="page-number">Page {image.metadata.page_number}</span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
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