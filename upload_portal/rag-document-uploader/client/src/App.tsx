import React, { useState } from 'react';
import FileUploader from './components/FileUploader';
import FileList from './components/FileList';

export interface UploadFile {
  file: File;
  description: string;
}

const App: React.FC = () => {
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

  const clearFiles = () => setFiles([]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <h1 className="text-3xl font-bold mb-6">RAG Document Uploader</h1>
      <FileUploader files={files} addFiles={addFiles} clearFiles={clearFiles} />
      <FileList files={files} updateDescription={updateDescription} />
    </div>
  );
};

export default App;