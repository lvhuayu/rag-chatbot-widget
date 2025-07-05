import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import pdf from 'pdf-parse';
import mammoth from 'mammoth';
import { PrismaClient } from '@prisma/client';
import { authenticateToken, AuthRequest } from '../middleware/auth';
import RAGService, { RAGDocument } from '../services/ragService';

const router = express.Router();
const prisma = new PrismaClient();
const uploadDir = path.join(process.cwd(), 'uploads');
const ragService = new RAGService();

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

        // Create RAG document object
        const ragDocument: RAGDocument = {
            url: file.originalname,
            title: file.originalname,
            content: content,
            user_id: userId,
            timestamp: new Date().toISOString()
        };

        // Send to RAG backend using the service
        const ragResult = await ragService.addDocument(ragDocument);
        
        if (!ragResult.success) {
            throw new Error(`RAG indexing failed: ${ragResult.message}`);
        }

        // Save document metadata to database
        await prisma.document.create({
            data: {
                userId: userId,
                originalName: file.originalname,
                fileSize: file.size,
                description: description || null,
                status: 'SUCCESS',
                ragDocId: ragResult.doc_id // Store the RAG document ID for reference
            }
        });

        return { 
            success: true, 
            file: file.originalname, 
            ragDocId: ragResult.doc_id,
            message: ragResult.message 
        };
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

        // TODO: If you want to also remove from the RAG backend, add that logic here
        // For now, we'll keep the document in RAG backend for consistency

        res.json({ message: 'Document deleted successfully.' });
    } catch (error) {
        console.error('Error deleting document:', error);
        res.status(500).send({ message: 'Error deleting document.' });
    }
});

// Route to get RAG documents for a user
router.get('/rag-documents', authenticateToken, async (req: AuthRequest, res) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        const ragDocuments = await ragService.getUserDocuments(req.user.id);
        res.json(ragDocuments);
    } catch (error: any) {
        console.error('Error fetching RAG documents:', error);
        res.status(500).send({ message: 'Error fetching RAG documents.', error: error.message });
    }
});

// Route to search RAG documents for a user
router.post('/search', authenticateToken, async (req: AuthRequest, res) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        const { query, top_k = 5, threshold = 0.7 } = req.body;

        if (!query) {
            return res.status(400).send({ message: 'Query is required.' });
        }

        const searchResult = await ragService.searchDocuments({
            query,
            top_k,
            threshold,
            user_id: req.user.id
        });

        res.json(searchResult);
    } catch (error: any) {
        console.error('Error searching RAG documents:', error);
        res.status(500).send({ message: 'Error searching RAG documents.', error: error.message });
    }
});

// Route to get RAG statistics for a user
router.get('/rag-stats', authenticateToken, async (req: AuthRequest, res) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        const stats = await ragService.getStats(req.user.id);
        res.json(stats);
    } catch (error: any) {
        console.error('Error fetching RAG stats:', error);
        res.status(500).send({ message: 'Error fetching RAG stats.', error: error.message });
    }
});

// Route to get system-wide RAG statistics (admin only)
router.get('/rag-stats/all', authenticateToken, async (req: AuthRequest, res) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        // Check if user is admin (you might want to add an isAdmin field to your User model)
        const user = await prisma.user.findUnique({
            where: { id: req.user.id }
        });

        if (!user || user.username !== 'admin') {
            return res.status(403).send({ message: 'Admin access required.' });
        }

        const stats = await ragService.getStats();
        res.json(stats);
    } catch (error: any) {
        console.error('Error fetching system RAG stats:', error);
        res.status(500).send({ message: 'Error fetching system RAG stats.', error: error.message });
    }
});

// Route to get RAG system health
router.get('/rag-health', authenticateToken, async (req: AuthRequest, res) => {
    try {
        const health = await ragService.getHealth();
        res.json(health);
    } catch (error: any) {
        console.error('Error fetching RAG health:', error);
        res.status(500).send({ message: 'Error fetching RAG health.', error: error.message });
    }
});

// Route to check RAG backend availability
router.get('/rag-available', async (req, res) => {
    try {
        const isAvailable = await ragService.isAvailable();
        res.json({ available: isAvailable });
    } catch (error: any) {
        res.json({ available: false, error: error.message });
    }
});

export default router;