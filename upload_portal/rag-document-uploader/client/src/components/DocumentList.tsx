import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, File, FileArchive } from 'lucide-react';

const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.pdf')) return <File color="red" className="h-8 w-8" />;
    if (fileName.endsWith('.docx')) return <FileArchive color="blue" className="h-8 w-8" />;
    if (fileName.endsWith('.txt')) return <FileText color="gray" className="h-8 w-8" />;
    return <File className="h-8 w-8" />;
};

const DocumentList = () => {
    const [documents, setDocuments] = useState([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDocuments = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get('/api/upload/documents', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                setDocuments(response.data);
            } catch (err) {
                setError('Failed to fetch documents');
            }
        };

        fetchDocuments();
    }, []);

    return (
        <div className="mt-6 w-full max-w-2xl">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Your Documents</h2>
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
        </div>
    );
};

export default DocumentList; 