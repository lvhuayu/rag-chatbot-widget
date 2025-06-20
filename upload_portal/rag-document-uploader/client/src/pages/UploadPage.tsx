import React, { useState, useCallback } from 'react';
import FileUploader from '../components/FileUploader';
import FileList from '../components/FileList';
import DocumentList from '../components/DocumentList';
import axios from 'axios';

export interface UploadFile {
  file: File;
  description: string;
}

const UploadPage: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);

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

  const fetchDocuments = useCallback(async () => {
    setDocLoading(true);
    setDocError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/upload/documents', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDocuments(response.data);
    } catch (err) {
      setDocError('Failed to fetch documents');
    } finally {
      setDocLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return (
    <div className="min-h-screen relative overflow-hidden bg-black">
      {/* Dark Tech Company Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black">
        {/* Subtle animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/5 via-purple-900/5 to-indigo-900/5 animate-pulse"></div>
        
        {/* Dark geometric patterns */}
        <div className="absolute top-0 left-0 w-full h-full">
          {/* Subtle floating circles */}
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-600/5 rounded-full blur-3xl animate-bounce"></div>
          <div className="absolute top-40 right-20 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-20 left-1/4 w-64 h-64 bg-indigo-600/5 rounded-full blur-3xl animate-bounce" style={{animationDelay: '1s'}}></div>
          
          {/* Dark grid pattern */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute inset-0" style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0)`,
              backgroundSize: '40px 40px'
            }}></div>
          </div>
          
          {/* Dark tech circuit lines */}
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
          {/* Dark tech company logo/brand */}
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-700 rounded-2xl mb-6 shadow-2xl border border-blue-500/20">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-4">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              AI-Powered RAG
            </span>
            <br />
            <span className="text-gray-100">Document Portal</span>
          </h1>
          
          <p className="mt-4 max-w-3xl mx-auto text-lg text-gray-300 leading-relaxed">
            Transform your documents into intelligent knowledge. Upload, process, and enhance your 
            <span className="font-semibold text-blue-300"> Retrieval-Augmented Generation</span> system with cutting-edge AI technology.
          </p>
          
          {/* Dark tech stats */}
          <div className="flex justify-center space-x-8 mt-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">99.9%</div>
              <div className="text-sm text-gray-400">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">AI-Powered</div>
              <div className="text-sm text-gray-400">Processing</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-400">Secure</div>
              <div className="text-sm text-gray-400">Encryption</div>
            </div>
          </div>
        </header>

        <main>
          {/* Dark glass morphism card */}
          <div className="max-w-4xl mx-auto backdrop-blur-xl bg-black/40 rounded-3xl shadow-2xl border border-gray-800/50">
            <FileUploader files={files} addFiles={addFiles} clearFiles={clearFiles} onUploadSuccess={fetchDocuments} />
            <FileList files={files} updateDescription={updateDescription} removeFile={removeFile} />
          </div>
          
          {/* Dark documents section */}
          <div className="mt-8 backdrop-blur-xl bg-black/30 rounded-3xl shadow-2xl border border-gray-800/30 p-6">
            <DocumentList documents={documents} loading={docLoading} error={docError} refreshDocuments={fetchDocuments} />
          </div>
        </main>

        {/* Dark footer */}
        <footer className="text-center mt-12 text-gray-500">
          <p className="text-sm">
            Powered by advanced AI technology • Enterprise-grade security • Built for scale
          </p>
        </footer>
      </div>
    </div>
  );
};

export default UploadPage;