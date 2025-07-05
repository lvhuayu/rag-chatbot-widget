#!/usr/bin/env pwsh

# 工作日记创建脚本
# 使用方法: .\create-daily-journal.ps1

param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$journalDir = "work-journal"
$journalFile = "$journalDir/$Date.md"

# 检查文件夹是否存在，如果不存在则创建
if (!(Test-Path $journalDir)) {
    New-Item -ItemType Directory -Path $journalDir
    Write-Host "创建文件夹: $journalDir" -ForegroundColor Green
}

# 检查文件是否已存在
if (Test-Path $journalFile) {
    Write-Host "日记文件已存在: $journalFile" -ForegroundColor Yellow
    $response = Read-Host "是否要覆盖? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "操作已取消" -ForegroundColor Red
        exit
    }
}

# 创建日记内容
$content = @"
# 工作日记 - $Date

## 今日工作内容
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3

## 遇到的问题
- 问题1：描述和解决方案
- 问题2：描述和解决方案

## 学习收获
- 新学到的技术或方法
- 有用的资源链接

## 明日计划
- 计划完成的任务
- 需要学习的内容

## 其他笔记
- 会议记录
- 想法和灵感
- 代码片段

---
*创建时间：$Date*
"@

# 写入文件
$content | Out-File -FilePath $journalFile -Encoding UTF8

Write-Host "已创建日记文件: $journalFile" -ForegroundColor Green
Write-Host "你可以使用以下命令打开文件:" -ForegroundColor Cyan
Write-Host "code $journalFile" -ForegroundColor White 