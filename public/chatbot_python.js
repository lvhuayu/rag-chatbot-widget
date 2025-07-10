(function() {
    'use strict';
    
    // 全局 RAG 服务实例
    let ragService = null;
    let contentIngestionPerformed = false;
    
    // 初始化聊天机器人函数，config为用户配置
    window.initRAGChatbot = async function(config) {
        const defaultConfig = {
            selector: null,
            theme: {
                primaryColor: '#007bff'
            },
            welcomeMessage: 'Hello! I\'m your AI assistant with RAG capabilities (Python backend). How can I help you today?',
            promptTypeId: 'default',
            enableContentIngestion: false,
            ingestEndpoint: 'https://yourdomain.com/api/ingest',
            enableRAG: true,
            backendUrl: 'https://essayformatter.com:8001', // Python 后端地址
            ragThreshold: 0.7,
            maxRAGResults: 3
        };
        
        const finalConfig = Object.assign({}, defaultConfig, config);
        
        // 初始化后端 RAG 服务
        try {
            const { RAGServiceClient } = await import('./rag_service_client.js');
            ragService = new RAGServiceClient(finalConfig.backendUrl);
            await ragService.initialize();
            console.log('✅ RAG service initialized with Python backend');
        } catch (error) {
            console.error('❌ Failed to initialize Python backend RAG service:', error);
            finalConfig.enableRAG = false;
        }
        
        // 如果开启内容采集且未采集过，则执行采集
        if (finalConfig.enableContentIngestion && !contentIngestionPerformed) {
            await performContentIngestion(finalConfig);
            contentIngestionPerformed = true;
        }
        
        // 创建 iframe 容器
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
        
        // 如果传了selector，挂载到对应节点下，并调整样式
        if (finalConfig.selector) {
            const targetElement = document.querySelector(finalConfig.selector);
            if (targetElement) {
                targetElement.appendChild(iframe);
                iframe.style.position = 'relative';
                iframe.style.bottom = 'auto';
                iframe.style.right = 'auto';
            }
        }
        
        // iframe 加载完成后，发送配置消息
        iframe.onload = function() {
            iframe.contentWindow.postMessage({
                type: 'CHATBOT_CONFIG',
                config: finalConfig
            }, '*');
        };
        
        document.body.appendChild(iframe);
        
        return iframe;
    };
    
    /**
     * 提取页面可见文本内容
     * @returns {string} 清理过的纯文本内容
     */
    function extractVisibleContent() {
        const bodyClone = document.body.cloneNode(true);
        const removeTags = ['script', 'style', 'noscript', 'iframe', 'img', 'svg', 'canvas', 'video', 'audio'];
        const nodesToRemove = bodyClone.querySelectorAll(removeTags.join(','));
        nodesToRemove.forEach(el => el.remove());
        
        let content = bodyClone.textContent || bodyClone.innerText || '';
        content = content
            .replace(/\s+/g, ' ')
            .replace(/\n+/g, ' ')
            .trim();
        console.log(content)    
        return content;
    }
    
    /**
     * 执行页面内容采集并上传至RAG知识库
     * @param {Object} config 配置项
     */
    async function performContentIngestion(config) {
        try {
            const pageContent = extractVisibleContent();
            const title = document.title || '';
            const url = window.location.href;
            const timestamp = new Date().toISOString();
            
            const truncatedContent = pageContent.length > 50000
                ? pageContent.substring(0, 50000) + '...'
                : pageContent;
            
            // 避免变量名冲突，改成 ragDocument
            const ragDocument = {
                url: url,
                title: title,
                content: truncatedContent,
                timestamp: timestamp
            };
            
            // 添加到Python后端RAG向量数据库
            if (config.enableRAG && ragService) {
                await ragService.addDocument(ragDocument);
                console.log('✅ Page content added to Python backend RAG vector database');
            }
            
            // 发送到外部 ingestEndpoint（如果配置了）
            if (config.ingestEndpoint && config.ingestEndpoint !== 'https://yourdomain.com/api/ingest') {
                fetch(config.ingestEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(ragDocument)
                })
                .then(resp => {
                    if (resp.ok) {
                        console.log('✅ Content sent to external ingest endpoint');
                    } else {
                        console.warn('⚠️ External ingestion failed with status:', resp.status);
                    }
                })
                .catch(err => {
                    console.warn('⚠️ External ingestion failed:', err.message);
                });
            }
        } catch (error) {
            console.error('❌ Error during content ingestion:', error);
        }
    }
    
    /**
     * 查询RAG相关内容
     * @param {string} query 用户查询文本
     * @param {Object} config 配置项
     * @returns {Array} 相关文档列表
     */
    async function searchRAGContext(query, config) {
        if (!config.enableRAG || !ragService) return [];
        try {
            // 这里用ragService的search方法，不是searchDocuments
            const results = await ragService.search(query, config.maxRAGResults);
            console.log(results)
            const filtered = results.filter(r => r.similarity >= config.ragThreshold);
            console.log(filtered)
            return filtered;
        } catch (error) {
            console.error('❌ Error searching RAG context:', error);
            return [];
        }
    }
    
    /**
     * 构建带RAG上下文增强的提示语
     * @param {string} userMessage 用户消息
     * @param {Array} ragResults RAG搜索结果
     * @returns {string} 拼接好的提示语
     */
    function buildRAGPrompt(userMessage, ragResults) {
        if (!ragResults || ragResults.length === 0) return userMessage;
        
        console.log(userMessage)
        let context = 'Based on the following relevant information:\n\n';
        ragResults.forEach((result, idx) => {
            context += `Source ${idx + 1} (${result.title}):\n${result.content}\n\n`;
        });
        context += `Please answer the following question using the information above: ${userMessage}`;
        return context;
    }
    
    // 对外暴露
    window.searchRAGContext = searchRAGContext;
    window.buildRAGPrompt = buildRAGPrompt;
    
})();
