import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import LoadingIndicator from './LoadingIndicator';
import { UploadFile } from '../App';

interface FileUploaderProps {
    files: UploadFile[];
    addFiles: (files: File[]) => void;
    clearFiles: () => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({ files, addFiles, clearFiles }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onDrop = (acceptedFiles: File[]) => {
        if (files.length + acceptedFiles.length > 5) {
            setError('You can only upload a maximum of 5 files.');
            return;
        }

        const validFiles = acceptedFiles.filter(file => file.size <= 10 * 1024 * 1024);
        if (validFiles.length !== acceptedFiles.length) {
            setError('Some files exceed the 10MB size limit.');
            return;
        }

        addFiles(validFiles);
        setError(null);
    };

    const { getRootProps, getInputProps } = useDropzone({
        onDrop,
        accept: { 'application/pdf': [], 'text/plain': [], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [] },
        maxSize: 10 * 1024 * 1024,
    });

    const handleUpload = async () => {
        setLoading(true);
        setError(null);

        const formData = new FormData();
        files.forEach((f, i) => {
            formData.append('files', f.file);
            formData.append(`descriptions`, f.description || '');
        });

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.message || 'Upload failed');
            }

            clearFiles();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4 w-full max-w-xl">
            <h1 className="text-xl font-bold mb-4">RAG Document Uploader</h1>
            <div {...getRootProps()} className="border-dashed border-2 border-gray-400 p-6 mb-4 text-center cursor-pointer bg-white">
                <input {...getInputProps()} />
                <p>Drag 'n' drop some files here, or click to select files</p>
                <p className="text-sm text-gray-500">Only PDF, TXT, and DOCX files are accepted (max 10MB each, up to 5 files).</p>
            </div>
            {error && <p className="text-red-500 mb-2">{error}</p>}
            {loading && <LoadingIndicator />}
            <button onClick={handleUpload} className="bg-blue-500 text-white px-4 py-2 rounded mt-2" disabled={loading || files.length === 0}>
                Upload Files
            </button>
        </div>
    );
};

export default FileUploader;