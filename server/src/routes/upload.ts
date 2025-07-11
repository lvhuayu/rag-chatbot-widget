import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import axios from 'axios';
import pdf from 'pdf-parse';
import mammoth from 'mammoth';
import { PrismaClient } from '@prisma/client';
import { authenticateToken, AuthRequest } from '../middleware/auth';
import cuid from 'cuid';

const router = express.Router();
const prisma = new PrismaClient();
const uploadDir = path.join(process.cwd(), 'uploads');
const RAG_BACKEND_URL = process.env.RAG_BACKEND_URL;

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
async function processAndIndexFile(file: any, description: string, siteId: string) {
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

        // Send to Python RAG backend with site_id
        await axios.post(
            `${RAG_BACKEND_URL}/add-documents`,
            [{
                url: file.originalname,
                title: file.originalname,
                content: content,
                site_id: siteId  // Use site_id for tenant-scoped storage
            }],
            { headers: { 'Content-Type': 'application/json' } }
        );

        // Save document metadata to database (only allowed fields)
        // await prisma.documents.create({
        //     data: {
        //         id: cuid(),
        //         site_id: siteId,
        //         title: file.originalname,
        //         url: file.originalname,
        //         content: content,
        //         created_at: new Date()
        //     }
        // });

        return { success: true, file: file.originalname };
    } catch (error: any) {
        console.error(`Error processing ${file.originalname}:`, error.message);
        
        // Save failed document metadata to database (only allowed fields, mark title as failed)
        // await prisma.documents.create({
        //     data: {
        //         id: cuid(),
        //         site_id: siteId,
        //         title: `[FAILED] ${file.originalname}`,
        //         url: file.originalname,
        //         content: error.message || 'Failed to process file.',
        //         created_at: new Date()
        //     }
        // });

        return { success: false, file: file.originalname, error: error.message };
    } finally {
        // Clean up the uploaded file after processing
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
    }
}

// Route for file upload (now protected)
router.post('/', authenticateToken, upload.array('files', 5), async (req: any, res: any) => {
    if (!req.files || !Array.isArray(req.files) || req.files.length === 0) {
        return res.status(400).send({ message: 'No files were uploaded.' });
    }

    if (!req.user) {
        return res.status(401).send({ message: 'User not authenticated.' });
    }

    // Fetch site_id for the user
    const site = await prisma.sites.findFirst({ where: { user_id: req.user.id } });
    if (!site) {
        return res.status(400).send({ message: 'No site found for user.' });
    }
    const siteId = site.site_id;

    const descriptions = req.body.descriptions || [];
    const files = req.files as any[];

    const processingPromises = files.map((file, idx) =>
        processAndIndexFile(file, descriptions[idx] || '', siteId)
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
router.get('/documents', authenticateToken, async (req: any, res: any) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        // Fetch site_id for the user
        const site = await prisma.sites.findFirst({ where: { user_id: req.user.id } });
        if (!site) {
            return res.status(404).send({ message: 'No site found for user.' });
        }
        const siteId = site.site_id;

        // Fetch documents from Python backend
        const pyResp = await axios.get(`${RAG_BACKEND_URL}/documents`, { params: { site_id: siteId } });
        res.json(pyResp.data);
    } catch (error) {
        console.error('Error fetching documents:', error);
        res.status(500).send({ message: 'Error fetching documents.' });
    }
});

// Route to delete a specific document
router.delete('/documents/:id', authenticateToken, async (req: any, res: any) => {
    try {
        if (!req.user) {
            return res.status(401).send({ message: 'User not authenticated.' });
        }

        const documentId = req.params.id;

        // Fetch site_id for the user
        const site = await prisma.sites.findFirst({ where: { user_id: req.user.id } });
        if (!site) {
            return res.status(404).send({ message: 'No site found for user.' });
        }
        const siteId = site.site_id;

        // Delete document from Python backend
        // (Assumes you have a DELETE endpoint like /documents/:id in Python backend)
        const pyResp = await axios.delete(`${RAG_BACKEND_URL}/documents/${documentId}`, { params: { site_id: siteId } });
        res.json(pyResp.data);
    } catch (error) {
        console.error('Error deleting document:', error);
        res.status(500).send({ message: 'Error deleting document.' });
    }
});

export default router; 