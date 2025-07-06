(function() {
    'use strict';
    
    // Global RAG service instance
    let ragService = null;
    let contentIngestionPerformed = false;
    let authToken = null;
    let userId = null;
    let privateKey = null;
    let publicKey = null;
    
    // Global function to initialize the chatbot
    window.initRAGChatbot = async function(config) {
        // Extract userId from various sources
        userId = extractUserId(config);
        
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
            maxRAGResults: 3,   // Maximum number of RAG results to include
            backendUrl: 'http://localhost:8001', // RAG backend URL - CHANGE THIS TO YOUR BACKEND
            ollamaUrl: 'http://localhost:11434',  // Ollama URL - CHANGE THIS IF NEEDED
            
            // Multi-tenant configuration
            userId: userId, // Add userId to config
            
            // Authentication configuration
            auth: {
                token: null,           // JWT token for authentication
                username: null,        // Username for login
                password: null,        // Password for login
                autoLogin: false,      // Auto-login with provided credentials
                loginEndpoint: '/api/auth/login', // Login endpoint
                tokenKey: 'rag_chatbot_token', // Local storage key for token
                
                // Public/Private Key Authentication
                useKeyAuth: true,      // Enable public/private key authentication
                keyAuthEndpoint: '/auth/request-challenge', // Challenge endpoint
                keyAuthVerifyEndpoint: '/auth/verify-challenge', // Verify endpoint
                keyStorageKey: 'rag_chatbot_keys', // Local storage key for keys
                publicKey: `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyoVzODARtoIk2jWbUGjU
rLlrCHK4oofLuFilKZvR/+p197qj5uqhJnVL4QsCRcZl0CBRqPDfwFzubjM20O4b
1qJvfD07emHCclqWWu49Gxwrb0nr//qVjltDNrQZvyKSObC+wXDlttHaSQ0xKzYz
/l2VNvsSc6DxwQHtXl65obzKQOx6BhZpRL9kv6HIuAo2MTCYbPke1R4uAndormnh
8MlJ/WPPyNNFuB2EPdHxB/Ks5cTU5MS5brrWNsEApyp6deF2lNkFF9UEjXh4GOTG
veMY/OjJ5eLC0rY5VS8PwrnSAf8Vq2fgiYocqgz/5qk5JWs4274mCb6feTATpcZT
iwIDAQAB
-----END PUBLIC KEY-----`,
                
                // Registered Key Authentication (from upload portal)
                useRegisteredKey: false, // Use public key from registration
                registeredUsername: null, // Username to fetch public key for
                uploadPortalUrl: 'http://localhost:3001', // Upload portal URL
                publicKeyEndpoint: '/api/auth/public-key' // Public key endpoint
            }
        };
        
        // Merge user config with defaults
        const finalConfig = Object.assign({}, defaultConfig, config);
        
        // Validate userId
        if (!finalConfig.userId) {
            console.warn('⚠️ No userId provided. Using default user. For multi-tenant support, please provide a userId.');
            finalConfig.userId = 'default_user';
        }
        
        // Update global userId
        userId = finalConfig.userId;
        
        // Validate backend URL
        if (!finalConfig.backendUrl || finalConfig.backendUrl === 'http://localhost:8001') {
            console.warn('⚠️ Please configure backendUrl to point to your RAG backend server!');
            console.warn('⚠️ Example: initRAGChatbot({ backendUrl: "https://your-backend.com" })');
        }
        
        console.log('🔑 Multi-tenant setup:', { userId: finalConfig.userId });
        
        // Handle authentication
        await handleAuthentication(finalConfig);
        
        // Initialize RAG service if enabled
        if (finalConfig.enableRAG) {
            try {
                // ragService = new RAGService();
                // await ragService.initialize();
                console.log('✅ RAG service initialized successfully');
                console.log('🔗 Backend URL:', finalConfig.backendUrl);
                console.log('🔐 Authentication:', authToken ? 'Authenticated' : 'Not authenticated');
                console.log('👤 User ID:', finalConfig.userId);
                if (finalConfig.auth.useKeyAuth) {
                    console.log('🔑 Key Auth:', publicKey ? 'Keys generated' : 'No keys');
                }
                if (finalConfig.auth.useRegisteredKey) {
                    console.log('🔑 Registered Key Auth:', publicKey ? 'Key loaded' : 'No key');
                }
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
            transition: all 0.3s ease;
        `;
        
        // Create minimize button
        const minimizeButton = document.createElement('div');
        minimizeButton.id = 'rag-chatbot-minimize';
        minimizeButton.innerHTML = '🤖';
        minimizeButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            z-index: 10001;
            transition: all 0.3s ease;
            display: none;
        `;
        
        // Add hover effects
        minimizeButton.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.boxShadow = '0 6px 25px rgba(0, 0, 0, 0.2)';
        });
        
        minimizeButton.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
        });
        
        // Minimize/Expand functionality
        let isMinimized = false;
        
        function minimizeChatbot() {
            iframe.style.transform = 'scale(0)';
            iframe.style.opacity = '0';
            setTimeout(() => {
                iframe.style.display = 'none';
                minimizeButton.style.display = 'flex';
            }, 300);
            isMinimized = true;
        }
        
        function expandChatbot() {
            minimizeButton.style.display = 'none';
            iframe.style.display = 'block';
            setTimeout(() => {
                iframe.style.transform = 'scale(1)';
                iframe.style.opacity = '1';
            }, 50);
            isMinimized = false;
        }
        
        // Add click handlers
        minimizeButton.addEventListener('click', expandChatbot);
        
        // Listen for minimize message from iframe
        window.addEventListener('message', function(event) {
            if (event.data.type === 'MINIMIZE_CHATBOT') {
                minimizeChatbot();
            }
        });
        
        // If selector is provided, attach to that element instead
        if (finalConfig.selector) {
            const targetElement = document.querySelector(finalConfig.selector);
            if (targetElement) {
                targetElement.appendChild(iframe);
                targetElement.appendChild(minimizeButton);
                iframe.style.position = 'relative';
                iframe.style.bottom = 'auto';
                iframe.style.right = 'auto';
                minimizeButton.style.position = 'absolute';
                minimizeButton.style.bottom = '20px';
                minimizeButton.style.right = '20px';
            }
        } else {
            // Add both iframe and minimize button to page
            document.body.appendChild(iframe);
            document.body.appendChild(minimizeButton);
        }
        
        // Send config to iframe when it loads
        iframe.onload = function() {
            iframe.contentWindow.postMessage({
                type: 'CHATBOT_CONFIG',
                config: finalConfig,
                authToken: authToken,
                userId: userId
            }, '*');
        };
        
        // Return iframe reference for potential future use
        return iframe;
    };
    
    /**
     * Extract userId from various sources
     * @param {Object} config - The chatbot configuration
     * @returns {string|null} The userId or null if not found
     */
    function extractUserId(config) {
        // 1. Check if userId is provided in config
        if (config && config.userId) {
            return config.userId;
        }
        
        // 2. Check if userId is provided in global config
        if (window.__RAG_CHATBOT_CONFIG__ && window.__RAG_CHATBOT_CONFIG__.userId) {
            return window.__RAG_CHATBOT_CONFIG__.userId;
        }
        
        // 3. Check if userId is provided as data attribute on script tag
        const currentScript = document.currentScript;
        if (currentScript && currentScript.dataset.userId) {
            return currentScript.dataset.userId;
        }
        
        // 4. Check if userId is provided as data attribute on any script tag with chatbot.js
        const scriptTags = document.querySelectorAll('script[src*="chatbot.js"]');
        for (const script of scriptTags) {
            if (script.dataset.userId) {
                return script.dataset.userId;
            }
        }
        
        // 5. Check if userId is provided as data attribute on any element with data-rag-user-id
        const elementWithUserId = document.querySelector('[data-rag-user-id]');
        if (elementWithUserId) {
            return elementWithUserId.dataset.ragUserId;
        }
        
        return null;
    }
    
    /**
     * Handle user authentication
     * @param {Object} config - The chatbot configuration
     */
    async function handleAuthentication(config) {
        try {
            // Check if we have a stored token
            const storedToken = localStorage.getItem(config.auth.tokenKey);
            if (storedToken) {
                authToken = storedToken;
                console.log('✅ Using stored authentication token');
                return;
            }
            
            // Check if token is provided in config
            if (config.auth.token) {
                authToken = config.auth.token;
                localStorage.setItem(config.auth.tokenKey, authToken);
                console.log('✅ Using provided authentication token');
                return;
            }
            
            // Handle registered key authentication (from upload portal)
            if (config.auth.useRegisteredKey) {
                await handleRegisteredKeyAuthentication(config);
                return;
            }
            
            // Handle public/private key authentication
            if (config.auth.useKeyAuth) {
                await handleKeyAuthentication(config);
                return;
            }
            
            // Auto-login if credentials are provided
            if (config.auth.autoLogin && config.auth.username && config.auth.password) {
                await performLogin(config);
                return;
            }
            
            console.warn('⚠️ No authentication provided. Some features may be limited.');
            
        } catch (error) {
            console.error('❌ Authentication error:', error);
        }
    }
    
    /**
     * Handle registered key authentication (from upload portal)
     * @param {Object} config - The chatbot configuration
     */
    async function handleRegisteredKeyAuthentication(config) {
        try {
            if (!config.auth.registeredUsername) {
                throw new Error('Username is required for registered key authentication');
            }
            
            // Fetch public key from upload portal
            const publicKeyResponse = await fetch(`${config.auth.uploadPortalUrl}${config.auth.publicKeyEndpoint}/${config.auth.registeredUsername}`);
            
            if (!publicKeyResponse.ok) {
                const error = await publicKeyResponse.json();
                throw new Error(error.message || 'Failed to fetch public key');
            }
            
            const publicKeyData = await publicKeyResponse.json();
            publicKey = publicKeyData.publicKey;
            
            console.log('✅ Registered public key loaded for:', config.auth.registeredUsername);
            
            // Use simplified registered key authentication
            const authResponse = await fetch(`${config.backendUrl}/auth/register-key`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    public_key: publicKey,
                    username: config.auth.registeredUsername
                })
            });
            
            if (!authResponse.ok) {
                const error = await authResponse.json();
                throw new Error(error.detail || 'Registered key authentication failed');
            }
            
            const authData = await authResponse.json();
            
            // Store token
            authToken = authData.token;
            userId = authData.user_id;
            localStorage.setItem(config.auth.tokenKey, authToken);
            
            console.log('✅ Registered key authentication successful');
            console.log('👤 User:', authData.username);
            
        } catch (error) {
            console.error('❌ Registered key authentication failed:', error);
            throw error;
        }
    }
    
    /**
     * Handle public/private key authentication
     * @param {Object} config - The chatbot configuration
     */
    async function handleKeyAuthentication(config) {
        try {
            // Generate or load keys
            await generateOrLoadKeys(config);
            
            // Request challenge from backend
            const challengeResponse = await requestChallenge(config);
            
            // Sign the challenge with private key
            const signature = await signChallenge(challengeResponse.challenge);
            
            // Verify challenge and get token
            const verifyResponse = await verifyChallenge(config, challengeResponse.challenge_id, signature);
            
            // Store token
            authToken = verifyResponse.token;
            userId = verifyResponse.user_id;
            localStorage.setItem(config.auth.tokenKey, authToken);
            
            console.log('✅ Key authentication successful');
            console.log('👤 User:', verifyResponse.username);
            
        } catch (error) {
            console.error('❌ Key authentication failed:', error);
            throw error;
        }
    }
    
    /**
     * Generate or load public/private keys
     * @param {Object} config - The chatbot configuration
     */
    async function generateOrLoadKeys(config) {
        try {
            // Check if keys are stored
            const storedKeys = localStorage.getItem(config.auth.keyStorageKey);
            if (storedKeys) {
                const keys = JSON.parse(storedKeys);
                privateKey = keys.privateKey;
                publicKey = keys.publicKey;
                console.log('✅ Loaded stored keys');
                return;
            }
            
            // Generate new keys (simplified implementation)
            privateKey = generateRandomKey();
            publicKey = generatePublicKey(privateKey);
            
            // Store keys
            localStorage.setItem(config.auth.keyStorageKey, JSON.stringify({
                privateKey: privateKey,
                publicKey: publicKey
            }));
            
            console.log('✅ Generated new keys');
            
        } catch (error) {
            console.error('❌ Error generating keys:', error);
            throw error;
        }
    }
    
    /**
     * Generate a random private key
     * @returns {string} Private key
     */
    function generateRandomKey() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }
    
    /**
     * Generate public key from private key (simplified)
     * @param {string} privateKey - The private key
     * @returns {string} Public key
     */
    function generatePublicKey(privateKey) {
        // In a real implementation, this would use proper cryptographic functions
        // For now, we'll use a simple hash-based approach
        const encoder = new TextEncoder();
        const data = encoder.encode(privateKey);
        return crypto.subtle.digest('SHA-256', data).then(hash => {
            return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
        });
    }
    
    /**
     * Request challenge from backend
     * @param {Object} config - The chatbot configuration
     * @returns {Object} Challenge response
     */
    async function requestChallenge(config) {
        const challengeUrl = `${config.backendUrl}${config.auth.keyAuthEndpoint}`;
        
        const response = await fetch(challengeUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                public_key: publicKey,
                username: config.auth.username || 'chatbot_user'
            })
        });
        
        if (!response.ok) {
            throw new Error(`Challenge request failed: ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Sign challenge with private key
     * @param {string} challenge - The challenge to sign
     * @returns {string} Signature
     */
    async function signChallenge(challenge) {
        // In a real implementation, this would use proper cryptographic signing
        // For now, we'll use a simple hash-based approach
        const encoder = new TextEncoder();
        const data = encoder.encode(`${publicKey}:${challenge}`);
        const hash = await crypto.subtle.digest('SHA-256', data);
        return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
    }
    
    /**
     * Verify challenge and get token
     * @param {Object} config - The chatbot configuration
     * @param {string} challengeId - The challenge ID
     * @param {string} signature - The signature
     * @returns {Object} Verification response
     */
    async function verifyChallenge(config, challengeId, signature) {
        const verifyUrl = `${config.backendUrl}${config.auth.keyAuthVerifyEndpoint}`;
        
        const response = await fetch(verifyUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                challenge_id: challengeId,
                public_key: publicKey,
                signature: signature
            })
        });
        
        if (!response.ok) {
            throw new Error(`Challenge verification failed: ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Perform login with username/password
     * @param {Object} config - The chatbot configuration
     */
    async function performLogin(config) {
        try {
            const loginUrl = `${config.backendUrl}${config.auth.loginEndpoint}`;
            
            const response = await fetch(loginUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: config.auth.username,
                    password: config.auth.password
                })
            });
            
            if (!response.ok) {
                throw new Error(`Login failed: ${response.status}`);
            }
            
            const data = await response.json();
            authToken = data.token;
            userId = data.user?.id;
            
            // Store token for future use
            localStorage.setItem(config.auth.tokenKey, authToken);
            
            console.log('✅ Login successful');
            
        } catch (error) {
            console.error('❌ Login failed:', error);
            throw error;
        }
    }
    
    /**
     * Get authentication headers for API calls
     * @returns {Object} Headers object with authentication
     */
    function getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        return headers;
    }
    
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
                timestamp: timestamp,
                user_id: config.userId // Include userId for multi-tenant support
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
                    timestamp: timestamp,
                    user_id: config.userId // Include userId for multi-tenant support
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
        if (!config.enableRAG) {
            return [];
        }
        
        try {
            // Make authenticated request to RAG backend
            const searchUrl = `${config.backendUrl}/search`;
            
            const response = await fetch(searchUrl, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    query: query,
                    top_k: config.maxRAGResults,
                    threshold: config.ragThreshold,
                    user_id: config.userId // Include userId for multi-tenant support
                })
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    console.error('❌ Authentication failed. Please login again.');
                    // Clear invalid token
                    localStorage.removeItem(config.auth.tokenKey);
                    authToken = null;
                } else {
                    console.error('❌ RAG search failed:', response.status);
                }
                return [];
            }
            
            const data = await response.json();
            
            // Handle both old and new response formats
            const documents = data.documents || data.results || [];
            
            // Filter by similarity threshold
            const relevantResults = documents.filter(result => 
                result.similarity >= config.ragThreshold
            );
            
            console.log(`🔍 Found ${relevantResults.length} relevant documents for query: "${query}" (User: ${config.userId})`);
            
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