import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface User {
    id: string;
    username: string;
    publicKey: string;
    privateKey: string;
    createdAt: string;
    documentCount: number;
}

const UsersPage = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showPrivateKeys, setShowPrivateKeys] = useState(false);
    const [adminPassword, setAdminPassword] = useState('');
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        // Check if user is already authenticated
        const token = localStorage.getItem('token');
        if (token) {
            fetchUsers();
        }
    }, []);

    const handleAdminAuth = async () => {
        if (!adminPassword) {
            setError('Please enter admin password');
            return;
        }

        try {
            const response = await axios.post('/api/auth/admin-login', { password: adminPassword });
            localStorage.setItem('adminToken', response.data.token);
            setIsAuthenticated(true);
            fetchUsers();
        } catch (err: any) {
            setError(err.response?.data?.message || 'Admin authentication failed');
        }
    };

    const fetchUsers = async () => {
        try {
            setIsLoading(true);
            setError(null);
            
            const token = localStorage.getItem('adminToken') || localStorage.getItem('token');
            const response = await axios.get('/api/auth/admin/users', {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            
            setUsers(response.data.users);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to fetch users');
        } finally {
            setIsLoading(false);
        }
    };

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        // You could add a toast notification here
        console.log(`${label} copied to clipboard`);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    const truncateText = (text: string, maxLength: number = 50) => {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    };

    if (!isAuthenticated && !localStorage.getItem('token')) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 flex items-center justify-center p-4">
                <div className="w-full max-w-md">
                    <div className="bg-white rounded-lg shadow-xl p-6">
                        <div className="text-center mb-6">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-600 rounded-full mb-4">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                            </div>
                            <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin Access Required</h1>
                            <p className="text-gray-600">Enter admin password to view user information</p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    Admin Password
                                </label>
                                <input
                                    type="password"
                                    value={adminPassword}
                                    onChange={(e) => setAdminPassword(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200"
                                    placeholder="Enter admin password"
                                    onKeyPress={(e) => e.key === 'Enter' && handleAdminAuth()}
                                />
                            </div>

                            {error && (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                    <div className="flex">
                                        <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <p className="ml-3 text-sm text-red-700">{error}</p>
                                    </div>
                                </div>
                            )}

                            <button
                                onClick={handleAdminAuth}
                                className="w-full bg-red-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200"
                            >
                                Access User Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-xl p-6 mb-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 mb-2">👥 User Management</h1>
                            <p className="text-gray-600">View and manage registered users and their keys</p>
                        </div>
                        <div className="flex space-x-3">
                            <button
                                onClick={() => setShowPrivateKeys(!showPrivateKeys)}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                    showPrivateKeys 
                                        ? 'bg-red-600 text-white hover:bg-red-700' 
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                            >
                                {showPrivateKeys ? 'Hide' : 'Show'} Private Keys
                            </button>
                            <button
                                onClick={fetchUsers}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Refresh
                            </button>
                        </div>
                    </div>
                </div>

                {/* Users List */}
                <div className="bg-white rounded-lg shadow-xl overflow-hidden">
                    {isLoading ? (
                        <div className="p-8 text-center">
                            <div className="inline-flex items-center">
                                <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span className="text-lg text-gray-600">Loading users...</span>
                            </div>
                        </div>
                    ) : error ? (
                        <div className="p-8 text-center">
                            <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-md mx-auto">
                                <div className="flex">
                                    <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <p className="ml-3 text-sm text-red-700">{error}</p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Public Key</th>
                                        {showPrivateKeys && (
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Private Key</th>
                                        )}
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Documents</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {users.map((user) => (
                                        <tr key={user.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div className="flex-shrink-0 h-10 w-10">
                                                        <div className="h-10 w-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                                                            <span className="text-white font-semibold text-sm">
                                                                {user.username.charAt(0).toUpperCase()}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="ml-4">
                                                        <div className="text-sm font-medium text-gray-900">{user.username}</div>
                                                        <div className="text-sm text-gray-500">ID: {user.id}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="max-w-xs">
                                                    <div className="text-sm text-gray-900 font-mono bg-gray-100 p-2 rounded border">
                                                        {truncateText(user.publicKey, 80)}
                                                    </div>
                                                    <button
                                                        onClick={() => copyToClipboard(user.publicKey, 'Public key')}
                                                        className="mt-1 text-xs text-blue-600 hover:text-blue-800"
                                                    >
                                                        Copy full key
                                                    </button>
                                                </div>
                                            </td>
                                            {showPrivateKeys && (
                                                <td className="px-6 py-4">
                                                    <div className="max-w-xs">
                                                        <div className="text-sm text-gray-900 font-mono bg-red-50 p-2 rounded border border-red-200">
                                                            {truncateText(user.privateKey, 80)}
                                                        </div>
                                                        <button
                                                            onClick={() => copyToClipboard(user.privateKey, 'Private key')}
                                                            className="mt-1 text-xs text-red-600 hover:text-red-800"
                                                        >
                                                            Copy full key
                                                        </button>
                                                    </div>
                                                </td>
                                            )}
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                    {user.documentCount} documents
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {formatDate(user.createdAt)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                <button
                                                    onClick={() => copyToClipboard(user.username, 'Username')}
                                                    className="text-blue-600 hover:text-blue-900 mr-3"
                                                >
                                                    Copy username
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Summary */}
                {users.length > 0 && (
                    <div className="mt-6 bg-white rounded-lg shadow-xl p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Summary</h3>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-blue-600">{users.length}</div>
                                <div className="text-sm text-blue-600">Total Users</div>
                            </div>
                            <div className="bg-green-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-green-600">
                                    {users.reduce((sum, user) => sum + user.documentCount, 0)}
                                </div>
                                <div className="text-sm text-green-600">Total Documents</div>
                            </div>
                            <div className="bg-purple-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-purple-600">
                                    {users.filter(user => user.documentCount > 0).length}
                                </div>
                                <div className="text-sm text-purple-600">Active Users</div>
                            </div>
                            <div className="bg-orange-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-orange-600">
                                    {new Date().toLocaleDateString()}
                                </div>
                                <div className="text-sm text-orange-600">Last Updated</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UsersPage; 