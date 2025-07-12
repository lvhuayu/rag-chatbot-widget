# 自动化网站爬虫 + 向量数据库存储系统

这是一个完整的自动化系统，能够爬取网站内容后自动将内容存储到向量数据库中，实现真正的端到端自动化。

## 🎯 系统架构

```
网站爬取 → 内容提取 → 文本切块 → 生成 Embeddings → 存储到向量数据库
    ↓           ↓           ↓           ↓              ↓
Playwright  BeautifulSoup  LangChain  SOTA Model    Prisma DB
```

## 🚀 快速开始

### 方法 1: 一键启动（推荐）

```powershell
.\start-auto-vector-scraper.ps1
```

这个脚本会自动：
1. 检查并启动所有必要的服务
2. 运行自动化爬虫
3. 显示结果和统计信息

### 方法 2: 手动启动

#### 步骤 1: 启动 RAG 主服务器
```powershell
cd backend
python rag_server_prisma.py
```

#### 步骤 2: 启动 JSONL 导入 API
```powershell
cd backend
python import_jsonl_to_embeddings.py
```

#### 步骤 3: 运行自动化爬虫
```powershell
cd rag_scraper/playwright_langchain_loader
python auto_vector_scraper.py
```

## ⚙️ 配置说明

### 1. 编辑配置文件

修改 `rag_scraper/playwright_langchain_loader/config.json`：

```json
{
  "scraping": {
    "urls": [
      "https://your-website.com/page1",
      "https://your-website.com/page2",
      "https://your-website.com/page3"
    ],
    "site_name": "我的网站内容",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "timeout": 60000
  },
  "authentication": {
    "username": "your_username",
    "public_key": "your_public_key",
    "rag_api_url": "http://localhost:8000"
  },
  "api": {
    "import_api_url": "http://localhost:8001",
    "embedding_model": "BAAI/bge-large-zh-v1.5"
  }
}
```

### 2. 配置参数说明

#### 爬取配置 (scraping)
- `urls`: 要爬取的网站 URL 列表
- `site_name`: 站点名称，用于标识存储的内容
- `chunk_size`: 文本切块大小（字符数）
- `chunk_overlap`: 切块重叠大小（字符数）
- `timeout`: 页面加载超时时间（毫秒）

#### 认证配置 (authentication)
- `username`: 用户名
- `public_key`: 公钥（用于认证）
- `rag_api_url`: RAG 主服务器地址

#### API 配置 (api)
- `import_api_url`: JSONL 导入 API 地址
- `embedding_model`: 使用的 embedding 模型

## 📊 工作流程

### 1. 自动化流程

```
开始
  ↓
🔐 认证用户
  ↓
📥 爬取网站内容
  ↓
🔄 提取和清理文本
  ↓
✂️ 文本切块
  ↓
🧠 生成 Embeddings
  ↓
💾 存储到向量数据库
  ↓
📈 生成统计报告
  ↓
完成
```

### 2. 详细步骤

#### 步骤 1: 认证
- 使用配置的用户名和公钥进行认证
- 获取 JWT token 用于后续 API 调用

#### 步骤 2: 爬取内容
- 使用 Playwright 渲染每个网页
- 支持 JavaScript 动态内容
- 自动等待页面加载完成

#### 步骤 3: 内容处理
- 使用 BeautifulSoup 提取正文
- 移除广告、导航等无关内容
- 保留结构化信息

#### 步骤 4: 文本切块
- 使用 LangChain 进行智能切块
- 保持语义完整性
- 支持重叠切块

#### 步骤 5: 生成 Embeddings
- 使用 SOTA 模型生成向量
- 支持中文和多语言
- 自动归一化处理

#### 步骤 6: 存储数据
- 存储文档到 documents 表
- 存储 embeddings 到 embeddings 表
- 建立文档和向量的关联

## 📈 监控和统计

### 实时监控
系统会显示：
- 爬取进度
- 成功/失败统计
- 错误详情
- 存储结果

### 统计信息
```json
{
  "success": true,
  "site_id": "site_1234567890",
  "scraped_count": 15,
  "stored_count": 15,
  "errors": [],
  "message": "成功爬取 15 个文档块，存储 15 个到向量数据库"
}
```

## 🔧 故障排除

### 常见问题

1. **认证失败**
   ```
   错误: 认证失败，请检查用户名和公钥
   解决: 修改 config.json 中的认证信息
   ```

2. **服务器未启动**
   ```
   错误: 连接被拒绝
   解决: 确保 RAG 主服务器和导入 API 都已启动
   ```

3. **爬取失败**
   ```
   错误: 爬取失败 [URL]: 超时
   解决: 增加 timeout 配置或检查网络连接
   ```

4. **存储失败**
   ```
   错误: 存储失败: 数据库连接错误
   解决: 检查 Prisma 数据库配置
   ```

### 调试技巧

1. **查看详细日志**
   ```powershell
   $env:LOG_LEVEL="DEBUG"
   python auto_vector_scraper.py
   ```

2. **测试单个 URL**
   ```json
   {
     "scraping": {
       "urls": ["https://example.com/test"]
     }
   }
   ```

3. **检查数据库状态**
   ```powershell
   python check-db.py
   ```

## 🚀 高级功能

### 1. 批量处理
- 支持大量 URL 的批量爬取
- 自动错误恢复
- 进度跟踪

### 2. 增量更新
- 检查 URL 是否已存在
- 只爬取新内容
- 避免重复处理

### 3. 自定义处理
- 支持自定义文本提取规则
- 可配置的切块策略
- 灵活的 metadata 处理

### 4. 性能优化
- 并发爬取支持
- 内存优化
- 缓存机制

## 📝 使用示例

### 示例 1: 爬取博客文章
```json
{
  "scraping": {
    "urls": [
      "https://blog.example.com/post1",
      "https://blog.example.com/post2",
      "https://blog.example.com/post3"
    ],
    "site_name": "技术博客"
  }
}
```

### 示例 2: 爬取文档网站
```json
{
  "scraping": {
    "urls": [
      "https://docs.example.com/getting-started",
      "https://docs.example.com/api-reference",
      "https://docs.example.com/tutorials"
    ],
    "site_name": "产品文档"
  }
}
```

### 示例 3: 爬取新闻网站
```json
{
  "scraping": {
    "urls": [
      "https://news.example.com/tech",
      "https://news.example.com/business",
      "https://news.example.com/science"
    ],
    "site_name": "新闻资讯"
  }
}
```

## 🔒 安全注意事项

1. **认证安全**
   - 不要在代码中硬编码认证信息
   - 使用环境变量存储敏感信息
   - 定期更新认证密钥

2. **访问控制**
   - 确保只有授权用户可以访问
   - 限制爬取频率避免被封
   - 遵守网站的 robots.txt

3. **数据安全**
   - 加密存储敏感数据
   - 定期备份数据库
   - 监控异常访问

## 📞 技术支持

如果遇到问题，请：

1. 查看日志文件
2. 检查配置文件
3. 验证网络连接
4. 确认服务状态

## 🎉 总结

这个自动化系统实现了：
- ✅ 一键爬取网站内容
- ✅ 自动生成高质量 embeddings
- ✅ 无缝存储到向量数据库
- ✅ 完整的监控和统计
- ✅ 易于配置和使用

现在你可以轻松地将任何网站的内容转换为可搜索的向量数据！ 