#!/usr/bin/env python3
"""
调试RAG生成功能中的context内容
"""

import requests
import json

def debug_rag_context():
    """调试RAG生成功能中的context内容"""
    print("=== 调试RAG生成功能中的context内容 ===")
    
    # 获取token
    token_response = requests.post("http://localhost:8001/auth/token", 
                                 json={"apiKey": "cmcu4th0r0005wouf9qpp3s0d"})
    if token_response.status_code != 200:
        print(f"❌ 获取token失败: {token_response.status_code}")
        return
    
    token = token_response.json()["token"]
    
    # 先进行搜索，看看找到了什么内容
    search_data = {
        "query": "校医院急诊电话",
        "top_k": 3,
        "site_id": "cmcu4th0h0004woufa9gh58wn"
    }
    
    search_response = requests.post("http://localhost:8001/search", json=search_data)
    if search_response.status_code == 200:
        search_result = search_response.json()
        print(f"✅ 搜索成功，找到 {len(search_result['documents'])} 个文档")
        
        # 显示每个文档的内容
        for i, doc in enumerate(search_result['documents']):
            print(f"\n文档 {i+1}:")
            print(f"  标题: {doc['document']['title']}")
            print(f"  相似度: {doc['similarity']:.3f}")
            print(f"  内容长度: {len(doc['document']['content'])} 字符")
            
            # 查找校医院相关信息
            content = doc['document']['content']
            if "校医院" in content:
                # 找到校医院信息的位置
                hospital_index = content.find("校医院")
                start = max(0, hospital_index - 50)
                end = min(len(content), hospital_index + 100)
                print(f"  ✅ 包含校医院信息:")
                print(f"      {content[start:end]}...")
            else:
                print(f"  ❌ 不包含校医院信息")
    
    # 现在测试RAG生成，看看实际传递给Ollama的context
    print(f"\n=== 测试RAG生成功能 ===")
    
    rag_data = {
        "query": "校医院急诊电话",
        "top_k": 3,
        "site_id": "cmcu4th0h0004woufa9gh58wn"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    rag_response = requests.post("http://localhost:8001/rag-generate", 
                               json=rag_data, headers=headers)
    
    if rag_response.status_code == 200:
        rag_result = rag_response.json()
        print(f"✅ RAG生成成功")
        print(f"生成的回答: {rag_result['context']}")
        
        # 显示传递给Ollama的context内容
        print(f"\n=== 传递给Ollama的context内容 ===")
        for i, doc in enumerate(rag_result['documents']):
            print(f"\n文档 {i+1} 的content:")
            content = doc['document']['content']
            print(f"长度: {len(content)} 字符")
            print(f"前200字符: {content[:200]}...")
            
            # 查找校医院信息
            if "校医院" in content:
                hospital_index = content.find("校医院")
                start = max(0, hospital_index - 50)
                end = min(len(content), hospital_index + 100)
                print(f"校医院相关信息: {content[start:end]}...")
    else:
        print(f"❌ RAG生成失败: {rag_response.status_code}")

if __name__ == "__main__":
    debug_rag_context() 