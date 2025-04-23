//researchpanel.jsx
import React from 'react';
import './ResearchPanel.css';

const ResearchPanel = ({ results, isLoading }) => {
  return (
    <div className="research-panel">
      {isLoading ? (
        <div className="loading-indicator">Loading...</div>
      ) : results && results.length > 0 ? (
        <div className="research-results">
          {results.map((result, index) => (
            <div key={index} className="result-item">
              <div className="result-text">{result.text}</div>
              <div className="result-score">
                <span>Relevance Score: {result.score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="placeholder-text">
          Researched data and insights will appear here. Upload files and use the search to explore your data galaxy.
        </div>
      )}
    </div>
  );
};

export default ResearchPanel;