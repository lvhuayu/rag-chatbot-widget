# 自动化网站爬虫 + 向量数据库存储系统
# 一键启动所有服务并运行自动化流程

Write-Host "🚀 启动自动化网站爬虫 + 向量数据库存储系统..." -ForegroundColor Green
Write-Host "=" * 60

# 检查必要的文件
$requiredFiles = @(
    "backend/import_jsonl_to_embeddings.py",
    "rag_scraper/playwright_langchain_loader/auto_vector_scraper.py",
    "rag_scraper/playwright_langchain_loader/main.py"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ 缺少必要文件: $file" -ForegroundColor Red
        exit 1
    }
}

# 步骤 1: 启动 RAG 主服务器（如果未运行）
Write-Host "📡 步骤 1: 检查 RAG 主服务器..." -ForegroundColor Yellow
$ragServerRunning = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ RAG 主服务器已在运行" -ForegroundColor Green
        $ragServerRunning = $true
    }
} catch {
    Write-Host "⚠️  RAG 主服务器未运行，需要手动启动" -ForegroundColor Yellow
    Write-Host "   请运行: cd backend && python rag_server_prisma.py" -ForegroundColor White
}

# 步骤 2: 启动 JSONL 导入 API 服务器
Write-Host "🔧 步骤 2: 启动 JSONL 导入 API 服务器..." -ForegroundColor Yellow

# 检查端口 8001 是否被占用
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ JSONL 导入 API 已在运行" -ForegroundColor Green
    }
} catch {
    Write-Host "🔄 启动 JSONL 导入 API 服务器..." -ForegroundColor Yellow
    
    # 启动 API 服务器（后台运行）
    $apiProcess = Start-Process -FilePath "python" -ArgumentList "backend/import_jsonl_to_embeddings.py" -PassThru -WindowStyle Hidden
    
    # 等待服务器启动
    Write-Host "⏳ 等待 API 服务器启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # 检查是否启动成功
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ JSONL 导入 API 启动成功" -ForegroundColor Green
        } else {
            Write-Host "❌ JSONL 导入 API 启动失败" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ JSONL 导入 API 启动失败，请检查端口 8001 是否被占用" -ForegroundColor Red
        exit 1
    }
}

# 步骤 3: 运行自动化爬虫
Write-Host "🕷️  步骤 3: 运行自动化爬虫..." -ForegroundColor Yellow

# 切换到爬虫目录
Push-Location "rag_scraper/playwright_langchain_loader"

# 检查虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
}

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# 安装依赖
Write-Host "📚 安装依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install requests tqdm

# 运行自动化爬虫
Write-Host "🚀 开始自动化爬取和存储流程..." -ForegroundColor Green
Write-Host ""

try {
    python auto_vector_scraper.py
} catch {
    Write-Host "❌ 自动化爬虫运行失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "故障排除:" -ForegroundColor Yellow
    Write-Host "1. 确保 RAG 主服务器在端口 8000 运行" -ForegroundColor White
    Write-Host "2. 确保 JSONL 导入 API 在端口 8001 运行" -ForegroundColor White
    Write-Host "3. 检查认证信息是否正确" -ForegroundColor White
    Write-Host "4. 检查网络连接" -ForegroundColor White
}

# 返回原目录
Pop-Location

Write-Host ""
Write-Host "✅ 自动化流程完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📊 下一步操作:" -ForegroundColor Yellow
Write-Host "1. 检查爬取结果: python check-db.py" -ForegroundColor White
Write-Host "2. 测试 RAG 功能: python test-rag-generate.py" -ForegroundColor White
Write-Host "3. 查看数据库统计: python backend/debug_site_documents.py" -ForegroundColor White 