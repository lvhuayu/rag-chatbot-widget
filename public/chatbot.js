(function() {
    'use strict';
    
    // Global function to initialize the chatbot
    window.initRAGChatbot = function(config) {
        // Default configuration
        const defaultConfig = {
            selector: null,
            theme: {
                primaryColor: '#007bff'
            },
            welcomeMessage: 'Hello! I\'m your AI assistant. How can I help you today?',
            promptTypeId: 'default',
            enableContentIngestion: false,
            ingestEndpoint: 'https://yourdomain.com/api/ingest'
        };
        
        // Merge user config with defaults
        const finalConfig = Object.assign({}, defaultConfig, config);
        
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
        
        // Handle content ingestion if enabled
        if (finalConfig.enableContentIngestion) {
            const pageContent = {
                title: document.title,
                body: document.body.innerText || document.body.textContent || ''
            };
            
            // Truncate body text to 5000 characters
            if (pageContent.body.length > 5000) {
                pageContent.body = pageContent.body.substring(0, 5000) + '...';
            }
            
            finalConfig.pageContent = pageContent;
            
            // Send content to ingest endpoint
            fetch(finalConfig.ingestEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(pageContent)
            }).catch(error => {
                console.warn('Failed to ingest page content:', error);
            });
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