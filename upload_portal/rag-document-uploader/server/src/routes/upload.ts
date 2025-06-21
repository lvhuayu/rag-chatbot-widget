import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import axios from 'axios';
import pdf from 'pdf-parse';
import mammoth from 'mammoth';
import { PrismaClient } from '@prisma/client';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = express.Router();
const prisma = new PrismaClient();
const uploadDir = path.join(process.cwd(), 'uploads');
const RAG_BACKEND_URL = 'http://localhost:8001/add-document';

// Ensure the uploads directory exists
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`);
    }
});

const upload = multer({
    storage,
    limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
    fileFilter: (req, file, cb) => {
        const filetypes = /pdf|txt|docx/;
        const extname = filetypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = filetypes.test(file.mimetype);

        if (extname || mimetype) {
            return cb(null, true);
        }
        cb(new Error('Invalid file type. Only PDF, TXT, and DOCX files are allowed.'));
    }
});

// Function to extract text and index the document
async function processAndIndexFile(file: Express.Multer.File, description: string, userId: string) {
    let content = '';
    const filePath = file.path;

    try {
        const ext = path.extname(file.originalname).toLowerCase();
        if (ext === '.txt') {
            content = fs.readFileSync(filePath, 'utf-8');
        } else if (ext === '.pdf') {
            const dataBuffer = fs.readFileSync(filePath);
            const data = await pdf(dataBuffer);
            content = data.text;
        } else if (ext === '.docx') {
            const result = await mammoth.extractRawText({ path: filePath });
            content = result.value;
        }

        if (description) {
            content = `Description: ${description}\n\n${content}`;
        }

        // Send to Python RAG backend with user_id
        await axios.post(RAG_BACKEND_URL, {
            url: file.originalname,
            title: file.originalname,
            content: content,
            user_id: userId  // Include user_id for user-scoped storage
        });

        // Save document metadata to database
        await prisma.document.create({
            data: {
                userId: userId,
                originalName: file.originalname,
                fileSize: file.size,
                description: description || null,
                status: 'SUCCESS'
            }
        });

        return { success: true, file: file.originalname };
    } catch (error: any) {
        console.error(`Error processing ${file.originalname}:`, error.message);
        
        // Save failed document metadata to database
        await prisma.document.create({
            data: {
                userId: userId,
                originalName: file.originalname,
                fileSize: file.size,
                description: description || null,
                status: 'FAILED'
            }
        });

        return { success: false, file: file.originalname, error: error.message };
    } finally {
        // Clean up the uploaded file after processing
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
    }
}

// Route for file upload (now protected)
router.post('/', authenticateToken, upload.array('files', 5), async (req: AuthRequest, res) => {
    if (!req.files || !Array.isArray(req.files) || req.files.length === 0) {
        return res.status(400).send({ message: 'No files were uploaded.' });
    }

    if (!req.user) {
        return res.status(401).send({ message: 'User not authenticated.' });
    }

    const descriptions = req.body.descriptions || [];
    const files = req.files as Express.Multer.File[];

    const processingPromises = files.map((file, idx) =>
        processAndIndexFile(file, descriptions[idx] || '', req.user!.id)
    );

    try {
        const results = await Promise.all(processingPromises);
        const successful = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);

        if (failed.length > 0) {
            return res.status(500).send({
                message: 'Some files failed to process.',
                successful,
                failed,
            });
        }

        res.status(200).send({ message: 'All files uploaded and indexed successfully.', successful });
    } catch (error: any) {
        res.status(500).send({ message: 'An unexpected error occurred during processing.', error: error.message });
    }
});

// Route to get user's documents
router.get('/documents', authenticateToken, async (req: AuthRequest, res) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        const documents = await prisma.document.findMany({
            where: { userId: req.user.id },
            orderBy: { createdAt: 'desc' }
        });

        res.json(documents);
    } catch (error) {
        console.error('Error fetching documents:', error);
        res.status(500).send({ message: 'Error fetching documents.' });
    }
});

// Route to delete a specific document
router.delete('/documents/:id', authenticateToken, async (req: AuthRequest, res) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        const documentId = req.params.id;

        // Find the document and ensure it belongs to the authenticated user
        const document = await prisma.document.findFirst({
            where: { 
                id: documentId,
                userId: req.user.id 
            }
        });

        if (!document) {
            return res.status(404).send({ message: 'Document not found or access denied.' });
        }

        // Delete the document from the database
        await prisma.document.delete({
            where: { id: documentId }
        });

        // TODO: If you want to also remove from the Python RAG backend, add that logic here
        // Example: await axios.delete(`http://localhost:8001/remove-document/${document.originalName}`);

        res.json({ message: 'Document deleted successfully.' });
    } catch (error) {
        console.error('Error deleting document:', error);
        res.status(500).send({ message: 'Error deleting document.' });
    }
});

export default router;