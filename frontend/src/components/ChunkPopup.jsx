import React, { useRef } from 'react';
import './ChunkPopup.css';

const ChunkPopup = ({ chunks, onClose }) => {
  const popupRef = useRef(null);

  const handleClickOutside = (e) => {
    if (popupRef.current && !popupRef.current.contains(e.target)) {
      onClose();
    }
  };

  return (
    <div className="chunk-popup" onClick={handleClickOutside}>
      <div className="chunk-popup-content" ref={popupRef}>
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>Fetched Data</h2>
        <div className="chunks-container">
          {chunks && chunks.length > 0 ? (
            chunks.map((chunk, index) => (
              <div key={index} className="chunk-item">
                <p>{chunk.text}</p>
                <div className="chunk-meta">
                  <span>PDF: {chunk.pdf_name}</span>
                  <span>Page: {chunk.page_number}</span>
                </div>
              </div>
            ))
          ) : (
            <p>No chunks available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChunkPopup;