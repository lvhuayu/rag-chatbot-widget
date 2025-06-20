import { Request, Response, NextFunction } from 'express';

const allowedFileTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
const maxFileSize = 10 * 1024 * 1024; // 10MB

export const fileValidation = (req: Request, res: Response, next: NextFunction) => {
    const files = req.files;

    if (!files || files.length === 0) {
        return res.status(400).json({ message: 'No files uploaded.' });
    }

    for (const file of files) {
        if (!allowedFileTypes.includes(file.mimetype)) {
            return res.status(400).json({ message: `Invalid file type: ${file.mimetype}. Only PDF, TXT, and DOCX are allowed.` });
        }

        if (file.size > maxFileSize) {
            return res.status(400).json({ message: `File size exceeds the limit of 10MB for file: ${file.originalname}.` });
        }
    }

    next();
};