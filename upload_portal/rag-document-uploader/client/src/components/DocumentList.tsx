import React from 'react';
import { FileText, File, FileArchive } from 'lucide-react';

const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.pdf')) return <File color="red" className="h-8 w-8" />;
    if (fileName.endsWith('.docx')) return <FileArchive color="blue" className="h-8 w-8" />;
    if (fileName.endsWith('.txt')) return <FileText color="gray" className="h-8 w-8" />;
    return <File className="h-8 w-8" />;
};

interface DocumentListProps {
    documents: any[];
    loading: boolean;
    error: string | null;
    refreshDocuments: () => void;
}

const DocumentList: React.FC<DocumentListProps> = ({ documents, loading, error, refreshDocuments }) => {
    return (
        <div className="w-full max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-100">Your Documents</h2>
                <button
                    onClick={refreshDocuments}
                    className="px-4 py-2 text-sm bg-gray-800/50 backdrop-blur-sm rounded-lg hover:bg-gray-700/50 transition-all duration-200 text-gray-200 border border-gray-600/50 hover:border-gray-500/50"
                    disabled={loading}
                >
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
                        <div className="flex-shrink-0 ml-4">
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
    );
};

export default DocumentList; 