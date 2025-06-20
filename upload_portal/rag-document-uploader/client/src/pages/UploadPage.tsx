import React, { useState } from 'react';
import FileUploader from '../components/FileUploader';
import FileList from '../components/FileList';
import DocumentList from '../components/DocumentList';

export interface UploadFile {
  file: File;
  description: string;
}

const UploadPage: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([]);

  const addFiles = (newFiles: File[]) => {
    // Prevent duplicates by name + size
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.file.name + f.file.size));
      const filtered = newFiles.filter(f => !existing.has(f.name + f.size));
      return [...prev, ...filtered.map(f => ({ file: f, description: '' }))];
    });
  };

  const updateDescription = (index: number, desc: string) => {
    setFiles(prev => prev.map((f, i) => i === index ? { ...f, description: desc } : f));
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => setFiles([]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8">
        <header className="text-center my-8 md:my-12">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900">
            AI-Powered RAG Document Portal
          </h1>
          <p className="mt-4 max-w-3xl mx-auto text-lg text-slate-600">
            Upload, manage, and sync your documents to enhance your Retrieval-Augmented Generation system with fresh knowledge.
          </p>
        </header>

        <main>
          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl ring-1 ring-slate-200/50">
            <FileUploader files={files} addFiles={addFiles} clearFiles={clearFiles} />
            <FileList files={files} updateDescription={updateDescription} removeFile={removeFile} />
          </div>
          <DocumentList />
        </main>
      </div>
    </div>
  );
};

export default UploadPage;