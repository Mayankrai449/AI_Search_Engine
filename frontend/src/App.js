import React from 'react';
import Navbar from './components/Navbar';
import ChatWindow from './components/ChatWindow';
import './App.css';

const App = () => {
  return (
    <div className="app-container">
      <Navbar />
      <ChatWindow />
    </div>
  );
};

export default App;