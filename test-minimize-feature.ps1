#!/usr/bin/env pwsh

# RAG Chatbot 最小化功能测试脚本
# 启动本地服务器来测试聊天机器人的最小化功能

Write-Host "🤖 RAG Chatbot 最小化功能测试" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# 检查是否安装了 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python，请先安装 Python" -ForegroundColor Red
    exit 1
}

# 检查是否安装了 Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js 已安装: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Node.js，请先安装 Node.js" -ForegroundColor Red
    exit 1
}

# 切换到项目目录
Set-Location $PSScriptRoot

Write-Host "`n📁 当前目录: $(Get-Location)" -ForegroundColor Yellow

# 检查必要的文件是否存在
$requiredFiles = @(
    "public/chatbot.js",
    "public/chat-ui.html", 
    "public/test-minimize.html"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ 找到文件: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ 缺少文件: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n🚀 启动测试服务器..." -ForegroundColor Yellow

# 启动 Python HTTP 服务器
Write-Host "🌐 启动 HTTP 服务器在端口 8080..." -ForegroundColor Blue

try {
    # 启动 Python 服务器
    Start-Process python -ArgumentList "-m", "http.server", "8080", "--directory", "public" -WindowStyle Hidden
    
    Write-Host "✅ HTTP 服务器已启动" -ForegroundColor Green
    Write-Host "🌐 服务器地址: http://localhost:8080" -ForegroundColor Cyan
    
    # 等待服务器启动
    Start-Sleep -Seconds 2
    
    # 尝试打开浏览器
    Write-Host "`n🌍 正在打开测试页面..." -ForegroundColor Yellow
    
    try {
        Start-Process "http://localhost:8080/test-minimize.html"
        Write-Host "✅ 测试页面已打开" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ 无法自动打开浏览器，请手动访问: http://localhost:8080/test-minimize.html" -ForegroundColor Yellow
    }
    
    Write-Host "`n📋 测试说明:" -ForegroundColor Cyan
    Write-Host "1. 聊天机器人会在页面右下角显示" -ForegroundColor White
    Write-Host "2. 点击聊天窗口右上角的最小化按钮（📊图标）" -ForegroundColor White
    Write-Host "3. 聊天窗口会平滑缩小并隐藏" -ForegroundColor White
    Write-Host "4. 此时会显示一个圆形机器人图标（🤖）" -ForegroundColor White
    Write-Host "5. 点击圆形图标可以重新展开聊天窗口" -ForegroundColor White
    Write-Host "6. 所有动画都有平滑的过渡效果" -ForegroundColor White
    
    Write-Host "`n🛑 按 Ctrl+C 停止服务器" -ForegroundColor Red
    
    # 保持脚本运行
    try {
        while ($true) {
            Start-Sleep -Seconds 1
        }
    } catch {
        Write-Host "`n🛑 正在停止服务器..." -ForegroundColor Yellow
        
        # 停止 Python 服务器
        Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*http.server*" } | Stop-Process -Force
        
        Write-Host "✅ 服务器已停止" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ 启动服务器失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 