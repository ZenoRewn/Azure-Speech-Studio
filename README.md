# Speech Studio

Azure Speech 服务的一站式 Web 工具集，基于 Flask + SocketIO 构建，提供实时语音识别、翻译、语音合成、AI 语音对话等功能。

## 功能概览

| 功能 | 说明 |
|------|------|
| **Realtime STT** | 实时语音转文字，支持说话人分离 (Diarization) |
| **Fast Transcription** | Azure Fast Transcription REST API 批量转写 |
| **Speech Translate** | 实时语音翻译，支持语言自动检测和多目标语言 |
| **Live Interpreter** | AI 驱动的实时同声传译，带语音合成输出 |
| **Voice Live** | 与 AI 进行实时语音对话（基于 Azure Voice Live SDK） |
| **LLM Speech** | LLM 增强的语音转写和翻译 |
| **TTS** | 文本转语音合成，支持纯文本和 SSML 模式 |

## 技术栈

- **后端**: Python / Flask / Flask-SocketIO
- **前端**: HTML / CSS / JavaScript (SPA)，WebSocket 实时通信
- **音频处理**: Web Audio API + AudioWorklet (PCM16)
- **云服务**: Azure Speech SDK, Azure OpenAI, Azure Voice Live

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（或直接设置环境变量）：

```bash
# Azure Speech 服务
ASIA_SPEECH_KEY=your_speech_key
ASIA_SPEECH_REGION=your_region          # 例如 eastasia

# Azure OpenAI（用于 Live Interpreter 等功能）
AZURE_OPENAI_API_KEY=your_aoai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_VERSION=2025-04-01-preview

# Azure Voice Live（用于 Voice Live 功能）
AZURE_VOICELIVE_ENDPOINT=your_voicelive_endpoint
```

> 也可以不配置环境变量，直接在 Web 界面的配置区域填写。

### 3. 启动

```bash
python app.py
```

访问 `http://localhost:5001` 即可使用。

## 项目结构

```
speech_studio/
├── app.py                  # Flask + SocketIO 入口，路由和生命周期管理
├── config.py               # 语言映射、语音配置、模型定义
├── sessions.py             # 基于 request.sid 的服务端会话管理
├── requirements.txt        # Python 依赖
├── speech/                 # 语音功能模块
│   ├── realtime_stt.py     # 实时语音识别
│   ├── fast_transcription.py # 快速批量转写
│   ├── speech_translate.py # 语音翻译
│   ├── live_interpreter.py # 实时同声传译
│   ├── voice_live.py       # Voice Live 语音对话
│   ├── llm_speech.py       # LLM 增强语音处理
│   ├── tts.py              # 文本转语音
│   └── audio_utils.py      # 音频工具函数
├── templates/
│   └── index.html          # SPA 主页面模板
└── static/
    ├── css/style.css        # 样式（支持深色/浅色主题）
    └── js/
        ├── app.js           # 主应用逻辑、Tab 切换、配置管理
        ├── socket_manager.js # SocketIO 连接管理
        ├── audio.js         # 麦克风采集与音频播放
        ├── worklets/        # AudioWorklet 处理器
        └── tabs/            # 各功能 Tab 的前端逻辑
```

## 环境要求

- Python 3.9+
- 现代浏览器（需支持 Web Audio API 和 AudioWorklet）
- Azure Speech 服务订阅
- （可选）Azure OpenAI 服务订阅
