#!/usr/bin/env python3
"""
Update document with complete business information
"""

import requests
import json

def update_document():
    """更新文档内容"""
    
    # 完整的业务文档内容
    new_content = """凌问 AI - 网站功能与收费方案说明

📌 网站定位
本网站提供一项名为「凌问 AI」的服务 —— 一个可嵌入任意网站的智能聊天机器人系统。
用户只需插入一行代码，就能为自己的网站添加一个支持中文大模型的 AI 对话窗口，支持自动问答、知识库接入、多轮上下文记忆等功能。

✅ 主要功能

功能模块        简要说明
----------      -------------------------------------------------
🔧 一行嵌入       通过 <script> 标签将 AI 聊天窗口嵌入任意网页、博客、商城、官网等
🧠 智能对话       基于国内先进的大模型，自动理解并回答用户问题
📚 私有知识库     支持上传文档构建专属问答内容（如 PDF、Markdown、Word）
🔐 多租户隔离     每个站点独立配置知识、风格和 API 权限，数据不混用
🎨 风格定制       聊天窗口颜色、头像、欢迎语等均可自定义
🧾 对话记录       后台可查看所有对话记录，便于优化知识库或客户服务
📈 限速计费       根据 siteId 实现限速控制，避免滥用或攻击

🧾 收费方案（示例）

版本     | 月费     | 适合用户               | 功能限制
--------|----------|------------------------|-----------------------------
免费版   | ¥0       | 博客、测试用户         | 每月对话次数限制，无知识库
基础版   | ¥49/月   | 内容站、咨询类网站     | 支持知识库，每日100条对话
专业版   | ¥199/月  | 企业官网、电商平台     | 无限知识库，2000次/月，自定义风格
私有化版 | ¥999/月起 | 企业 / 教育客户        | 私有部署，定制化支持

👨‍💻 适合用户类型
- 想在网页中嵌入 AI 客服功能的个人站长、小微企业
- 公众号 / 小程序作者希望提升转化率
- 想展示 AI Copilot / Demo 的 AI 创业项目
- 教育、心理、法律等行业希望用 AI 做内容答疑

🚀 如何使用？
1. 注册后创建站点，获得 siteId 与 apiKey
2. 在网页中插入如下代码：

<script src="https://yourcdn.com/chat-bot.js" data-api-key="你的 apiKey"></script>

3. 聊天窗口即可自动加载，无需开发！

🧩 后续支持功能（开发中）
- 微信 / 企业微信接入
- 多语言支持（中英双语）
- 插件系统（如自动填写表单、推荐商品）"""
    
    # 先清除现有文档
    try:
        print("🗑️ Clearing existing documents...")
        response = requests.delete("http://localhost:8001/clear-documents?user_id=main_page_user", timeout=10)
        if response.status_code == 200:
            print("✅ Documents cleared")
        else:
            print(f"⚠️ Clear failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Clear error: {e}")
    
    # 添加新文档
    try:
        print("📝 Adding new document...")
        response = requests.post("http://localhost:8001/add-documents", 
                               json=[{
                                   "url": "https://lingwen-ai.com",
                                   "title": "凌问 AI - 网站功能与收费方案说明",
                                   "content": new_content,
                                   "user_id": "main_page_user"
                               }],
                               timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document added successfully")
            print(f"📊 Result: {result}")
        else:
            print(f"❌ Add failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Add error: {e}")

def test_queries():
    """测试查询"""
    test_queries = ["资费", "收费方案", "价格", "月费", "费用"]
    
    print("\n" + "="*60)
    print("🧪 Testing Queries After Update")
    print("="*60)
    
    for query in test_queries:
        try:
            response = requests.post("http://localhost:8001/search", 
                                   json={
                                       "query": query,
                                       "user_id": "main_page_user",
                                       "threshold": 0.1,
                                       "top_k": 3
                                   },
                                   timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🔍 Query: '{query}'")
                print(f"📊 Found {len(data.get('documents', []))} documents")
                
                if data.get('context'):
                    print(f"📝 Context: {data['context'][:200]}...")
                else:
                    print("❌ No context found")
                    
        except Exception as e:
            print(f"❌ Query error for '{query}': {e}")

if __name__ == "__main__":
    update_document()
    test_queries() 