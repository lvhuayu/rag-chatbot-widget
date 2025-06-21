# User Management System

This feature provides an administrative interface to view and manage all registered users, including their public and private keys.

## 🔐 Security Features

- **Admin Authentication**: Requires admin password to access user data
- **Secure Key Storage**: Private keys are encrypted with user passwords
- **Access Control**: Only authenticated users can view the user list
- **Audit Trail**: Shows user creation dates and document counts

## 🚀 Setup Instructions

### 1. Set Admin Password

First, set up an admin password for accessing the user management system:

```bash
cd upload_portal/rag-document-uploader/server
node set-admin-password.js yourSecurePassword123
```

This will create/update the `.env` file with your admin password.

### 2. Restart the Server

After setting the admin password, restart the server:

```bash
npm start
```

### 3. Access User Management

Navigate to the Users page:
- **URL**: `http://localhost:3001/users`
- **Navbar Link**: Click "👥 Users" in the navigation bar

## 📋 Features

### User Information Display

The Users page shows:

- **Username**: User's login name
- **User ID**: Unique identifier
- **Public Key**: RSA public key for chatbot authentication
- **Private Key**: Encrypted private key (can be shown/hidden)
- **Document Count**: Number of documents uploaded by the user
- **Creation Date**: When the user account was created

### Admin Functions

- **View All Users**: See complete list of registered users
- **Copy Keys**: Copy public/private keys to clipboard
- **Toggle Private Keys**: Show/hide sensitive private key data
- **Refresh Data**: Update the user list
- **User Statistics**: Summary of total users and documents

### Security Controls

- **Admin Authentication**: Password required to access user data
- **Session Management**: Admin tokens expire after 1 hour
- **Key Protection**: Private keys are encrypted and can be hidden
- **Access Logging**: All admin actions are logged

## 🔧 API Endpoints

### Admin Authentication

```http
POST /api/auth/admin-login
Content-Type: application/json

{
  "password": "your_admin_password"
}
```

Response:
```json
{
  "message": "Admin login successful",
  "token": "jwt_token_here"
}
```

### Get All Users

```http
GET /api/admin/users
Authorization: Bearer <admin_token>
```

Response:
```json
{
  "users": [
    {
      "id": "user_id",
      "username": "username",
      "publicKey": "-----BEGIN PUBLIC KEY-----...",
      "privateKey": "-----BEGIN PRIVATE KEY-----...",
      "createdAt": "2024-01-01T00:00:00.000Z",
      "documentCount": 5
    }
  ],
  "total": 1
}
```

## 🎯 Usage Examples

### Viewing User Data

1. **Navigate to Users page**: `http://localhost:3001/users`
2. **Enter admin password**: Use the password you set with the script
3. **Browse users**: See all registered users and their information
4. **Copy keys**: Click "Copy" buttons to copy keys to clipboard
5. **Toggle private keys**: Click "Show Private Keys" to view sensitive data

### Managing User Information

- **Copy Public Key**: Use for chatbot configuration
- **Copy Username**: For reference or chatbot setup
- **View Document Count**: See how active each user is
- **Check Creation Date**: Monitor user registration patterns

## 🔒 Security Best Practices

### Admin Password

- Use a strong, unique password
- Change the admin password regularly
- Don't share the admin password
- Store it securely

### Access Control

- Only access user data when necessary
- Log out when finished
- Don't leave the admin interface open
- Monitor for unauthorized access

### Key Management

- Private keys are encrypted and should remain secure
- Only show private keys when absolutely necessary
- Copy keys securely to trusted systems
- Don't share private keys

## 🚨 Important Notes

### Default Admin Password

The default admin password is `admin123`. **Change this immediately** in production:

```bash
node set-admin-password.js yourSecureProductionPassword
```

### Environment Variables

The admin password is stored in the `.env` file:

```env
ADMIN_PASSWORD=your_secure_password
```

### Production Considerations

- Use environment variables for admin password
- Implement proper admin role management
- Add audit logging for admin actions
- Consider implementing user deletion/management features
- Add rate limiting for admin endpoints

## 📊 User Statistics

The Users page provides summary statistics:

- **Total Users**: Number of registered users
- **Total Documents**: Combined document count across all users
- **Active Users**: Users with uploaded documents
- **Last Updated**: When the data was last refreshed

## 🔍 Troubleshooting

### Common Issues

1. **"Authentication required"**: Enter the correct admin password
2. **"Admin access required"**: Make sure you're using admin credentials
3. **"Failed to fetch users"**: Check server logs and database connection
4. **"Invalid admin password"**: Verify the password in your `.env` file

### Debug Steps

1. **Check admin password**:
   ```bash
   cat .env | grep ADMIN_PASSWORD
   ```

2. **Verify server is running**:
   ```bash
   curl http://localhost:3001/health
   ```

3. **Test admin login**:
   ```bash
   curl -X POST http://localhost:3001/api/auth/admin-login \
     -H "Content-Type: application/json" \
     -d '{"password":"your_admin_password"}'
   ```

4. **Check database connection**:
   ```bash
   npx prisma db push
   ```

## 📝 Files Modified

- `client/src/pages/UsersPage.tsx` - User management interface
- `client/src/App.tsx` - Added routing for Users page
- `client/src/components/Navbar.tsx` - Added Users page link
- `server/src/routes/auth.ts` - Admin authentication and user listing endpoints
- `server/set-admin-password.js` - Admin password management script

## 🎉 Benefits

- **Complete User Overview**: See all registered users at a glance
- **Key Management**: Easy access to public/private keys
- **Security**: Protected access with admin authentication
- **Statistics**: User activity and document counts
- **Audit Trail**: Track user creation and activity
- **Easy Setup**: Simple script-based admin password management 