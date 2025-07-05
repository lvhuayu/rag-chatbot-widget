import axios from 'axios';

export interface RAGDocument {
    url: string;
    title: string;
    content: string;
    user_id: string;
    timestamp?: string;
}

export interface RAGSearchRequest {
    query: string;
    top_k?: number;
    threshold?: number;
    user_id: string;
}

export interface RAGSearchResult {
    document: RAGDocument;
    similarity: number;
}

export interface RAGResponse {
    context?: string;
    documents: RAGSearchResult[];
}

export interface RAGStats {
    user_id: string;
    document_count: number;
    total_documents: number;
    unique_users?: number;
    embedding_model: string;
    vector_db: string;
    status: string;
    multi_tenant: boolean;
}

export interface RAGHealth {
    status: string;
    model: string;
    storage: string;
    database_info: {
        database_path: string;
        database_size_mb: number;
        total_documents: number;
        unique_users: number;
        embedding_dimension: number;
        storage_type: string;
    };
}

class RAGService {
    private baseUrl: string;

    constructor(baseUrl: string = 'http://localhost:8001') {
        this.baseUrl = baseUrl;
    }

    /**
     * Add a document to the RAG system
     */
    async addDocument(document: RAGDocument): Promise<{ success: boolean; doc_id?: string; message: string }> {
        try {
            const response = await axios.post(`${this.baseUrl}/add-document`, document, {
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000 // 30 second timeout
            });

            return {
                success: true,
                doc_id: response.data.doc_id,
                message: response.data.message
            };
        } catch (error: any) {
            console.error('Error adding document to RAG:', error.response?.data || error.message);
            return {
                success: false,
                message: error.response?.data?.detail || error.message
            };
        }
    }

    /**
     * Search documents for a specific user
     */
    async searchDocuments(request: RAGSearchRequest): Promise<RAGResponse> {
        try {
            const response = await axios.post(`${this.baseUrl}/search`, request, {
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000
            });

            return response.data;
        } catch (error: any) {
            console.error('Error searching RAG documents:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || error.message);
        }
    }

    /**
     * Get documents for a specific user
     */
    async getUserDocuments(userId: string): Promise<RAGDocument[]> {
        try {
            const response = await axios.get(`${this.baseUrl}/documents?user_id=${userId}`, {
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Error fetching user documents:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || error.message);
        }
    }

    /**
     * Get all documents (admin function)
     */
    async getAllDocuments(): Promise<RAGDocument[]> {
        try {
            const response = await axios.get(`${this.baseUrl}/documents`, {
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Error fetching all documents:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || error.message);
        }
    }

    /**
     * Get statistics for a specific user or overall
     */
    async getStats(userId?: string): Promise<RAGStats> {
        try {
            const url = userId 
                ? `${this.baseUrl}/stats?user_id=${userId}`
                : `${this.baseUrl}/stats`;
            
            const response = await axios.get(url, {
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Error fetching RAG stats:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || error.message);
        }
    }

    /**
     * Get system health information
     */
    async getHealth(): Promise<RAGHealth> {
        try {
            const response = await axios.get(`${this.baseUrl}/health`, {
                timeout: 5000
            });

            return response.data;
        } catch (error: any) {
            console.error('Error fetching RAG health:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || error.message);
        }
    }

    /**
     * Delete documents for a specific user
     */
    async deleteUserDocuments(userId: string): Promise<{ success: boolean; message: string }> {
        try {
            // Note: This would require implementing a delete endpoint in the RAG backend
            // For now, we'll return a not implemented message
            return {
                success: false,
                message: 'Delete functionality not yet implemented in RAG backend'
            };
        } catch (error: any) {
            console.error('Error deleting user documents:', error.response?.data || error.message);
            return {
                success: false,
                message: error.response?.data?.detail || error.message
            };
        }
    }

    /**
     * Check if RAG backend is available
     */
    async isAvailable(): Promise<boolean> {
        try {
            await this.getHealth();
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Get user-specific document count
     */
    async getUserDocumentCount(userId: string): Promise<number> {
        try {
            const stats = await this.getStats(userId);
            return stats.document_count;
        } catch (error) {
            console.error('Error getting user document count:', error);
            return 0;
        }
    }

    /**
     * Get total system document count
     */
    async getTotalDocumentCount(): Promise<number> {
        try {
            const stats = await this.getStats();
            return stats.total_documents;
        } catch (error) {
            console.error('Error getting total document count:', error);
            return 0;
        }
    }
}

export default RAGService; 