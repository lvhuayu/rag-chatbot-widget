import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { FileText, File, FileArchive, Trash2, RefreshCw, Brain } from 'lucide-react';

const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.pdf')) return <File color="red" className="h-8 w-8" />;
    if (fileName.endsWith('.docx')) return <FileArchive color="blue" className="h-8 w-8" />;
    if (fileName.endsWith('.txt')) return <FileText color="gray" className="h-8 w-8" />;
    return <File className="h-8 w-8" />;
};

const DocumentsPage: React.FC = () => {
    const [documents, setDocuments] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const fetchDocuments = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get('/api/upload/documents', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setDocuments(response.data);
        } catch (err) {
            setError('Failed to fetch documents');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    const handleDelete = async (id: string) => {
        if (!window.confirm('Are you sure you want to delete this document?')) return;
        setDeletingId(id);
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`/api/upload/documents/${id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setDocuments(docs => docs.filter(doc => doc.id !== id));
        } catch (err) {
            alert('Failed to delete document.');
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div className="min-h-screen relative overflow-hidden bg-black">
            {/* Dark Tech Company Background (reuse from UploadPage) */}
            <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-900/5 via-purple-900/5 to-indigo-900/5 animate-pulse"></div>
                <div className="absolute top-0 left-0 w-full h-full">
                    <div className="absolute top-20 left-10 w-72 h-72 bg-blue-600/5 rounded-full blur-3xl animate-bounce"></div>
                    <div className="absolute top-40 right-20 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl animate-pulse"></div>
                    <div className="absolute bottom-20 left-1/4 w-64 h-64 bg-indigo-600/5 rounded-full blur-3xl animate-bounce" style={{animationDelay: '1s'}}></div>
                    <div className="absolute inset-0 opacity-5">
                        <div className="absolute inset-0" style={{
                            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0)`,
                            backgroundSize: '40px 40px'
                        }}></div>
                    </div>
                    <svg className="absolute inset-0 w-full h-full opacity-10" viewBox="0 0 100 100" preserveAspectRatio="none">
                        <defs>
                            <linearGradient id="techGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#1E3A8A" stopOpacity="0.3"/>
                                <stop offset="50%" stopColor="#3730A3" stopOpacity="0.2"/>
                                <stop offset="100%" stopColor="#7C3AED" stopOpacity="0.3"/>
                            </linearGradient>
                        </defs>
                        <path d="M10,20 Q30,10 50,20 T90,20" stroke="url(#techGradient)" strokeWidth="0.3" fill="none"/>
                        <path d="M10,40 Q30,30 50,40 T90,40" stroke="url(#techGradient)" strokeWidth="0.3" fill="none"/>
                        <path d="M10,60 Q30,50 50,60 T90,60" stroke="url(#techGradient)" strokeWidth="0.3" fill="none"/>
                        <path d="M10,80 Q30,70 50,80 T90,80" stroke="url(#techGradient)" strokeWidth="0.3" fill="none"/>
                    </svg>
                </div>
            </div>

            {/* Content */}
            <div className="relative z-10 container mx-auto p-4 sm:p-6 lg:p-8">
                <header className="text-center my-8 md:my-12">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-700 rounded-2xl mb-6 shadow-2xl border border-blue-500/20">
                        <FileText className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-4">
                        <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                            Your Documents
                        </span>
                    </h1>
                    <p className="mt-4 max-w-3xl mx-auto text-lg text-gray-300 leading-relaxed">
                        Manage your uploaded documents. Remove any document you no longer need.
                    </p>
                </header>

                <main>
                    <div className="max-w-4xl mx-auto backdrop-blur-xl bg-black/40 rounded-3xl shadow-2xl border border-gray-800/50 p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-gray-100">Documents</h2>
                            <button
                                onClick={fetchDocuments}
                                className="flex items-center px-4 py-2 text-sm bg-gray-800/50 backdrop-blur-sm rounded-lg hover:bg-gray-700/50 transition-all duration-200 text-gray-200 border border-gray-600/50 hover:border-gray-500/50"
                                disabled={loading}
                            >
                                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                {loading ? 'Refreshing...' : 'Refresh'}
                            </button>
                        </div>
                        {loading && (
                            <div className="text-center py-8">
                                <div className="inline-flex items-center justify-center w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
                                <span className="text-gray-300">Loading documents...</span>
                            </div>
                        )}
                        {error && (
                            <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4 mb-4">
                                <p className="text-red-300">{error}</p>
                            </div>
                        )}
                        <div className="grid gap-4">
                            {documents.map((doc: any) => (
                                <div
                                    key={doc.id}
                                    className="flex items-center backdrop-blur-sm bg-gray-900/50 p-4 rounded-xl border border-gray-700/50 hover:bg-gray-800/50 transition-all duration-200 group"
                                >
                                    <div className="flex-shrink-0 mr-4">
                                        <div className="p-2 bg-gray-800/50 rounded-lg group-hover:bg-gray-700/50 transition-colors">
                                            {getFileIcon(doc.originalName)}
                                        </div>
                                    </div>
                                    <div className="flex-grow min-w-0">
                                        <h3 className="font-semibold text-gray-100 truncate">{doc.originalName}</h3>
                                        <p className="text-sm text-gray-400 mt-1">{doc.description || 'No description'}</p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Uploaded {new Date(doc.createdAt).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div className="flex-shrink-0 ml-4 flex items-center space-x-2">
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                            doc.status === 'SUCCESS' 
                                                ? 'bg-green-900/30 text-green-300 border border-green-500/30' 
                                                : 'bg-red-900/30 text-red-300 border border-red-500/30'
                                        }`}>
                                            {doc.status === 'SUCCESS' ? (
                                                <>
                                                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                                                    Processed
                                                </>
                                            ) : (
                                                <>
                                                    <div className="w-2 h-2 bg-red-400 rounded-full mr-2"></div>
                                                    Failed
                                                </>
                                            )}
                                        </span>
                                        {doc.ragDocId && (
                                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-900/30 text-blue-300 border border-blue-500/30">
                                                <Brain className="w-3 h-3 mr-1" />
                                                RAG Indexed
                                            </span>
                                        )}
                                        <button
                                            onClick={() => handleDelete(doc.id)}
                                            className="ml-2 p-2 text-red-300 rounded-lg hover:bg-red-900/30 hover:text-red-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-all duration-200"
                                            disabled={deletingId === doc.id}
                                            title="Delete document"
                                        >
                                            {deletingId === doc.id ? (
                                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                            ) : (
                                                <Trash2 className="h-5 w-5" />
                                            )}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {!loading && documents.length === 0 && !error && (
                            <div className="text-center py-12">
                                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-800/50 rounded-full mb-4">
                                    <FileText className="h-8 w-8 text-gray-400" />
                                </div>
                                <p className="text-gray-400">No documents found. Upload your first document to get started.</p>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default DocumentsPage; 