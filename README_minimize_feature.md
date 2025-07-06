# 🤖 RAG Chatbot 最小化功能

## 概述

为RAG聊天机器人添加了最小化功能，用户可以将聊天窗口最小化为一个圆形图标，节省屏幕空间，同时保持快速访问。

## ✨ 新功能特性

### 🎯 核心功能
- **最小化按钮**: 在聊天窗口右上角添加了最小化按钮
- **圆形图标**: 最小化后显示为圆形机器人图标（🤖）
- **平滑动画**: 使用CSS transform和opacity实现流畅的过渡效果
- **悬停效果**: 鼠标悬停时图标会放大并增强阴影效果

### 🔧 技术特性
- **iframe通信**: 通过postMessage API实现iframe与父窗口的通信
- **响应式设计**: 支持不同屏幕尺寸和自定义容器
- **状态保持**: 最小化时保持聊天状态和配置
- **兼容性**: 保持原有的所有RAG和认证功能

## 📋 使用方法

### 1. 基本使用

```javascript
// 初始化聊天机器人
initRAGChatbot({
    backendUrl: 'http://localhost:8001',
    enableRAG: true,
    welcomeMessage: '你好！我是RAG助手，现在支持最小化功能了！'
});
```

### 2. 最小化操作

1. **最小化**: 点击聊天窗口右上角的最小化按钮（📊图标）
2. **展开**: 点击右下角的圆形机器人图标（🤖）
3. **动画**: 所有操作都有平滑的300ms过渡动画

### 3. 自定义容器

```javascript
// 将聊天机器人放在指定容器中
initRAGChatbot({
    selector: '#my-chatbot-container',
    backendUrl: 'http://localhost:8001'
});
```

## 🎨 样式定制

### 最小化按钮样式

```css
.minimize-button {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s ease;
}

.minimize-button:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
}
```

### 圆形图标样式

```css
#rag-chatbot-minimize {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    z-index: 10001;
    transition: all 0.3s ease;
}
```

## 🧪 测试方法

### 1. 使用测试脚本

```powershell
# 运行测试脚本
.\test-minimize-feature.ps1
```

### 2. 手动测试

1. 启动HTTP服务器：
   ```bash
   cd public
   python -m http.server 8080
   ```

2. 访问测试页面：
   ```
   http://localhost:8080/test-minimize.html
   ```

3. 测试最小化功能：
   - 点击最小化按钮
   - 验证动画效果
   - 点击圆形图标展开
   - 测试悬停效果

## 🔍 技术实现

### 1. 文件结构

```
public/
├── chatbot.js          # 主聊天机器人脚本（已更新）
├── chat-ui.html        # 聊天界面（已更新）
└── test-minimize.html  # 测试页面（新增）
```

### 2. 关键代码

#### 最小化按钮创建
```javascript
const minimizeButton = document.createElement('div');
minimizeButton.id = 'rag-chatbot-minimize';
minimizeButton.innerHTML = '🤖';
// ... 样式设置
```

#### 最小化/展开功能
```javascript
function minimizeChatbot() {
    iframe.style.transform = 'scale(0)';
    iframe.style.opacity = '0';
    setTimeout(() => {
        iframe.style.display = 'none';
        minimizeButton.style.display = 'flex';
    }, 300);
}

function expandChatbot() {
    minimizeButton.style.display = 'none';
    iframe.style.display = 'block';
    setTimeout(() => {
        iframe.style.transform = 'scale(1)';
        iframe.style.opacity = '1';
    }, 50);
}
```

#### iframe通信
```javascript
// 发送最小化消息
window.parent.postMessage({
    type: 'MINIMIZE_CHATBOT'
}, '*');

// 监听最小化消息
window.addEventListener('message', function(event) {
    if (event.data.type === 'MINIMIZE_CHATBOT') {
        minimizeChatbot();
    }
});
```

## 🐛 故障排除

### 常见问题

1. **最小化按钮不显示**
   - 检查CSS样式是否正确加载
   - 确认JavaScript没有报错

2. **动画效果不流畅**
   - 检查浏览器是否支持CSS transform
   - 确认没有其他CSS冲突

3. **圆形图标位置错误**
   - 检查z-index设置
   - 确认容器定位正确

4. **iframe通信失败**
   - 检查postMessage API支持
   - 确认域名和端口设置正确

### 调试方法

1. 打开浏览器开发者工具
2. 查看Console面板的错误信息
3. 检查Network面板的资源加载
4. 使用Elements面板检查DOM结构

## 📝 更新日志

### v1.1.0 (最新)
- ✅ 添加最小化功能
- ✅ 实现平滑动画效果
- ✅ 添加悬停交互效果
- ✅ 支持自定义容器
- ✅ 保持原有功能完整性

### v1.0.0
- ✅ 基础RAG聊天机器人功能
- ✅ 多租户支持
- ✅ 认证系统
- ✅ 文档上传和管理

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个功能！

## 📄 许可证

本项目采用MIT许可证。 