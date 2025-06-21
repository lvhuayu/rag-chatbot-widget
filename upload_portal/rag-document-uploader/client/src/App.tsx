import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import UploadPage from './pages/UploadPage';
import DocumentsPage from './pages/DocumentsPage';
import UsersPage from './pages/UsersPage';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/upload" element={<ProtectedRoute />}>
          <Route path="/upload" element={<UploadPage />} />
        </Route>
        <Route path="/documents" element={<ProtectedRoute />}>
          <Route path="/documents" element={<DocumentsPage />} />
        </Route>
        <Route path="/users" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/upload" />} />
      </Routes>
    </Router>
  );
}

export default App; 