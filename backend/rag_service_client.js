// RAG Service Client - Communicates with Python Backend
class RAGServiceClient {
    constructor(backendUrl = 'http://localhost:8000') {
        this.backendUrl = backendUrl;
        this.isInitialized = false;
        this.initPromise = null;
    }

    async initialize() {
        if (this.initPromise) return this.initPromise;
        
        this.initPromise = this._initialize();
        return this.initPromise;
    }

    async _initialize() {
        try {
            console.log('Initializing RAG service client...');
            
            // Test connection to backend
            const response = await fetch(`${this.backendUrl}/health`);
            if (!response.ok) {
                throw new Error(`Backend not available: ${response.status}`);
            }
            
            const health = await response.json();
            console.log('Backend health check:', health);
            
            this.isInitialized = true;
            console.log('RAG service client initialized successfully');
        } catch (error) {
            console.error('Failed to initialize RAG service client:', error);
            throw error;
        }
    }

    async addDocument(document) {
        await this.initialize();
        
        try {
            const response = await fetch(`${this.backendUrl}/add-documents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: document.url,
                    title: document.title,
                    content: document.content,
                    timestamp: document.timestamp || new Date().toISOString()
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to add document: ${response.status}`);
            }

            const result = await response.json();
            console.log(`Document added to RAG backend: ${document.title}`);
            return result.doc_id;
        } catch (error) {
            console.error('Error adding document to RAG backend:', error);
            throw error;
        }
    }

    async search(query, topK = 3) {
        await this.initialize();
        
        try {
            const response = await fetch(`${this.backendUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: topK
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to search: ${response.status}`);
            }

            const result = await response.json();
            
            // Convert backend format to frontend format
            return result.documents.map(item => ({
                document: {
                    id: item.document.url, // Use URL as ID for now
                    url: item.document.url,
                    title: item.document.title,
                    content: item.document.content,
                    timestamp: item.document.timestamp
                },
                similarity: item.similarity
            }));
        } catch (error) {
            console.error('Error searching RAG backend:', error);
            return [];
        }
    }

    async getContext(query, maxLength = 2000) {
        try {
            const response = await fetch(`${this.backendUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 3
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to get context: ${response.status}`);
            }

            const result = await response.json();
            
            if (!result.context) {
                return null;
            }

            // Truncate context if needed
            if (result.context.length > maxLength) {
                return result.context.substring(0, maxLength) + '...';
            }

            return result.context;
        } catch (error) {
            console.error('Error getting context from RAG backend:', error);
            return null;
        }
    }

    async getDocumentCount() {
        try {
            const response = await fetch(`${this.backendUrl}/stats`);
            if (!response.ok) {
                throw new Error(`Failed to get stats: ${response.status}`);
            }

            const stats = await response.json();
            return stats.document_count;
        } catch (error) {
            console.error('Error getting document count:', error);
            return 0;
        }
    }

    async getAllDocuments() {
        try {
            const response = await fetch(`${this.backendUrl}/documents`);
            if (!response.ok) {
                throw new Error(`Failed to get documents: ${response.status}`);
            }

            const documents = await response.json();
            return documents.map(doc => ({
                id: doc.url,
                url: doc.url,
                title: doc.title,
                content: doc.content,
                timestamp: doc.timestamp
            }));
        } catch (error) {
            console.error('Error getting documents:', error);
            return [];
        }
    }

    async getStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/stats`);
            if (!response.ok) {
                throw new Error(`Failed to get stats: ${response.status}`);
            }

            const stats = await response.json();
            return {
                isInitialized: this.isInitialized,
                documentCount: stats.document_count,
                embeddingModel: stats.embedding_model,
                vectorDB: stats.vector_db,
                backendUrl: this.backendUrl
            };
        } catch (error) {
            console.error('Error getting status:', error);
            return {
                isInitialized: this.isInitialized,
                documentCount: 0,
                embeddingModel: 'Unknown',
                vectorDB: 'Unknown',
                backendUrl: this.backendUrl,
                error: error.message
            };
        }
    }

    async clearDocuments() {
        try {
            const response = await fetch(`${this.backendUrl}/clear-documents`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Failed to clear documents: ${response.status}`);
            }

            const result = await response.json();
            console.log('RAG backend documents cleared');
            return result;
        } catch (error) {
            console.error('Error clearing documents:', error);
            throw error;
        }
    }
}

// Global RAG service client instance
window.RAGService = new RAGServiceClient(); 