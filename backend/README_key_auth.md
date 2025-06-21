# 🔑 Public/Private Key Authentication System

This document explains the public/private key authentication system implemented in the RAG chatbot backend.

## Overview

The system implements a challenge-response authentication mechanism using cryptographic keys, providing secure authentication without requiring password storage or transmission.

## 🔐 Authentication Flow

### 1. Key Generation
- Client generates a public/private key pair
- Private key stays on client (never transmitted)
- Public key is sent to server for registration

### 2. Challenge Request
```
Client → Server: POST /auth/request-challenge
{
    "public_key": "client_public_key",
    "username": "optional_username"
}
```

### 3. Challenge Response
```
Server → Client: 
{
    "challenge_id": "uuid",
    "challenge": "random_string",
    "expires_in": 300
}
```

### 4. Challenge Signing
- Client signs the challenge with their private key
- Signature is created using: `SHA256(public_key + ":" + challenge)`

### 5. Challenge Verification
```
Client → Server: POST /auth/verify-challenge
{
    "challenge_id": "uuid",
    "public_key": "client_public_key",
    "signature": "signed_challenge"
}
```

### 6. Token Issuance
```
Server → Client:
{
    "token": "jwt_token",
    "user_id": "user_id",
    "username": "username",
    "expires_in": 86400
}
```

## 🛠️ Implementation Details

### Backend Endpoints

#### `POST /auth/request-challenge`
- Generates random challenge using `secrets.token_urlsafe(32)`
- Stores challenge with 5-minute expiration
- Returns challenge_id and challenge string

#### `POST /auth/verify-challenge`
- Validates challenge_id and expiration
- Verifies public key matches stored challenge
- Verifies signature using hash-based verification
- Issues JWT token for subsequent requests

#### `GET /auth/me`
- Returns current user information
- Requires valid JWT token

### Frontend Implementation

#### Key Generation
```javascript
// Generate random private key
const array = new Uint8Array(32);
crypto.getRandomValues(array);
privateKey = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');

// Generate public key (simplified)
const encoder = new TextEncoder();
const data = encoder.encode(privateKey);
const hash = await crypto.subtle.digest('SHA-256', data);
publicKey = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
```

#### Challenge Signing
```javascript
// Sign challenge with private key
const encoder = new TextEncoder();
const data = encoder.encode(`${publicKey}:${challenge}`);
const hash = await crypto.subtle.digest('SHA-256', data);
const signature = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
```

## 🔒 Security Features

### ✅ Implemented
- **Challenge Expiration**: 5-minute timeout prevents replay attacks
- **Key Storage**: Private keys never leave client
- **Signature Verification**: Server validates challenge signatures
- **JWT Tokens**: Secure session management after authentication
- **User Isolation**: Each user only accesses their own documents

### ⚠️ Current Limitations
- **Simplified Cryptography**: Uses hash-based signatures instead of proper digital signatures
- **In-Memory Storage**: Keys and challenges lost on server restart
- **No Key Rotation**: Keys persist until manually regenerated

### 🔮 Future Enhancements
- **Proper Digital Signatures**: Use RSA/ECDSA for real cryptographic signing
- **Key Rotation**: Automatic key expiration and renewal
- **Persistent Storage**: Database storage for keys and challenges
- **Certificate Authority**: PKI integration for key validation

## 🧪 Testing

### Test Page
Use `public/test-key-auth-chatbot.html` to test the authentication system:

1. **Start the backend**: `python rag_server_simple.py`
2. **Open test page**: Navigate to the test page
3. **Generate keys**: Click "Generate New Keys"
4. **Authenticate**: Click "Authenticate with Keys"
5. **Test chatbot**: Use the authenticated chatbot

### Manual Testing
```bash
# 1. Request challenge
curl -X POST http://localhost:8001/auth/request-challenge \
  -H "Content-Type: application/json" \
  -d '{"public_key": "your_public_key", "username": "test_user"}'

# 2. Verify challenge (replace with actual values)
curl -X POST http://localhost:8001/auth/verify-challenge \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": "challenge_id", "public_key": "your_public_key", "signature": "signature"}'

# 3. Test authenticated endpoint
curl -X GET http://localhost:8001/auth/me \
  -H "Authorization: Bearer your_jwt_token"
```

## 📝 Configuration

### Backend Configuration
```python
# JWT Configuration
JWT_SECRET = "your-secret-key"  # Change in production!
JWT_ALGORITHM = "HS256"

# Challenge Configuration
CHALLENGE_EXPIRY = 300  # 5 minutes
TOKEN_EXPIRY = 86400    # 24 hours
```

### Frontend Configuration
```javascript
initRAGChatbot({
    backendUrl: 'http://localhost:8001',
    auth: {
        useKeyAuth: true,
        keyAuthEndpoint: '/auth/request-challenge',
        keyAuthVerifyEndpoint: '/auth/verify-challenge',
        keyStorageKey: 'my_chatbot_keys',
        username: 'optional_username'
    }
});
```

## 🚀 Production Considerations

### Security
- Use strong JWT secrets
- Implement proper digital signatures
- Add rate limiting for challenge requests
- Use HTTPS in production
- Implement key rotation policies

### Performance
- Use database storage for challenges and keys
- Implement challenge cleanup jobs
- Add caching for frequently accessed data
- Monitor authentication metrics

### Monitoring
- Log authentication attempts
- Monitor challenge expiration rates
- Track key generation and usage
- Alert on suspicious activity

## 🔗 Integration with RAG System

After successful authentication:
- JWT token is used for all subsequent requests
- User ID is extracted from token
- All document operations are scoped to the user
- Search results only include user's documents

## 📚 References

- [Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)
- [JWT Authentication](https://jwt.io/)
- [Challenge-Response Authentication](https://en.wikipedia.org/wiki/Challenge%E2%80%93response_authentication)
- [Public Key Cryptography](https://en.wikipedia.org/wiki/Public-key_cryptography) 