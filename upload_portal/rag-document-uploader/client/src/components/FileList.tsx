import React from 'react';
import { UploadFile } from '../App';
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
                    <h2 className="text-lg font-medium text-slate-900 mb-3">Ready for Upload</h2>
                    <ul className="space-y-3">
                        {files.map((fileObj, index) => (
                            <li
                                key={index}
                                className="flex items-center bg-slate-50 p-3 rounded-lg border border-slate-200"
                            >
                                <div className="flex-shrink-0 mr-4">
                                    {getFileIcon(fileObj.file.name)}
                                </div>
                                <div className="flex-grow">
                                    <div className="flex justify-between items-start">
                                        <span className="font-semibold text-slate-800 truncate" title={fileObj.file.name}>
                                            {fileObj.file.name}
                                        </span>
                                        <span className="text-sm text-slate-500 ml-2 whitespace-nowrap">
                                            {(fileObj.file.size / 1024).toFixed(2)} KB
                                        </span>
                                    </div>
                                    <input
                                        type="text"
                                        placeholder="Optional: Add a description..."
                                        className="mt-2 block w-full text-sm bg-white border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                                        value={fileObj.description}
                                        onChange={(e) => updateDescription(index, e.target.value)}
                                    />
                                </div>
                                <button
                                    onClick={() => removeFile(index)}
                                    className="ml-4 p-1.5 text-slate-500 rounded-full hover:bg-slate-200 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default FileList;