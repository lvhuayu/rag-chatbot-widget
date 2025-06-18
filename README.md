# RAG Chatbot Widget

A lightweight, embeddable JavaScript chatbot widget that connects to your local Ollama LLM server. Perfect for adding AI-powered chat functionality to any website with minimal setup.

## 🚀 Features

- **🤖 Ollama Integration**: Seamlessly connects to local Ollama LLM server
- **🎨 Customizable Theme**: Fully customizable colors and styling
- **📄 Content Ingestion**: Automatic page content capture for RAG capabilities
- **📍 Flexible Positioning**: Fixed bottom-right or custom DOM element attachment
- **💬 Conversation Memory**: Maintains context across multiple messages
- **📱 Responsive Design**: Works perfectly on all devices
- **🔧 Easy Integration**: Single script tag integration

## 📋 Prerequisites

Before using this widget, ensure you have:

1. **Ollama installed** and running locally
2. **A model pulled** (e.g., `ollama pull mistral`)

### Quick Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model (in a new terminal)
ollama pull mistral
```

## 🛠️ Development Setup

1. **Clone or download** this project
2. **Install dependencies**:
   ```bash
   npm install
   ```
3. **Start development server**:
   ```bash
   npm run dev
   ```
4. **Open** `http://localhost:5500` in your browser

## 📦 Project Structure

```
rag-chatbot-widget/
├── public/
│   ├── index.html        # Test page with demo
│   ├── chatbot.js        # Main widget script
│   └── chat-ui.html      # Chat interface
├── package.json          # Project configuration
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🔧 Usage

### Basic Integration

Add this to any HTML page:

```html
<!-- Include the chatbot script -->
<script src="chatbot.js"></script>

<script>
    // Initialize with default settings
    initRAGChatbot({});
</script>
```

### Advanced Configuration

```html
<script src="chatbot.js"></script>

<script>
    initRAGChatbot({
        // Ollama model to use
        model: 'mistral',
        
        // Theme customization
        theme: {
            primaryColor: '#667eea'
        },
        
        // Welcome message
        welcomeMessage: 'Hello! How can I help you today?',
        
        // Content ingestion settings
        enableContentIngestion: true,
        ingestEndpoint: 'https://yourdomain.com/api/ingest',
        
        // Custom positioning (optional)
        selector: '#chat-container'
    });
</script>
```

## ⚙️ Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `'mistral'` | Ollama model name to use |
| `theme.primaryColor` | string | `'#007bff'` | Primary color for UI elements |
| `welcomeMessage` | string | `'Hello! I\'m your AI assistant...'` | Welcome message displayed |
| `enableContentIngestion` | boolean | `false` | Enable page content capture |
| `ingestEndpoint` | string | `'https://yourdomain.com/api/ingest'` | Content ingestion endpoint |
| `selector` | string | `null` | DOM selector for custom positioning |
| `promptTypeId` | string | `'default'` | Prompt type identifier |

## 🎨 Customization

### Theme Colors

```javascript
initRAGChatbot({
    theme: {
        primaryColor: '#667eea'  // Purple
        // primaryColor: '#28a745'  // Green
        // primaryColor: '#dc3545'  // Red
        // primaryColor: '#ffc107'  // Yellow
    }
});
```

### Custom Positioning

```html
<!-- Attach to specific element -->
<div id="my-chat-container"></div>

<script>
    initRAGChatbot({
        selector: '#my-chat-container'
    });
</script>
```

### Content Ingestion

When enabled, the widget will:

1. Capture page title and body text
2. Truncate content to 5000 characters
3. Send to specified endpoint via POST
4. Include content in conversation context

```javascript
initRAGChatbot({
    enableContentIngestion: true,
    ingestEndpoint: 'https://yourdomain.com/api/ingest'
});
```

## 🔍 Testing

### Local Development

1. Start the development server: `npm run dev`
2. Open `http://localhost:5500`
3. The chatbot will auto-initialize with demo configuration
4. Test Ollama connection using the "Test Ollama Connection" button

### Ollama Connection Test

The test page includes a connection checker that will:
- Verify Ollama server is running
- List available models
- Test the chat API
- Show connection status

## 🚀 Deployment

### CDN Deployment

1. Upload `chatbot.js` and `chat-ui.html` to your CDN
2. Update the iframe `src` in `chatbot.js` to point to your CDN URL
3. Include the script from your CDN

### Self-Hosted

1. Place both files in your web server directory
2. Ensure `chat-ui.html` is accessible from the same domain
3. Include the script in your HTML pages

## 🔧 Troubleshooting

### Common Issues

1. **"Failed to get response from LLM"**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is pulled: `ollama list`
   - Verify Ollama is accessible at `http://localhost:11434`

2. **Chatbot not appearing**
   - Check browser console for JavaScript errors
   - Verify `chatbot.js` is loaded correctly
   - Ensure `chat-ui.html` is accessible

3. **Theme not applying**
   - Check if `primaryColor` is a valid hex color
   - Verify CSS is not being overridden

### Debug Mode

Enable console logging by checking the browser's developer tools:

```javascript
// The widget logs detailed information to console
console.log('Chatbot config:', config);
console.log('Ollama response:', response);
```

## 📄 API Reference

### Ollama API Endpoint

The widget connects to: `http://localhost:11434/api/chat`

Request format:
```json
{
  "model": "mistral",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"}
  ],
  "stream": false
}
```

### Content Ingestion Format

When `enableContentIngestion` is true:
```json
{
  "title": "Page Title",
  "body": "Page content (truncated to 5000 chars)"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section above
- Review browser console for error messages
- Ensure Ollama is properly configured
- Open an issue on the repository

---

**Happy chatting! 🤖✨** 