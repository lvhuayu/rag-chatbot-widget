import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const isLoggedIn = Boolean(localStorage.getItem('token'));

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-md px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <Link to="/" className="text-xl font-bold text-blue-600">RAG Document Portal</Link>
        <Link to="/upload" className="text-gray-700 hover:text-blue-600 transition">Upload</Link>
        <Link to="/documents" className="text-gray-700 hover:text-blue-600 transition">Documents</Link>
      </div>
      <div className="flex items-center space-x-4">
        {isLoggedIn ? (
          <button
            onClick={handleLogout}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
          >
            Logout
          </button>
        ) : (
          <>
            <Link to="/login" className="text-gray-700 hover:text-blue-600 transition">Login</Link>
            <Link to="/register" className="text-gray-700 hover:text-blue-600 transition">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar; 