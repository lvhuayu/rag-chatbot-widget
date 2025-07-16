(function() {
    'use strict';
    
    // Global variables
    let ragService = null;
    let contentIngestionPerformed = false;
    let authToken = null;
    let userId = null;
    let privateKey = null;
    let publicKey = null;
    
    // Detect environment and set API base URL
    const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    const API_BASE_URL = isLocalhost ? "http://localhost:8001" : "https://essayformatter.com";
    
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
            ragThreshold: 0.7,
            maxRAGResults: 3,
            backendUrl: API_BASE_URL, // Use detected API base URL
            ollamaUrl: 'http://localhost:11434',
            
            // Multi-tenant configuration
            userId: userId,
            
            // Authentication configuration
            auth: {
                token: null,
                username: null,
                password: null,
                autoLogin: false,
                loginEndpoint: '/api/auth/login',
                tokenKey: 'rag_chatbot_token',
                
                // Public/Private Key Authentication
                useKeyAuth: false, // Disabled by default for simplicity
                keyAuthEndpoint: '/auth/request-challenge',
                keyAuthVerifyEndpoint: '/auth/verify-challenge',
                keyStorageKey: 'rag_chatbot_keys',
                publicKey: null,
                
                // Registered Key Authentication
                useRegisteredKey: false,
                registeredUsername: null,
                uploadPortalUrl: 'http://localhost:3001',
                publicKeyEndpoint: '/api/auth/public-key'
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
        
        console.log('🔑 Multi-tenant setup:', { userId: finalConfig.userId });
        console.log('🔗 Backend URL:', finalConfig.backendUrl);
        
        // Handle authentication
        await handleAuthentication(finalConfig);
        
        // Initialize RAG service if enabled
        if (finalConfig.enableRAG) {
            try {
                console.log('✅ RAG service initialized successfully');
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
        iframe.src = 'https://lingwenai.cn/chat-ui.html';
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
            display: flex;
            flex-direction: column;
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
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            z-index: 10001;
            transition: all 0.3s ease;
        `;
        
        // Add hover effects (matching index.html style)
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
            iframe.style.display = 'none';
            minimizeButton.style.display = 'flex';
            isMinimized = true;
        }
        
        function expandChatbot() {
            minimizeButton.style.display = 'none';
            iframe.style.display = 'block';
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
            // Check if we have a stored token and siteId
            const storedToken = localStorage.getItem(config.auth.tokenKey);
            const storedSiteId = localStorage.getItem('rag_chatbot_siteid');

            if (storedToken && storedSiteId === config.siteId) {
                authToken = storedToken;
                console.log('✅ Using stored authentication token');
                return;
            }

            // If siteId changed, clear the old token
            localStorage.removeItem(config.auth.tokenKey);
            localStorage.setItem('rag_chatbot_siteid', config.siteId);

            // 新增：apiKey换token
            if (config.apiKey && !authToken) {
                try {
                    const res = await fetch(config.backendUrl + '/auth/token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ apiKey: config.apiKey })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        authToken = data.token;
                        localStorage.setItem(config.auth.tokenKey, authToken);
                        localStorage.setItem('rag_chatbot_apikey', config.apiKey);
                        console.log('✅ Token obtained via apiKey');
                        return;
                    } else {
                        console.warn('❌ Failed to get token via apiKey:', res.status);
                    }
                } catch (err) {
                    console.warn('❌ Error fetching token via apiKey:', err);
                }
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
            const publicKey = publicKeyData.publicKey;
            
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
                const privateKey = keys.privateKey;
                const publicKey = keys.publicKey;
                console.log('✅ Loaded stored keys');
                return { privateKey, publicKey };
            }
            
            // Generate new keys (simplified implementation)
            const privateKey = generateRandomKey();
            const publicKey = await generatePublicKey(privateKey);
            
            // Store keys
            localStorage.setItem(config.auth.keyStorageKey, JSON.stringify({
                privateKey: privateKey,
                publicKey: publicKey
            }));
            
            console.log('✅ Generated new keys');
            return { privateKey, publicKey };
            
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
    async function generatePublicKey(privateKey) {
        // In a real implementation, this would use proper cryptographic functions
        // For now, we'll use a simple hash-based approach
        const encoder = new TextEncoder();
        const data = encoder.encode(privateKey);
        const hash = await crypto.subtle.digest('SHA-256', data);
        return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
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
                public_key: config.auth.publicKey,
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
        const data = encoder.encode(`${config.auth.publicKey}:${challenge}`);
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
                public_key: config.auth.publicKey,
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
     * @param {Function} onData - Optional callback for streaming data
     * @returns {Array} Relevant documents with similarity scores
     */
    async function searchRAGContext(query, config, onData) {
        if (!config.enableRAG) {
            return [];
        }
        
        try {
            // Make authenticated request to RAG backend using /rag-generate
            const ragGenerateUrl = `${config.backendUrl}/rag-generate`;
            
            const response = await fetch(ragGenerateUrl, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    query: query,
                    top_k: config.maxRAGResults,
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
                    console.error('❌ RAG generate failed:', response.status);
                }
                return [];
            }
            
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('text/event-stream')) {
                // 流式 SSE 处理
                if (!response.body) {
                    throw new Error('No response body');
                }
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let done = false;
                let fullMsg = '';
                while (!done) {
                    const { value, done: doneReading } = await reader.read();
                    done = doneReading;
                    if (value) {
                        const chunk = decoder.decode(value, { stream: true });
                        chunk.split('\n').forEach(line => {
                            if (line.startsWith('data:')) {
                                const text = line.replace(/^data:/, '').trim();
                                if (text) {
                                    fullMsg += text;
                                    if (onData) onData(fullMsg);
                                }
                            }
                        });
                    }
                }
                return [{ document: { id: '', url: '', title: '', content: fullMsg, timestamp: new Date().toISOString() }, similarity: 1 }];
            } else {
                // 兼容旧接口
                const data = await response.json();
                
                // Handle both old and new response formats
                const documents = data.documents || data.results || [];
                
                // Filter by similarity threshold
                const relevantResults = documents.filter(result => 
                    result.similarity >= config.ragThreshold
                );
                
                console.log(`🔍 Found ${relevantResults.length} relevant documents for query: "${query}" (User: ${config.userId})`);
                
                return relevantResults;
            }
            
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
    
    // Add comprehensive styles to match index.html design
    const style = document.createElement('style');
    style.textContent = `
        /* 聊天机器人容器样式 */
        #rag-chatbot-iframe {
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        #rag-chatbot-iframe:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
        }
        
        /* 最小化按钮样式 */
        #rag-chatbot-minimize {
            transition: all 0.3s ease;
        }
        
        #rag-chatbot-minimize:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
        }
        
        /* 聊天机器人消息样式 */
        .chatbot-message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .chatbot-message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 12px;
            flex-shrink: 0;
        }
        
        .chatbot-message.user .message-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .chatbot-message.bot .message-avatar {
            background: #e5e7eb;
            color: #374151;
        }
        
        .message-content {
            max-width: 70%;
            padding: 10px 14px;
            border-radius: 16px;
            line-height: 1.4;
            word-wrap: break-word;
            font-size: 14px;
        }
        
        /* 强制 Markdown 渲染后的内容保持原有字体大小 */
        .message-content * {
            font-size: inherit !important;
            line-height: inherit !important;
        }
        
        .message-content p {
            margin: 0.5em 0;
        }
        
        .message-content h1, .message-content h2, .message-content h3, 
        .message-content h4, .message-content h5, .message-content h6 {
            font-size: 12px !important;
            font-weight: 600;
            margin: 0.5em 0;
        }
        
        .message-content ul, .message-content ol {
            margin: 0.5em 0;
            padding-left: 1.5em;
        }
        
        .message-content li {
            margin: 0.2em 0;
        }
        
        .message-content strong, .message-content b {
            font-weight: 600;
        }
        
        .message-content em, .message-content i {
            font-style: italic;
        }
        
        .chatbot-message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .chatbot-message.bot .message-content {
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            border-bottom-left-radius: 4px;
        }
        
        /* 输入框样式 */
        .chatbot-input {
            padding: 15px;
            background: white;
            border-top: 1px solid #e5e7eb;
            border-radius: 0 0 12px 12px;
        }
        
        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        .message-input {
            flex: 1;
            border: 2px solid #e5e7eb;
            border-radius: 18px;
            padding: 10px 14px;
            font-size: 16px;
            resize: none;
            outline: none;
            transition: border-color 0.3s ease;
            font-family: inherit;
            max-height: 80px;
            min-height: 36px;
        }
        
        .message-input:focus {
            border-color: #667eea;
        }
        
        .send-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            flex-shrink: 0;
        }
        
        .send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* 打字指示器样式 */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 10px 14px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            border-bottom-left-radius: 4px;
            max-width: 70%;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #9ca3af;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        
        /* 聊天机器人头部样式 */
        .chatbot-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chatbot-header h3 {
            font-size: 16px;
            font-weight: 600;
            margin: 0;
        }
        
        .chatbot-controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .minimize-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .minimize-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.1);
        }
        
        /* 消息区域样式 */
        .chatbot-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
    `;
    document.head.appendChild(style);
    
})(); 