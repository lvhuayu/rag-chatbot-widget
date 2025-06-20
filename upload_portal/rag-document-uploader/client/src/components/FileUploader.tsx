import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadFile } from '../pages/UploadPage';
import { FileUp, X, Loader2 } from 'lucide-react';

interface FileUploaderProps {
    files: UploadFile[];
    addFiles: (files: File[]) => void;
    clearFiles: () => void;
    onUploadSuccess?: () => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({ files, addFiles, clearFiles, onUploadSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (files.length + acceptedFiles.length > 5) {
            setError('You can only upload a maximum of 5 files.');
            return;
        }
        const validFiles = acceptedFiles.filter(file => file.size <= 10 * 1024 * 1024);
        if (validFiles.length !== acceptedFiles.length) {
            setError('One or more files exceed the 10MB size limit.');
            return;
        }
        addFiles(validFiles);
        setError(null);
    }, [files, addFiles]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'text/plain': ['.txt'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        },
        maxSize: 10 * 1024 * 1024,
    });

    const handleUpload = async () => {
        setLoading(true);
        setError(null);
        const formData = new FormData();
        files.forEach((f) => {
            formData.append('files', f.file);
            formData.append(`descriptions`, f.description || '');
        });

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
            });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.message || 'Upload failed. Please try again.');
            }
            clearFiles();
            if (onUploadSuccess) onUploadSuccess();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full p-6 sm:p-8">
            <div
                {...getRootProps()}
                className={`relative flex flex-col items-center justify-center w-full p-10 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 ease-in-out backdrop-blur-sm
                ${isDragActive 
                    ? 'border-blue-400 bg-blue-500/20 shadow-lg shadow-blue-500/25' 
                    : 'border-white/30 bg-white/5 hover:border-blue-400/50 hover:bg-white/10'
                }`}
            >
                <input {...getInputProps()} />
                <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-4 shadow-lg">
                        <FileUp className="h-8 w-8 text-white" />
                    </div>
                    <p className="mt-4 text-lg text-white">
                        <span className="font-semibold text-blue-300">Click to upload</span> or drag and drop
                    </p>
                    <p className="mt-1 text-sm text-blue-200/70">Supports: PDF, TXT, DOCX (Max 10MB each)</p>
                </div>
            </div>

            {error && (
                <div className="mt-4 flex items-center justify-center text-red-300 bg-red-500/20 p-3 rounded-lg border border-red-500/30">
                    <X className="h-5 w-5 mr-2 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            <div className="mt-6 flex justify-end">
                <button
                    onClick={handleUpload}
                    className="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-lg text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                    disabled={loading || files.length === 0}
                >
                    {loading ? (
                        <>
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            <span>Processing...</span>
                        </>
                    ) : (
                        `Upload ${files.length} ${files.length === 1 ? 'File' : 'Files'}`
                    )}
                </button>
            </div>
        </div>
    );
};

export default FileUploader;