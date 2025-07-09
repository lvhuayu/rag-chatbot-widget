#!/usr/bin/env python3
"""
测试RAG搜索和生成质量
"""

import requests
import json

def test_search():
    """测试搜索功能"""
    print("=== 测试搜索功能 ===")
    
    # 搜索"校医院急诊电话"
    search_data = {
        "query": "校医院急诊电话",
        "top_k": 3,
        "site_id": "cmcu4th0h0004woufa9gh58wn"
    }
    
    response = requests.post("http://localhost:8001/search", json=search_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 搜索成功，找到 {len(result['documents'])} 个文档")
        
        for i, doc in enumerate(result['documents']):
            print(f"\n文档 {i+1}:")
            print(f"  标题: {doc['document']['title']}")
            print(f"  相似度: {doc['similarity']:.3f}")
            print(f"  内容预览: {doc['document']['content'][:200]}...")
            
            # 检查是否包含校医院信息
            if "校医院" in doc['document']['content']:
                print("  ✅ 包含校医院信息")
            else:
                print("  ❌ 不包含校医院信息")
    else:
        print(f"❌ 搜索失败: {response.status_code}")

def test_rag_generate():
    """测试RAG生成功能"""
    print("\n=== 测试RAG生成功能 ===")
    
    # 获取token
    token_response = requests.post("http://localhost:8001/auth/token", 
                                 json={"apiKey": "cmcu4th0r0005wouf9qpp3s0d"})
    if token_response.status_code != 200:
        print(f"❌ 获取token失败: {token_response.status_code}")
        return
    
    token = token_response.json()["token"]
    
    # RAG生成
    rag_data = {
        "query": "校医院急诊电话",
        "top_k": 3,
        "site_id": "cmcu4th0h0004woufa9gh58wn"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("http://localhost:8001/rag-generate", 
                           json=rag_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ RAG生成成功")
        print(f"生成的回答: {result['context']}")
        
        # 检查回答质量
        if "校医院" in result['context'] and ("62782185" in result['context'] or "62799120" in result['context']):
            print("✅ 回答包含正确的校医院急诊电话")
        else:
            print("❌ 回答没有包含正确的校医院急诊电话")
    else:
        print(f"❌ RAG生成失败: {response.status_code}")

def test_ollama_direct():
    """直接测试Ollama"""
    print("\n=== 直接测试Ollama ===")
    
    prompt = """你是一个有用的AI助手。请使用以下上下文来回答用户的问题。
如果上下文中的信息不足以回答问题，请说明这一点。

上下文：
校医院急诊010-62782185 / 010-62799120

用户问题：校医院急诊电话

请根据上述上下文提供有用且准确的回答（请用中文回答）："""

    ollama_data = {
        "model": "qwen:7b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000
        }
    }
    
    response = requests.post("http://localhost:11434/api/generate", json=ollama_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Ollama直接调用成功")
        print(f"回答: {result['response']}")
    else:
        print(f"❌ Ollama调用失败: {response.status_code}")

if __name__ == "__main__":
    test_search()
    test_rag_generate()
    test_ollama_direct() 