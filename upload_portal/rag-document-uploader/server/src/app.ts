import express from 'express';
import path from 'path';
import uploadRoutes from './routes/upload';

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware to serve static files from the uploads directory
app.use('/uploads', express.static(path.join(process.cwd(), 'uploads')));

// Middleware for parsing application/json
app.use(express.json());

// Use the upload routes
app.use('/api/upload', uploadRoutes);

// Add a root GET route for a friendly message
app.get('/', (req, res) => {
  res.send('RAG Uploader backend is running.');
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});