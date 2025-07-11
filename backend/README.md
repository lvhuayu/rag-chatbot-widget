# RAG Chatbot Backend

This is a Python FastAPI backend that provides RAG (Retrieval-Augmented Generation) functionality for the chatbot widget.

## Features

- **Real Embeddings**: Uses `sentence-transformers` with the `all-MiniLM-L6-v2` model
- **Vector Database**: ChromaDB for efficient similarity search
- **RESTful API**: FastAPI endpoints for document management and search
- **CORS Support**: Configured for frontend integration

## Setup

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Backend Server

```bash
python rag_server_simple.py
```

The server will start on `http://localhost:8000`

### 3. API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Health Check
- `GET /health` - Check if the backend is running

### Document Management
- `POST /add-document` - Add a document to the RAG system
- `GET /documents` - List all documents
- `DELETE /clear-documents` - Clear all documents

### Search
- `POST /search` - Search for relevant documents
- `GET /stats` - Get system statistics

## Frontend Integration

To use the Python backend instead of the browser-based RAG service:

1. Replace `rag-service.js` with `rag_service_client.js` in your HTML files
2. Make sure the backend is running on `http://localhost:8000`
3. The frontend will automatically connect to the backend

### Example HTML Update

```html
<!-- Replace this: -->
<script src="rag-service.js"></script>

<!-- With this: -->
<script src="backend/rag_service_client.js"></script>
```

## Configuration

### Backend URL
You can change the backend URL by modifying the constructor in `rag_service_client.js`:

```javascript
window.RAGService = new RAGServiceClient('http://your-backend-url:8000');
```

### Embedding Model
To use a different embedding model, modify `rag_server.py`:

```python
embedding_model = SentenceTransformer('your-model-name')
```

### Vector Database
The backend uses ChromaDB by default. You can modify the configuration in `rag_server.py`:

```python
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(
    name="rag_documents",
    metadata={"hnsw:space": "cosine"}  # or "l2", "ip"
)
```

## Performance

- **Embeddings**: Generated server-side for better performance
- **Vector Search**: ChromaDB provides fast similarity search
- **Scalability**: Can handle thousands of documents efficiently

## Production Deployment

For production deployment:

1. **Security**: Configure CORS origins properly
2. **Persistence**: Configure ChromaDB for persistent storage
3. **Scaling**: Use multiple workers with uvicorn
4. **Monitoring**: Add logging and monitoring

Example production command:
```bash
uvicorn rag_server:app --host 0.0.0.0 --port 8000 --workers 4
```

## 使用 Hugging Face 镜像加速模型下载

如果你在中国大陆，建议在下载模型前设置环境变量以使用 Hugging Face 镜像：

### PowerShell（推荐，临时生效）
```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

### Linux/Mac 或 WSL（临时生效）
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

设置后再运行模型下载命令，例如：
```powershell
huggingface-cli download BAAI/bge-large-zh-v1.5 --local-dir backend/bge-large-zh-v1.5
```

如需每次自动生效，可将上述命令加入你的 PowerShell profile 或 bashrc/zshrc 文件。 