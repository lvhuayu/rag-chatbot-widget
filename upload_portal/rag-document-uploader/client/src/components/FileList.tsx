import React from 'react';
import { UploadFile } from '../pages/UploadPage';
import { FileText, File, X, FileArchive } from 'lucide-react'; // Using FileArchive for DOCX

interface FileListProps {
    files: UploadFile[];
    updateDescription: (index: number, desc: string) => void;
    removeFile: (index: number) => void;
}

const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.pdf')) return <File color="red" className="h-8 w-8" />;
    if (fileName.endsWith('.docx')) return <FileArchive color="blue" className="h-8 w-8" />;
    if (fileName.endsWith('.txt')) return <FileText color="gray" className="h-8 w-8" />;
    return <File className="h-8 w-8" />;
};

const FileList: React.FC<FileListProps> = ({ files, updateDescription, removeFile }) => {
    return (
        <div className="px-6 sm:px-8 pb-6 sm:pb-8">
            {files.length > 0 && (
                <div className="mt-6">
                    <h2 className="text-lg font-semibold text-white mb-4">Ready for Upload</h2>
                    <div className="space-y-3">
                        {files.map((fileObj, index) => (
                            <div
                                key={index}
                                className="flex items-center backdrop-blur-sm bg-white/10 p-4 rounded-xl border border-white/20 hover:bg-white/15 transition-all duration-200"
                            >
                                <div className="flex-shrink-0 mr-4">
                                    <div className="p-2 bg-white/10 rounded-lg">
                                        {getFileIcon(fileObj.file.name)}
                                    </div>
                                </div>
                                <div className="flex-grow min-w-0">
                                    <div className="flex justify-between items-start">
                                        <span className="font-semibold text-white truncate" title={fileObj.file.name}>
                                            {fileObj.file.name}
                                        </span>
                                        <span className="text-sm text-blue-200/70 ml-2 whitespace-nowrap">
                                            {(fileObj.file.size / 1024).toFixed(2)} KB
                                        </span>
                                    </div>
                                    <input
                                        type="text"
                                        placeholder="Optional: Add a description..."
                                        className="mt-3 block w-full text-sm bg-white/10 border border-white/20 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-white placeholder-blue-200/50 backdrop-blur-sm transition-all duration-200"
                                        value={fileObj.description}
                                        onChange={(e) => updateDescription(index, e.target.value)}
                                    />
                                </div>
                                <button
                                    onClick={() => removeFile(index)}
                                    className="ml-4 p-2 text-blue-200/70 rounded-lg hover:bg-red-500/20 hover:text-red-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-all duration-200"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default FileList;