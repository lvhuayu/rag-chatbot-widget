import requests
import os
import json

def get_token():
    token = os.environ.get('RAG_TOKEN')
    if token:
        return token
    try:
        with open('token.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        pass
    # 自动登录获取token
    print('未找到本地token，将自动登录获取...')
    username = input('请输入用户名: ').strip()
    password = input('请输入密码: ').strip()
    login_url = 'http://localhost:5000/api/auth/login'
    try:
        resp = requests.post(login_url, json={'username': username, 'password': password})
        if resp.status_code == 200 and 'token' in resp.json():
            token = resp.json()['token']
            # 保存到本地
            with open('token.txt', 'w', encoding='utf-8') as f:
                f.write(token)
            print('登录成功，token已保存到 token.txt')
            return token
        else:
            print('登录失败:', resp.text)
            exit(1)
    except Exception as e:
        print('登录请求失败:', e)
        exit(1)

def main():
    token = get_token()
    site_id = 'cmcvit2ft0001jguff2m89lyq'
    print(f'使用默认 site_id: {site_id}')
    start_urls = input('请输入要爬取的URL（多个用逗号分隔）: ').strip().split(',')
    start_urls = [url.strip() for url in start_urls if url.strip()]
    url = 'http://localhost:5000/api/upload/crawl'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        'site_id': site_id,
        'start_urls': start_urls
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        print('Status:', resp.status_code)
        print('Response:', resp.text)
    except Exception as e:
        print('请求失败:', e)

if __name__ == '__main__':
    main() 