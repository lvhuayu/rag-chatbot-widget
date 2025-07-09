import requests
import os

def get_token():
    token = os.environ.get('RAG_TOKEN')
    if token:
        return token
    try:
        with open('token.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        pass
    return input('请输入你的JWT Token: ').strip()

def main():
    token = get_token()
    url = 'http://localhost:3001/api/upload/siteid'
    headers = {'Authorization': f'Bearer {token}'}
    try:
        resp = requests.get(url, headers=headers)
        print('Status:', resp.status_code)
        print('Response:', resp.json())
    except Exception as e:
        print('请求失败:', e)

if __name__ == '__main__':
    main() 