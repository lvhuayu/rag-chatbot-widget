#!/usr/bin/env node

/**
 * Script to set admin password for user management
 * Usage: node set-admin-password.js <password>
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);

if (args.length === 0) {
    console.log('❌ Please provide an admin password');
    console.log('Usage: node set-admin-password.js <password>');
    console.log('');
    console.log('Example: node set-admin-password.js mySecurePassword123');
    process.exit(1);
}

const password = args[0];

if (password.length < 6) {
    console.log('❌ Password must be at least 6 characters long');
    process.exit(1);
}

// Create .env file if it doesn't exist
const envPath = path.join(__dirname, '.env');
let envContent = '';

if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, 'utf8');
}

// Check if ADMIN_PASSWORD already exists
if (envContent.includes('ADMIN_PASSWORD=')) {
    // Update existing ADMIN_PASSWORD
    envContent = envContent.replace(/ADMIN_PASSWORD=.*/g, `ADMIN_PASSWORD=${password}`);
} else {
    // Add new ADMIN_PASSWORD
    envContent += `\nADMIN_PASSWORD=${password}`;
}

// Write back to .env file
fs.writeFileSync(envPath, envContent.trim() + '\n');

console.log('✅ Admin password set successfully!');
console.log('');
console.log('🔐 Admin password:', password);
console.log('');
console.log('📝 You can now access the Users page at: http://localhost:3001/users');
console.log('🔑 Use this password to authenticate as admin');
console.log('');
console.log('⚠️  Remember to restart the server for changes to take effect'); 