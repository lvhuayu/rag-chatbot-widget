import React from 'react';
import { UploadFile } from '../App';

interface FileListProps {
    files: UploadFile[];
    updateDescription: (index: number, desc: string) => void;
}

const FileList: React.FC<FileListProps> = ({ files, updateDescription }) => {
    if (files.length === 0) return null;
    return (
        <div className="mt-4 w-full max-w-xl">
            <h2 className="text-lg font-semibold mb-2">Files to Upload</h2>
            <ul className="list-disc pl-5">
                {files.map((fileObj, index) => (
                    <li key={index} className="flex justify-between items-center mb-2">
                        <div>
                            <span className="font-medium">{fileObj.file.name}</span> - <span>{(fileObj.file.size / 1024).toFixed(2)} KB</span>
                        </div>
                        <input
                            type="text"
                            placeholder="Optional description"
                            className="ml-4 border border-gray-300 rounded p-1"
                            value={fileObj.description}
                            onChange={e => updateDescription(index, e.target.value)}
                        />
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default FileList;