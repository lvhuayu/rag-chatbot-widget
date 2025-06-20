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
                <h2 className="text-2xl font-bold text-white">Your Documents</h2>
                <button
                    onClick={refreshDocuments}
                    className="px-4 py-2 text-sm bg-white/10 backdrop-blur-sm rounded-lg hover:bg-white/20 transition-all duration-200 text-white border border-white/20 hover:border-white/30"
                    disabled={loading}
                >
                    {loading ? 'Refreshing...' : 'Refresh'}
                </button>
            </div>
            
            {loading && (
                <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mr-2"></div>
                    <span className="text-blue-200">Loading documents...</span>
                </div>
            )}
            
            {error && (
                <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 mb-4">
                    <p className="text-red-300">{error}</p>
                </div>
            )}
            
            <div className="grid gap-4">
                {documents.map((doc: any) => (
                    <div
                        key={doc.id}
                        className="flex items-center backdrop-blur-sm bg-white/10 p-4 rounded-xl border border-white/20 hover:bg-white/15 transition-all duration-200 group"
                    >
                        <div className="flex-shrink-0 mr-4">
                            <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-colors">
                                {getFileIcon(doc.originalName)}
                            </div>
                        </div>
                        <div className="flex-grow min-w-0">
                            <h3 className="font-semibold text-white truncate">{doc.originalName}</h3>
                            <p className="text-sm text-blue-200/70 mt-1">{doc.description || 'No description'}</p>
                            <p className="text-xs text-blue-200/50 mt-1">
                                Uploaded {new Date(doc.createdAt).toLocaleDateString()}
                            </p>
                        </div>
                        <div className="flex-shrink-0 ml-4">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                doc.status === 'SUCCESS' 
                                    ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                                    : 'bg-red-500/20 text-red-300 border border-red-500/30'
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
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-full mb-4">
                        <FileText className="h-8 w-8 text-blue-300" />
                    </div>
                    <p className="text-blue-200/70">No documents found. Upload your first document to get started.</p>
                </div>
            )}
        </div>
    );
};

export default DocumentList; 