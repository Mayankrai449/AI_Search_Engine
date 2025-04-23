import React from 'react';
import { deleteDocument } from '../api';
import './Navbar.css';

const Navbar = ({ title, documents, activeWindowId, onDeleteDocument }) => {
  const handleDeleteDocument = async (docId) => {
    try {
      await deleteDocument(activeWindowId, docId);
      if (onDeleteDocument) {
        onDeleteDocument(docId);
      }
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const handleTitleClick = () => {
    window.location.reload();
  };

  return (
    <div className="navbar">
      <div className="navbar-title" onClick={handleTitleClick}>
        {title}
      </div>
      {documents.length > 0 && (
        <div className="documents-container">
          <div className="documents-scroll">
            {documents.map((doc) => (
              <div key={doc.uuid} className="document-item">
                <span className="document-name">{doc.name}</span>
                <button 
                  className="document-delete-btn"
                  onClick={() => handleDeleteDocument(doc.uuid)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Navbar;