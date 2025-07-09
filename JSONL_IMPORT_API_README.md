# JSONL to Embeddings Import API

这个 API 允许你将从 Playwright + LangChain 爬虫生成的 JSONL 文件导入到 RAG 系统的 embeddings 表中。

## 功能特性

✅ **JSONL 文件导入** - 支持直接上传 JSONL 文件  
✅ **Base64 内容导入** - 支持通过 API 发送 JSONL 内容  
✅ **自动生成 Embeddings** - 使用 SOTA 模型生成向量  
✅ **JWT 认证** - 安全的用户认证  
✅ **错误处理** - 详细的错误报告和统计  
✅ **批量处理** - 支持大量文档的批量导入  

## API 端点

### 1. 健康检查
```
GET /health
```
返回 API 状态和模型信息。

### 2. 文件导入
```
POST /import-jsonl-file
```
上传 JSONL 文件进行导入。

**参数：**
- `file`: JSONL 文件 (multipart/form-data)
- `site_id`: 站点 ID (form data)
- `Authorization`: Bearer token (header)

### 3. 内容导入
```
POST /import-jsonl
```
通过 Base64 编码的内容进行导入。

**请求体：**
```json
{
  "site_id": "your-site-id",
  "jsonl_content": "base64-encoded-jsonl-content"
}
```

### 4. 统计信息
```
GET /stats/{site_id}
```
获取指定站点的导入统计信息。

## 使用方法

### 步骤 1: 启动 API 服务器

```powershell
.\start-import-api.ps1
```

或者手动启动：

```powershell
cd backend
python import_jsonl_to_embeddings.py
```

### 步骤 2: 获取认证 Token

你需要先获取 JWT token。可以使用现有的认证 API：

```bash
# 使用现有的 RAG 服务器获取 token
curl -X POST "http://localhost:8000/auth/register-key" \
  -H "Content-Type: application/json" \
  -d '{"public_key": "your-public-key", "username": "your-username"}'
```

### 步骤 3: 导入 JSONL 文件

#### 方法 A: 使用测试脚本

```powershell
python test-import-jsonl-api.py
```

#### 方法 B: 使用 curl

```bash
# 文件上传
curl -X POST "http://localhost:8001/import-jsonl-file" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@rag_scraper/playwright_langchain_loader/output/rag_chunks.jsonl" \
  -F "site_id=your-site-id"

# 内容导入
curl -X POST "http://localhost:8001/import-jsonl" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "your-site-id",
    "jsonl_content": "base64-encoded-content"
  }'
```

#### 方法 C: 使用 Python 客户端

```python
import requests
import base64

# 读取 JSONL 文件
with open('rag_chunks.jsonl', 'r', encoding='utf-8') as f:
    content = f.read()

# 编码为 Base64
jsonl_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

# 发送请求
response = requests.post(
    'http://localhost:8001/import-jsonl',
    headers={
        'Authorization': 'Bearer YOUR_JWT_TOKEN',
        'Content-Type': 'application/json'
    },
    json={
        'site_id': 'your-site-id',
        'jsonl_content': jsonl_b64
    }
)

print(response.json())
```

## JSONL 格式要求

JSONL 文件应该包含以下格式的每一行：

```json
{"text": "文档内容...", "metadata": {"url": "...", "title": "...", "source": "..."}}
{"text": "另一个文档块...", "metadata": {"url": "...", "title": "...", "source": "..."}}
```

**必需字段：**
- `text`: 文档内容（字符串）
- `metadata.url`: 来源 URL（可选）
- `metadata.title`: 文档标题（可选）
- `metadata.source`: 来源信息（可选）

## 响应格式

### 成功响应
```json
{
  "success": true,
  "imported_count": 10,
  "errors": [],
  "message": "Successfully imported 10 documents with 0 errors"
}
```

### 错误响应
```json
{
  "success": true,
  "imported_count": 8,
  "errors": [
    "Line 9: Empty text content",
    "Line 15: Invalid JSON - Expecting ',' delimiter"
  ],
  "message": "Successfully imported 8 documents with 2 errors"
}
```

## 数据库结构

导入的数据会存储到以下表中：

### documents 表
```sql
CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  site_id TEXT NOT NULL,
  title TEXT,
  url TEXT,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### embeddings 表
```sql
CREATE TABLE embeddings (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  embedding_vector BLOB NOT NULL,
  dimension INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 故障排除

### 常见问题

1. **认证失败**
   - 确保使用有效的 JWT token
   - 检查 token 是否过期

2. **文件格式错误**
   - 确保文件是有效的 JSONL 格式
   - 检查每行是否包含必需的字段

3. **数据库连接错误**
   - 确保 Prisma 数据库已正确设置
   - 运行 `npx prisma db push` 更新数据库

4. **内存不足**
   - 对于大文件，考虑分批导入
   - 增加服务器内存限制

### 调试技巧

1. **查看详细日志**
   ```powershell
   $env:LOG_LEVEL="DEBUG"
   python import_jsonl_to_embeddings.py
   ```

2. **测试小文件**
   - 先用少量数据测试
   - 确认格式正确后再处理大文件

3. **检查数据库**
   ```python
   # 使用现有的检查脚本
   python check-db.py
   ```

## 性能优化

1. **批量处理**: API 支持批量导入，但建议单次不超过 1000 条记录
2. **并发限制**: 避免同时发送多个大文件
3. **内存管理**: 大文件会自动分批处理
4. **错误恢复**: 支持部分失败，成功导入的记录会保留

## 安全注意事项

1. **Token 安全**: 不要在代码中硬编码 JWT token
2. **文件验证**: API 会验证文件格式和内容
3. **访问控制**: 确保只有授权用户可以访问 API
4. **数据隔离**: 不同站点的数据完全隔离

## 扩展功能

未来可能添加的功能：
- 增量导入（跳过已存在的文档）
- 并行处理支持
- 自定义 embedding 模型
- 导入进度跟踪
- WebSocket 实时状态更新 