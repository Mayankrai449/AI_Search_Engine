import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  }
});

export const fetchChatWindows = async () => {
  try {
    const response = await API.get('/chatwindows');
    return response.data;
  } catch (error) {
    console.error('Error fetching chat windows:', error);
    throw error;
  }
};

export const createChatWindow = async () => {
  try {
    const response = await API.post('/create-chatwindow');
    return response.data;
  } catch (error) {
    console.error('Error creating chat window:', error);
    throw error;
  }
};

export const selectChatWindow = async (chatwindow_uuid) => {
  try {
    const response = await API.post('/select-chatwindow', { chatwindow_uuid });
    return response.data;
  } catch (error) {
    console.error('Error selecting chat window:', error);
    throw error;
  }
};

export const deleteChatWindow = async (chatwindow_uuid) => {
  try {
    await API.post('/delete-chatwindow', { chatwindow_uuid });
    return true;
  } catch (error) {
    console.error('Error deleting chat window:', error);
    throw error;
  }
};

export const deleteDocument = async (chatwindow_uuid, doc_uuid) => {
  try {
    await API.post('/delete-doc', { chatwindow_uuid, doc_uuid });
    return true;
  } catch (error) {
    console.error('Error deleting document:', error);
    throw error;
  }
};

export const uploadFile = async (chatwindow_uuid, file) => {
  try {
    const formData = new FormData();
    formData.append('chatwindow_uuid', chatwindow_uuid);
    formData.append('file', file);
    
    const response = await API.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const searchDocuments = async (query, chatwindow_uuid) => {
  try {
    const response = await API.post('/search', {
      query,
      top_k: 3,
      chatwindow_uuid
    });
    return response.data;
  } catch (error) {
    console.error('Error searching documents:', error);
    throw error;
  }
};

export const updateChatWindowTitle = async (chatwindow_uuid, title) => {
  try {
    await API.post(`/chatwindow/${chatwindow_uuid}/update-title`, {
      title
    });
    return true;
  } catch (error) {
    console.error('Error updating chat window title:', error);
    throw error;
  }
};

export default API;