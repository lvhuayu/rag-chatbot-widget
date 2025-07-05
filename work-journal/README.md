# 工作日记 (Work Journal)

这个文件夹用于记录日常工作的笔记、想法和进展。

## 文件命名规范

- 使用日期格式：`YYYY-MM-DD.md`
- 例如：`2024-01-15.md`

## 日记模板

每个日记文件可以包含以下内容：

### 今日工作内容
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3

### 遇到的问题
- 问题1：描述和解决方案
- 问题2：描述和解决方案

### 学习收获
- 新学到的技术或方法
- 有用的资源链接

### 明日计划
- 计划完成的任务
- 需要学习的内容

### 其他笔记
- 会议记录
- 想法和灵感
- 代码片段

## 快速创建今日日记

可以使用以下命令快速创建今日的日记文件：

```bash
# Windows PowerShell
$date = Get-Date -Format "yyyy-MM-dd"
New-Item -Path "work-journal/$date.md" -ItemType File
```

## 有用的命令

```bash
# 查看所有日记文件
ls work-journal/*.md

# 搜索特定内容
grep -r "关键词" work-journal/

# 统计日记数量
ls work-journal/*.md | Measure-Object | Select-Object Count
``` 