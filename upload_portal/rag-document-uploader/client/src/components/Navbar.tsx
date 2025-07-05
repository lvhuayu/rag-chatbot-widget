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
    <nav className="bg-gray-900 border-b border-gray-700/50 px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-lg">
      <div className="flex items-center space-x-6">
        <Link to="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
          RAG Document Portal
        </Link>
        <div className="hidden md:flex items-center space-x-6">
          <Link 
            to="/upload" 
            className="text-gray-200 hover:text-blue-300 transition-colors duration-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-800/50"
          >
            Upload
          </Link>
          <Link 
            to="/documents" 
            className="text-gray-200 hover:text-blue-300 transition-colors duration-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-800/50"
          >
            Documents
          </Link>
          <Link 
            to="/rag" 
            className="text-gray-200 hover:text-green-300 transition-colors duration-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-800/50"
          >
            🧠 RAG Management
          </Link>
          <Link 
            to="/users" 
            className="text-gray-200 hover:text-red-300 transition-colors duration-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-800/50"
          >
            👥 Users
          </Link>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        {isLoggedIn ? (
          <button
            onClick={handleLogout}
            className="bg-gray-800/70 text-gray-200 px-4 py-2 rounded-lg hover:bg-gray-700/70 hover:text-white transition-all duration-200 font-medium border border-gray-600/50 hover:border-gray-500/50"
          >
            Logout
          </button>
        ) : (
          <>
            <Link 
              to="/login" 
              className="text-gray-200 hover:text-blue-300 transition-colors duration-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-800/50"
            >
              Login
            </Link>
            <Link 
              to="/register" 
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium shadow-lg border border-blue-500/20"
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar; 