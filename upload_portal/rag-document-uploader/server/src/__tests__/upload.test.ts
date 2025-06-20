import request from 'supertest';
import express from 'express';
import path from 'path';
import fs from 'fs';
import uploadRoutes from '../routes/upload';
import axios from 'axios';

// Mock axios to prevent actual network calls
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Create a test express app
const app = express();
app.use(express.json());
app.use('/api/upload', uploadRoutes);

// Mock the uploads directory
const uploadsDir = path.join(process.cwd(), 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

describe('POST /api/upload', () => {
  it('should upload a file and return success', async () => {
    // Mock the axios post call to the Python backend
    mockedAxios.post.mockResolvedValue({ data: { success: true } });

    const filePath = path.join(uploadsDir, 'test.txt');
    const fileContent = 'This is a test file.';
    fs.writeFileSync(filePath, fileContent);

    const response = await request(app)
      .post('/api/upload')
      .attach('files', filePath)
      .field('descriptions', 'A test description');
    
    expect(response.status).toBe(200);
    expect(response.body.message).toBe('All files uploaded and indexed successfully.');
    expect(response.body.successful[0].file).toBe('test.txt');

    // The test should clean up after itself, but the route itself already does.
    // We just need to check if the file is gone.
    expect(fs.existsSync(filePath)).toBe(false);
  });

  it('should return a 400 error if no files are uploaded', async () => {
    const response = await request(app)
      .post('/api/upload');

    expect(response.status).toBe(400);
    expect(response.body.message).toBe('No files were uploaded.');
  });

  it('should handle errors from the Python backend', async () => {
    // Mock a failure from the Python backend
    mockedAxios.post.mockRejectedValue(new Error('RAG backend failed'));
    
    const filePath = path.join(uploadsDir, 'fail-test.txt');
    fs.writeFileSync(filePath, 'This file will fail to index.');

    const response = await request(app)
      .post('/api/upload')
      .attach('files', filePath);
      
    expect(response.status).toBe(500);
    expect(response.body.message).toBe('Some files failed to process.');
    expect(response.body.failed[0].file).toBe('fail-test.txt');
    expect(response.body.failed[0].error).toBe('RAG backend failed');
  });
}); 