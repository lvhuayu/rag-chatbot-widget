# Registered Key Authentication for RAG Chatbot

This feature allows users to authenticate with the RAG chatbot using public/private keys that are automatically generated during user registration in the upload portal.

## Overview

When a user registers in the upload portal, the system automatically generates a public/private key pair. The public key is stored in the database and can be used for chatbot authentication, while the private key is encrypted and stored securely.

## How It Works

1. **Registration**: User registers in the upload portal
2. **Key Generation**: System generates RSA key pair (2048-bit)
3. **Storage**: Public key stored in database, private key encrypted with user's password
4. **Authentication**: Chatbot fetches public key and uses it for authentication
5. **Document Access**: User can only access their own uploaded documents

## Setup Instructions

### 1. Start the Upload Portal Server

```bash
cd upload_portal/rag-document-uploader/server
npm install
npm start
```

The upload portal will be available at `http://localhost:3001`

### 2. Start the Python RAG Backend

```bash
cd backend
pip install -r requirements_simple.txt
python rag_server_simple.py
```

The RAG backend will be available at `http://localhost:8001`

### 3. Register a User

1. Go to `http://localhost:3001/register`
2. Create an account with username and password
3. Copy the generated public key (displayed after registration)
4. Note your username for chatbot authentication

### 4. Use the Chatbot with Registered Key Authentication

#### Option A: Use the Example Page

1. Open `public/registered-key-example.html` in your browser
2. Enter your registered username
3. Click "Initialize Chatbot"

#### Option B: Use the Test Page

1. Open `public/test-registered-key-chatbot.html` in your browser
2. Enter your registered username
3. Click "Test Registered Key Authentication" to verify
4. Click "Initialize Chatbot" to start chatting

#### Option C: Use in Your Own Code

```javascript
// Initialize chatbot with registered key authentication
initRAGChatbot({
    backendUrl: 'http://localhost:8001',
    auth: {
        useRegisteredKey: true,
        registeredUsername: 'your_username_here',
        uploadPortalUrl: 'http://localhost:3001',
        publicKeyEndpoint: '/api/auth/public-key'
    }
});
```

## API Endpoints

### Upload Portal Endpoints

- `POST /api/auth/register` - Register user and generate keys
- `GET /api/auth/public-key/:username` - Get user's public key

### RAG Backend Endpoints

- `POST /auth/register-key` - Authenticate with registered public key
- `POST /search` - Search documents (requires authentication)
- `POST /add-document` - Add document (requires authentication)

## Security Features

1. **RSA Key Pair**: 2048-bit RSA keys for secure authentication
2. **Encrypted Storage**: Private keys encrypted with user's password
3. **User Isolation**: Each user can only access their own documents
4. **JWT Tokens**: Secure session management with JWT tokens
5. **No Private Key Exposure**: Private keys never leave the server

## Database Schema

The User model includes new fields:

```prisma
model User {
  id         String    @id @default(cuid())
  username   String    @unique
  password   String
  publicKey  String?   // Store the public key for chatbot authentication
  privateKey String?   // Store the private key (encrypted)
  documents  Document[]
  createdAt  DateTime  @default(now())
}
```

## Configuration Options

### Chatbot Configuration

```javascript
{
    backendUrl: 'http://localhost:8001',           // RAG backend URL
    auth: {
        useRegisteredKey: true,                    // Enable registered key auth
        registeredUsername: 'your_username',       // Username to authenticate
        uploadPortalUrl: 'http://localhost:3001',  // Upload portal URL
        publicKeyEndpoint: '/api/auth/public-key'  // Public key endpoint
    }
}
```

## Troubleshooting

### Common Issues

1. **"User not found"**: Make sure you've registered the user in the upload portal
2. **"Public key not found"**: The user registration may have failed
3. **"Failed to fetch public key"**: Check if the upload portal is running
4. **"Authentication failed"**: Verify the username is correct

### Debug Steps

1. Check that both servers are running:
   - Upload portal: `http://localhost:3001`
   - RAG backend: `http://localhost:8001`

2. Verify user registration:
   - Go to `http://localhost:3001/register`
   - Create a new account
   - Note the public key is displayed

3. Test the public key endpoint:
   - `GET http://localhost:3001/api/auth/public-key/your_username`

4. Check browser console for error messages

## Example Workflow

1. **Register**: User registers at upload portal
2. **Upload**: User uploads documents through the portal
3. **Authenticate**: Chatbot authenticates using registered public key
4. **Chat**: User can ask questions about their uploaded documents
5. **Isolation**: User only sees their own documents in search results

## Benefits

- **Secure**: Uses cryptographic keys for authentication
- **User-Friendly**: No need to manage keys manually
- **Isolated**: Each user's documents are completely separate
- **Automatic**: Keys generated during registration process
- **Flexible**: Can be used with existing chatbot interface

## Files Modified

- `upload_portal/rag-document-uploader/server/prisma/schema.prisma` - Database schema
- `upload_portal/rag-document-uploader/server/src/routes/auth.ts` - Registration and key endpoints
- `upload_portal/rag-document-uploader/client/src/pages/RegisterPage.tsx` - Registration UI
- `public/chatbot.js` - Chatbot authentication logic
- `backend/rag_server_simple.py` - RAG backend authentication
- `public/test-registered-key-chatbot.html` - Test page
- `public/registered-key-example.html` - Example usage page 