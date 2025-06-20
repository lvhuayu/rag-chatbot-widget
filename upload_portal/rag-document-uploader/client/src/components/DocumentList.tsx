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
        <div className="mt-6 w-full max-w-2xl">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Your Documents</h2>
                <button
                    onClick={refreshDocuments}
                    className="px-3 py-1 text-sm bg-slate-200 rounded hover:bg-slate-300 transition"
                    disabled={loading}
                >
                    Refresh
                </button>
            </div>
            {loading && <p className="text-sm text-gray-500">Loading documents...</p>}
            {error && <p className="text-sm text-red-600">{error}</p>}
            <ul className="space-y-4">
                {documents.map((doc: any) => (
                    <li
                        key={doc.id}
                        className="flex items-center bg-white p-4 rounded-lg shadow-md border border-gray-200"
                    >
                        <div className="flex-shrink-0 mr-4">
                            {getFileIcon(doc.originalName)}
                        </div>
                        <div className="flex-grow">
                            <span className="font-semibold text-gray-900 truncate">{doc.originalName}</span>
                            <p className="text-sm text-gray-500">{doc.description || 'No description'}</p>
                        </div>
                        <span className={`text-sm font-medium ${doc.status === 'SUCCESS' ? 'text-green-600' : 'text-red-600'}`}>
                            {doc.status}
                        </span>
                    </li>
                ))}
            </ul>
            {!loading && documents.length === 0 && !error && (
                <p className="text-sm text-gray-500 mt-4">No documents found.</p>
            )}
        </div>
    );
};

export default DocumentList; 