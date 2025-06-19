(function() {
    'use strict';
    
    // Global RAG service instance
    let ragService = null;
    let contentIngestionPerformed = false;
    
    // Global function to initialize the chatbot
    window.initRAGChatbot = async function(config) {
        // Default configuration
        const defaultConfig = {
            selector: null,
            theme: {
                primaryColor: '#007bff'
            },
            welcomeMessage: 'Hello! I\'m your AI assistant with RAG capabilities. How can I help you today?',
            promptTypeId: 'default',
            enableContentIngestion: false,
            ingestEndpoint: 'https://yourdomain.com/api/ingest',
            enableRAG: true,
            ragThreshold: 0.7, // Minimum similarity threshold for RAG results
            maxRAGResults: 3   // Maximum number of RAG results to include
        };
        
        // Merge user config with defaults
        const finalConfig = Object.assign({}, defaultConfig, config);
        
        // Initialize RAG service if enabled
        if (finalConfig.enableRAG) {
            try {
                ragService = new RAGService();
                await ragService.initialize();
                console.log('✅ RAG service initialized successfully');
            } catch (error) {
                console.error('❌ Failed to initialize RAG service:', error);
                finalConfig.enableRAG = false;
            }
        }
        
        // Handle content ingestion if enabled and not already performed
        if (finalConfig.enableContentIngestion && !contentIngestionPerformed) {
            await performContentIngestion(finalConfig);
            contentIngestionPerformed = true;
        }
        
        // Create iframe element
        const iframe = document.createElement('iframe');
        iframe.id = 'rag-chatbot-iframe';
        iframe.src = './chat-ui.html';
        iframe.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            background: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        
        // If selector is provided, attach to that element instead
        if (finalConfig.selector) {
            const targetElement = document.querySelector(finalConfig.selector);
            if (targetElement) {
                targetElement.appendChild(iframe);
                iframe.style.position = 'relative';
                iframe.style.bottom = 'auto';
                iframe.style.right = 'auto';
            }
        }
        
        // Send config to iframe when it loads
        iframe.onload = function() {
            iframe.contentWindow.postMessage({
                type: 'CHATBOT_CONFIG',
                config: finalConfig
            }, '*');
        };
        
        // Add iframe to page
        document.body.appendChild(iframe);
        
        // Return iframe reference for potential future use
        return iframe;
    };
    
    /**
     * Extract visible text content from the page body
     * @returns {string} Clean text content
     */
    function extractVisibleContent() {
        // Clone the body to avoid modifying the original DOM
        const bodyClone = document.body.cloneNode(true);
        
        // Remove script and style elements
        const scripts = bodyClone.querySelectorAll('script, style, noscript, iframe, img, svg, canvas, video, audio');
        scripts.forEach(el => el.remove());
        
        // Get text content and clean it up
        let content = bodyClone.textContent || bodyClone.innerText || '';
        
        // Clean up whitespace
        content = content
            .replace(/\s+/g, ' ')  // Replace multiple whitespace with single space
            .replace(/\n+/g, ' ')  // Replace newlines with spaces
            .trim();               // Remove leading/trailing whitespace
        
        return content;
    }
    
    /**
     * Perform content ingestion with RAG capabilities
     * @param {Object} config - The chatbot configuration
     */
    async function performContentIngestion(config) {
        try {
            // Extract page content
            const pageContent = extractVisibleContent();
            const title = document.title || '';
            const url = window.location.href;
            const timestamp = new Date().toISOString();
            
            // Truncate content to 5000 characters
            const truncatedContent = pageContent.length > 5000 
                ? pageContent.substring(0, 5000) + '...'
                : pageContent;
            
            // Prepare the document for RAG
            const document = {
                url: url,
                title: title,
                content: truncatedContent,
                timestamp: timestamp
            };
            
            // Add to RAG service if enabled
            if (config.enableRAG && ragService) {
                await ragService.addDocument(document);
                console.log('✅ Page content added to RAG vector database');
            }
            
            // Also send to external ingest endpoint if specified
            if (config.ingestEndpoint && config.ingestEndpoint !== 'https://yourdomain.com/api/ingest') {
                const payload = {
                    url: url,
                    title: title,
                    content: truncatedContent,
                    timestamp: timestamp
                };
                
                fetch(config.ingestEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => {
                    if (response.ok) {
                        console.log('✅ Content sent to external ingest endpoint');
                    } else {
                        console.warn('⚠️ External ingestion failed with status:', response.status);
                    }
                })
                .catch(error => {
                    console.warn('⚠️ External ingestion failed:', error.message);
                });
            }
            
        } catch (error) {
            console.error('❌ Error during content ingestion:', error);
        }
    }
    
    /**
     * Search for relevant context using RAG
     * @param {string} query - The user's question
     * @param {Object} config - The chatbot configuration
     * @returns {Array} Relevant documents with similarity scores
     */
    async function searchRAGContext(query, config) {
        if (!config.enableRAG || !ragService) {
            return [];
        }
        
        try {
            const results = await ragService.searchDocuments(query, config.maxRAGResults);
            
            // Filter by similarity threshold
            const relevantResults = results.filter(result => 
                result.similarity >= config.ragThreshold
            );
            
            return relevantResults;
            
        } catch (error) {
            console.error('❌ Error searching RAG context:', error);
            return [];
        }
    }
    
    /**
     * Build enhanced prompt with RAG context
     * @param {string} userMessage - The user's message
     * @param {Array} ragResults - Relevant documents from RAG search
     * @returns {string} Enhanced prompt with context
     */
    function buildRAGPrompt(userMessage, ragResults) {
        if (!ragResults || ragResults.length === 0) {
            return userMessage;
        }
        
        let context = 'Based on the following relevant information:\n\n';
        
        ragResults.forEach((result, index) => {
            context += `Source ${index + 1} (${result.title}):\n`;
            context += `${result.content}\n\n`;
        });
        
        context += `Please answer the following question using the information above: ${userMessage}`;
        
        return context;
    }
    
    // Expose RAG functions globally for the chat UI to use
    window.RAGChatbotAPI = {
        searchContext: searchRAGContext,
        buildPrompt: buildRAGPrompt,
        getRAGStats: () => ragService ? ragService.getStats() : null,
        clearRAGDocuments: () => ragService ? ragService.clearDocuments() : null
    };
    
    // Add some basic styles to prevent conflicts
    const style = document.createElement('style');
    style.textContent = `
        #rag-chatbot-iframe {
            transition: all 0.3s ease;
        }
        #rag-chatbot-iframe:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
        }
    `;
    document.head.appendChild(style);
    
})(); 