import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface RAGDocument {
  id: string;
  url: string;
  title: string;
  content: string;
  user_id: string;
  timestamp: string;
}

interface RAGSearchResult {
  document: RAGDocument;
  similarity: number;
}

interface RAGResponse {
  context?: string;
  documents: RAGSearchResult[];
}

interface RAGStats {
  user_id: string;
  document_count: number;
  total_documents: number;
  unique_users?: number;
  embedding_model: string;
  vector_db: string;
  status: string;
  multi_tenant: boolean;
}

const RAGManagementPage: React.FC = () => {
  const [documents, setDocuments] = useState<RAGDocument[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<RAGResponse | null>(null);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'documents' | 'search' | 'stats'>('documents');

  const API_BASE = 'http://localhost:5000/api/upload';

  useEffect(() => {
    fetchDocuments();
    fetchStats();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/rag-documents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDocuments(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/rag-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (err: any) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE}/search`, {
        query: searchQuery,
        top_k: 5,
        threshold: 0.7
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSearchResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const truncateContent = (content: string, maxLength: number = 200) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Document Management</h1>
        <p className="text-gray-600">Manage and search your RAG-enabled documents</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-blue-900 mb-4">Your RAG Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-blue-600">{stats.document_count}</div>
              <div className="text-sm text-gray-600">Your Documents</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-green-600">{stats.total_documents}</div>
              <div className="text-sm text-gray-600">Total System Documents</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-purple-600">{stats.vector_db}</div>
              <div className="text-sm text-gray-600">Storage Type</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📄 Your Documents ({documents.length})
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'search'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔍 Search Documents
            </button>
            <button
              onClick={() => setActiveTab('stats')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'stats'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 System Stats
            </button>
          </nav>
        </div>
      </div>

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-gray-900">Your RAG Documents</h2>
            <button
              onClick={fetchDocuments}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🔄 Refresh
            </button>
          </div>

          {loading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading documents...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {!loading && documents.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">No documents found in your RAG system.</p>
              <p className="text-sm text-gray-400 mt-2">Upload some documents to get started!</p>
            </div>
          )}

          {!loading && documents.length > 0 && (
            <div className="grid gap-4">
              {documents.map((doc) => (
                <div key={doc.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{doc.title}</h3>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {new Date(doc.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{doc.url}</p>
                  <p className="text-gray-700">{truncateContent(doc.content)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Search Your Documents</h2>
          
          <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
            <div className="flex gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search query..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button
                onClick={handleSearch}
                disabled={loading || !searchQuery.trim()}
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-6 py-2 rounded-lg transition-colors"
              >
                {loading ? 'Searching...' : '🔍 Search'}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {searchResults && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Search Results ({searchResults.documents.length} found)
              </h3>
              
              {searchResults.context && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <h4 className="font-semibold text-blue-900 mb-2">AI Response:</h4>
                  <p className="text-blue-800">{searchResults.context}</p>
                </div>
              )}

              <div className="grid gap-4">
                {searchResults.documents.map((result, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-lg font-semibold text-gray-900">{result.document.title}</h4>
                      <span className="text-sm text-green-600 font-medium">
                        {(result.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{result.document.url}</p>
                    <p className="text-gray-700">{truncateContent(result.document.content)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && (
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">System Statistics</h2>
          
          {stats && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Your Documents:</span>
                      <span className="font-semibold">{stats.document_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">User ID:</span>
                      <span className="font-semibold">{stats.user_id}</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Documents:</span>
                      <span className="font-semibold">{stats.total_documents}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Embedding Model:</span>
                      <span className="font-semibold">{stats.embedding_model}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Vector Database:</span>
                      <span className="font-semibold">{stats.vector_db}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Multi-tenant:</span>
                      <span className="font-semibold">{stats.multi_tenant ? '✅ Enabled' : '❌ Disabled'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RAGManagementPage; 