import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Extend AuthRequest from express.Request for type-safe params
export interface AuthRequest extends Request {
  user?: {
    id?: string;
    username?: string;
    apiKeyId?: string;
    origin?: string;
  };
}

export const authenticateToken = (req: AuthRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({ message: 'Access token required' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET) as any;
    // 支持用户登录Token和API Key签发Token
    req.user = {
      id: decoded.id,
      username: decoded.username,
      apiKeyId: decoded.apiKeyId,
      origin: decoded.origin,
    };
    next();
  } catch (error) {
    return res.status(403).json({ message: 'Invalid or expired token' });
  }
}; 