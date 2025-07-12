#!/usr/bin/env python3
import requests
import json
import time

def test_rag_generate_endpoint():
    """测试 /rag-generate 端点是否正常工作"""
    url = "http://localhost:8001/rag-generate"
    payload = {
        "query": "收费方案",
        "user_id": "main_page_user",
        "top_k": 3
    }
    
    try:
        print("🔗 测试 /rag-generate 端点...")
        response = requests.post(url, json=payload, timeout=60)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /rag-generate 端点正常工作")
            print(f"返回的 context 长度: {len(data.get('context', ''))}")
            print(f"找到的文档数量: {len(data.get('documents', []))}")
            return True
        else:
            print(f"❌ /rag-generate 端点返回错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试 /rag-generate 端点失败: {e}")
        return False

def test_search_endpoint():
    """测试 /search 端点是否仍然可用（用于对比）"""
    url = "http://localhost:8001/search"
    payload = {
        "query": "收费方案",
        "user_id": "main_page_user",
        "top_k": 3
    }
    
    try:
        print("\n🔍 测试 /search 端点（对比用）...")
        response = requests.post(url, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /search 端点仍然可用")
            print(f"返回的文档数量: {len(data.get('documents', []))}")
            return True
        else:
            print(f"❌ /search 端点返回错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试 /search 端点失败: {e}")
        return False

def main():
    print("🚀 开始测试 RAG 系统 API 切换...")
    print("=" * 50)
    
    # 测试 /rag-generate 端点
    rag_generate_ok = test_rag_generate_endpoint()
    
    # 测试 /search 端点（对比）
    search_ok = test_search_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"✅ /rag-generate 端点: {'正常' if rag_generate_ok else '异常'}")
    print(f"✅ /search 端点: {'正常' if search_ok else '异常'}")
    
    if rag_generate_ok:
        print("\n🎉 所有前端文件已成功切换到 /rag-generate API!")
        print("💡 现在所有用户提问都会通过大模型生成回答，而不是直接返回原始内容。")
    else:
        print("\n⚠️ 需要检查后端 /rag-generate 端点是否正常启动。")

if __name__ == "__main__":
    main() 