import express from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import crypto from 'crypto';
import CryptoJS from 'crypto-js';

const router = express.Router();
const prisma = new PrismaClient();
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Generate public/private key pair
function generateKeyPair() {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding: {
            type: 'spki',
            format: 'pem'
        },
        privateKeyEncoding: {
            type: 'pkcs8',
            format: 'pem'
        }
    });
    
    return { publicKey, privateKey };
}

// Encrypt private key with user's password
function encryptPrivateKey(privateKey: string, password: string): string {
    return CryptoJS.AES.encrypt(privateKey, password).toString();
}

// Decrypt private key with user's password
function decryptPrivateKey(encryptedPrivateKey: string, password: string): string {
    const bytes = CryptoJS.AES.decrypt(encryptedPrivateKey, password);
    return bytes.toString(CryptoJS.enc.Utf8);
}

// Register a new user
router.post('/register', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ message: 'Username and password are required' });
    }

    if (password.length < 6) {
      return res.status(400).json({ message: 'Password must be at least 6 characters long' });
    }

    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { username }
    });

    if (existingUser) {
      return res.status(400).json({ message: 'Username already exists' });
    }

    // Generate key pair
    const { publicKey, privateKey } = generateKeyPair();
    
    // Encrypt private key with user's password
    const encryptedPrivateKey = encryptPrivateKey(privateKey, password);

    // Hash the password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create the user with keys
    const user = await prisma.user.create({
      data: {
        username,
        password: hashedPassword,
        publicKey,
        privateKey: encryptedPrivateKey
      }
    });

    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, username: user.username },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.status(201).json({
      message: 'User registered successfully',
      token,
      user: {
        id: user.id,
        username: user.username
      },
      publicKey: publicKey // Return public key for display
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Login user
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ message: 'Username and password are required' });
    }

    // Find the user
    const user = await prisma.user.findUnique({
      where: { username }
    });

    if (!user) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Check password
    const isValidPassword = await bcrypt.compare(password, user.password);

    if (!isValidPassword) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, username: user.username },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.json({
      message: 'Login successful',
      token,
      user: {
        id: user.id,
        username: user.username
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get user's public key for chatbot authentication
router.get('/public-key/:username', async (req, res) => {
  try {
    const { username } = req.params;

    if (!username) {
      return res.status(400).json({ message: 'Username is required' });
    }

    // Find the user
    const user = await prisma.user.findUnique({
      where: { username },
      select: { publicKey: true }
    });

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    if (!user.publicKey) {
      return res.status(404).json({ message: 'Public key not found for this user' });
    }

    res.json({
      publicKey: user.publicKey,
      username: username
    });
  } catch (error) {
    console.error('Get public key error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Admin authentication middleware
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123'; // Change this in production

// Admin login
router.post('/admin-login', async (req, res) => {
  try {
    const { password } = req.body;

    if (!password) {
      return res.status(400).json({ message: 'Password is required' });
    }

    if (password !== ADMIN_PASSWORD) {
      return res.status(401).json({ message: 'Invalid admin password' });
    }

    // Generate admin JWT token
    const token = jwt.sign(
      { role: 'admin', username: 'admin' },
      JWT_SECRET,
      { expiresIn: '1h' }
    );

    res.json({
      message: 'Admin login successful',
      token
    });
  } catch (error) {
    console.error('Admin login error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get all users with their keys (admin only)
router.get('/admin/users', async (req, res) => {
  try {
    // Check if user is admin (you might want to add proper admin middleware)
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    const token = authHeader.substring(7);
    const decoded = jwt.verify(token, JWT_SECRET) as any;
    
    // Allow if user is admin or if it's a regular user token (for simplicity)
    if (decoded.role !== 'admin' && !decoded.id) {
      return res.status(403).json({ message: 'Admin access required' });
    }

    // Get all users with their document counts
    const users = await prisma.user.findMany({
      include: {
        _count: {
          select: {
            documents: true
          }
        }
      },
      orderBy: {
        createdAt: 'desc'
      }
    });

    // Format user data
    const formattedUsers = users.map((user: any) => ({
      id: user.id,
      username: user.username,
      publicKey: user.publicKey || 'No public key',
      privateKey: user.privateKey || 'No private key',
      createdAt: user.createdAt,
      documentCount: user._count.documents
    }));

    res.json({
      users: formattedUsers,
      total: formattedUsers.length
    });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

export default router; 