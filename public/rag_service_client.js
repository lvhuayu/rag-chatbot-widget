// RAG Service Client - Communicates with Python Backend

export class RAGServiceClient {
    constructor(backendUrl = 'https://essayformatter.com:8001') {
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
            const response = await fetch(`${this.backendUrl}/health`);
            if (!response.ok) {
                throw new Error(`Backend not available: ${response.status}`);
            }
            this.isInitialized = true;
            return true;
        } catch (error) {
            throw new Error('Failed to connect to Python backend: ' + error.message);
        }
    }

    async ingestDocument(doc) {
        const response = await fetch(`${this.backendUrl}/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(doc)
        });
        if (!response.ok) {
            throw new Error('Failed to ingest document');
        }
        return await response.json();
    }

    async query(query, top_k = 3) {
        const response = await fetch(`${this.backendUrl}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k })
        });
        if (!response.ok) {
            throw new Error('Failed to query backend');
        }
        return await response.json();
    }

    async addDocument(document) {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            const response = await fetch(`${this.backendUrl}/add-documents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(document)
            });

            if (!response.ok) {
                throw new Error(`Failed to add document: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ Document added to RAG backend:', result);
            return result;

        } catch (error) {
            console.error('❌ Error adding document to RAG backend:', error);
            throw error;
        }
    }

    async search(query, topK = 3) {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            const response = await fetch(`${this.backendUrl}/rag-generate`, {
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
                throw new Error(`RAG generate failed: ${response.status}`);
            }

            const results = await response.json();
            console.log('✅ RAG generate results:', results);
            return results;

        } catch (error) {
            console.error('❌ Error generating with RAG backend:', error);
            throw error;
        }
    }

    async getDocuments() {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            const response = await fetch(`${this.backendUrl}/documents`);
            if (!response.ok) {
                throw new Error(`Failed to get documents: ${response.status}`);
            }

            const documents = await response.json();
            return documents;

        } catch (error) {
            console.error('❌ Error getting documents from RAG backend:', error);
            throw error;
        }
    }

    async clearDocuments() {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            const response = await fetch(`${this.backendUrl}/documents`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Failed to clear documents: ${response.status}`);
            }

            console.log('✅ Documents cleared from RAG backend');
            return true;

        } catch (error) {
            console.error('❌ Error clearing documents from RAG backend:', error);
            throw error;
        }
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            backendUrl: this.backendUrl
        };
    }
}
