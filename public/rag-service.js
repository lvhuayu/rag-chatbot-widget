/**
 * RAG Service - Handles embeddings, vector storage, and retrieval
 * Uses local transformers for embeddings and HNSW for vector search
 */

class RAGService {
    constructor() {
        this.embeddingPipeline = null;
        this.vectorDB = null;
        this.documents = [];
        this.isInitialized = false;
        this.embeddingDimension = 384; // Default for sentence-transformers/all-MiniLM-L6-v2
    }

    /**
     * Initialize the RAG service with embedding model
     */
    async initialize() {
        try {
            console.log('🚀 Initializing RAG service...');
            
            // Load embedding pipeline
            const { pipeline } = await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.15.0/dist/transformers.min.js');
            this.embeddingPipeline = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
            
            // Initialize vector database
            await this.initializeVectorDB();
            
            this.isInitialized = true;
            console.log('✅ RAG service initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize RAG service:', error);
            throw error;
        }
    }

    /**
     * Initialize local vector database using HNSW
     */
    async initializeVectorDB() {
        try {
            // For now, we'll use a simple in-memory vector store
            // In production, you'd use a proper vector DB like Chroma, Pinecone, or Weaviate
            this.vectorDB = {
                vectors: [],
                documents: [],
                add: (vector, document) => {
                    this.vectorDB.vectors.push(vector);
                    this.vectorDB.documents.push(document);
                },
                search: (queryVector, k = 5) => {
                    const similarities = this.vectorDB.vectors.map((vector, index) => ({
                        index,
                        similarity: this.cosineSimilarity(queryVector, vector),
                        document: this.vectorDB.documents[index]
                    }));
                    
                    return similarities
                        .sort((a, b) => b.similarity - a.similarity)
                        .slice(0, k);
                }
            };
            
            console.log('✅ Vector database initialized');
            
        } catch (error) {
            console.error('❌ Failed to initialize vector database:', error);
            throw error;
        }
    }

    /**
     * Generate embeddings for text
     */
    async generateEmbedding(text) {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            const result = await this.embeddingPipeline(text, {
                pooling: 'mean',
                normalize: true
            });
            
            return Array.from(result.data);
        } catch (error) {
            console.error('❌ Failed to generate embedding:', error);
            throw error;
        }
    }

    /**
     * Add document to vector database
     */
    async addDocument(document) {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            // Generate embedding for the document content
            const embedding = await this.generateEmbedding(document.content);
            
            // Add to vector database
            this.vectorDB.add(embedding, document);
            
            // Store document metadata
            this.documents.push({
                id: document.id || Date.now().toString(),
                url: document.url,
                title: document.title,
                content: document.content,
                timestamp: document.timestamp,
                embedding: embedding
            });
            
            console.log(`✅ Document added to RAG: ${document.title}`);
            
        } catch (error) {
            console.error('❌ Failed to add document:', error);
            throw error;
        }
    }

    /**
     * Search for relevant documents
     */
    async searchDocuments(query, k = 5) {
        if (!this.isInitialized) {
            throw new Error('RAG service not initialized');
        }

        try {
            // Generate embedding for the query
            const queryEmbedding = await this.generateEmbedding(query);
            
            // Search vector database
            const results = this.vectorDB.search(queryEmbedding, k);
            
            console.log(`🔍 Found ${results.length} relevant documents for: "${query}"`);
            
            return results.map(result => ({
                ...result.document,
                similarity: result.similarity
            }));
            
        } catch (error) {
            console.error('❌ Failed to search documents:', error);
            throw error;
        }
    }

    /**
     * Calculate cosine similarity between two vectors
     */
    cosineSimilarity(vectorA, vectorB) {
        if (vectorA.length !== vectorB.length) {
            throw new Error('Vectors must have the same dimension');
        }
        
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;
        
        for (let i = 0; i < vectorA.length; i++) {
            dotProduct += vectorA[i] * vectorB[i];
            normA += vectorA[i] * vectorA[i];
            normB += vectorB[i] * vectorB[i];
        }
        
        normA = Math.sqrt(normA);
        normB = Math.sqrt(normB);
        
        if (normA === 0 || normB === 0) {
            return 0;
        }
        
        return dotProduct / (normA * normB);
    }

    /**
     * Get statistics about the RAG system
     */
    getStats() {
        return {
            isInitialized: this.isInitialized,
            documentCount: this.documents.length,
            embeddingDimension: this.embeddingDimension,
            documents: this.documents.map(doc => ({
                id: doc.id,
                title: doc.title,
                url: doc.url,
                timestamp: doc.timestamp
            }))
        };
    }

    /**
     * Clear all documents from the vector database
     */
    clearDocuments() {
        this.vectorDB.vectors = [];
        this.vectorDB.documents = [];
        this.documents = [];
        console.log('🗑️ All documents cleared from RAG');
    }
}

// Export for use in other modules
window.RAGService = RAGService; 