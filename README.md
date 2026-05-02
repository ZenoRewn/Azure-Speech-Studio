# Azure Speech Studio

Azure Speech 服务的一站式 Web 工具集 — Flask + SocketIO 后端 + Aurora 玻璃质感前端 UI,为客户演示和真实业务场景覆盖 Azure Speech 全栈能力。密钥始终驻留服务端,适合在 AKS 上公网部署。

## 功能矩阵 (13 个 Tab)

### Speech to Text
| Tab | 说明 |
|---|---|
| **Realtime STT** | 流式语音转文字,支持说话人分离、连续/起始语言检测、短语列表提示 |
| **Fast Transcription** | Azure Fast Transcription REST API 批量转写,支持多语种检测 |
| **MAI-Transcribe** | 新一代 MAI-Transcribe-1 模型,覆盖 25 种语言 |
| **Whisper Batch** | Azure Speech v3.2 Batch API + Whisper 基础模型,异步长任务 |
| **LLM Speech** | LLM 增强的转写与翻译,支持 prompt 引导输出格式 |

### Text to Speech / 声音克隆
| Tab | 说明 |
|---|---|
| **Speech TTS** | Neural TTS 纯文本或 SSML,14 种内置声 |
| **Multi-Talker** | DragonHD `mstts:dialog`,9 种语种多人对话合成,内置模板 |
| **Voice Creation** | Personal Voice 四步向导(项目 → 同意 → 训练音频 → 提交) |
| **Voice Changer** | 实时变声(仅 eastus / westeurope / southeastasia,需 Blob Storage) |

### Translation
| Tab | 说明 |
|---|---|
| **Speech Translation** | 实时多目标语种翻译 |
| **Live Interpreter** | 语音到语音同声传译,支持 Personal Voice 克隆说话人 |
| **Voice Live Translator** | 基于 Voice Live,自然口语实时口译 |
| **Video Translation** | 视频配音 + 字幕,30 源语种 |

### Conversational AI / Content
| Tab | 说明 |
|---|---|
| **Voice Live** | 与 AI 实时语音对话,支持 gpt-realtime/4o/5 系列 + 10+ 声线,带 token 用量面板 |
| **Podcast Agent** | 文本生成 AI 播客(单主播/双主播、3 风格、5 时长) |

## 架构

- **后端**: Flask + Flask-SocketIO(gevent-websocket worker),Python Azure Speech SDK + Voice Live SDK,REST wrapper 封装 Fast Transcription / MAI / Whisper Batch / Video Translation / Podcast / Personal Voice
- **前端**: Vanilla JS + Aurora 设计系统(CSS 变量双主题、玻璃卡片、手工移植的 magicui 特效:border-beam / shimmer / number-ticker / ring-progress / waveform);`templates/index.html` 仅 38 行骨架,通过 Jinja `include` 把 sidebar / header / footer / 13 个 Tab 拆分为独立 partials
- **实时通信**: Socket.IO WebSocket,服务端 `sessions.py` 按 SID 管理会话资源与清理
- **音频 pipeline**: MediaRecorder + AudioWorklet (PCM16) 采集,浏览器端回放用 Web Audio API;服务端 `audio_utils.py` 提供 smoothstep fade-in / cosine crossfade 的 WAV 合成

## 快速开始

### 本地开发(裸跑)

```bash
pip install -r requirements.txt
cp .env.example .env    # 填入你的 Azure keys
python app.py
# 打开 http://localhost:5001
```

### 本地 Docker

```bash
cp .env.example .env
docker-compose up --build
```

### AKS 公网部署

见 [`deploy/aks/README.md`](deploy/aks/README.md) — 涵盖:
- Dockerfile(`gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker`)
- Deployment / Service(`sessionAffinity: ClientIP`) / Ingress(WebSocket upgrade + 3600s timeout + cookie affinity)
- HPA(CPU 70% 扩容,慢收缩保护在线会话)
- Azure Key Vault + Workload Identity 的密钥管理推荐配置

## 环境变量

```bash
# Azure Speech(必需)
ASIA_SPEECH_KEY=
ASIA_SPEECH_REGION=eastus

# Azure OpenAI(Voice Live / LLM Speech 需要)
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_VERSION=2025-04-01-preview

# Voice Live 端点
AZURE_VOICELIVE_ENDPOINT=

# Azure Blob Storage(Voice Changer / Video Translation 需要上传媒体)
AZURE_STORAGE_ACCOUNT=
AZURE_STORAGE_KEY=
AZURE_STORAGE_CONTAINER=speech-studio
```

所有配置也可以在浏览器侧栏动态填入,会保存到 sessionStorage(关闭标签页清空)。

## 项目结构

```
Azure-Speech-Studio/
├── app.py                      # Flask 入口 + 17 个 HTTP 路由 + /healthz
├── config.py                   # 所有语种 / 语音 / 模型 / 区域常量
├── sessions.py                 # SID 级会话管理与资源回收
├── requirements.txt
├── Dockerfile                  # python:3.11-slim + ffmpeg + gunicorn
├── docker-compose.yml
├── .env.example
├── deploy/aks/                 # Deployment / Service / Ingress / HPA / Secret + README
├── speech/                     # 所有 Azure 能力模块(共 16 个)
│   ├── realtime_stt.py  fast_transcription.py  speech_translate.py
│   ├── live_interpreter.py  voice_live.py  voice_live_translator.py
│   ├── llm_speech.py  tts.py  audio_utils.py
│   ├── mai_transcribe.py  whisper_batch.py  multi_talker_tts.py
│   ├── video_translation.py  voice_creation.py  voice_changer.py
│   └── podcast_agent.py
├── templates/
│   ├── index.html              # Aurora 3 列骨架,通过 Jinja include 组合
│   └── partials/
│       ├── sidebar.html        # 左侧配置面板(Speech / AOAI / Voice Live)
│       ├── header.html         # 标题 + 主题切换 + 13 个 Tab 导航
│       ├── footer.html         # JSON data payloads + SocketIO / Tab 脚本
│       └── tabs/               # 13 个 Tab partial(每 Tab 一文件)
└── static/
    ├── css/                    # tokens / base / aurora / components / effects / theme
    └── js/
        ├── app.js  effects.js  socket_manager.js  audio.js  worklets/
        └── tabs/               # 13 个 Tab 逻辑
```

## 运行要求

- Python 3.11+
- 现代浏览器(Web Audio API + AudioWorklet + WebSocket)
- Azure Speech 订阅 +(可选)Azure OpenAI、Voice Live、Blob Storage

## 端到端验证建议

1. Realtime STT — 麦克风说中文,确认实时转写
2. Speech TTS — 合成 SSML 并下载 WAV
3. Voice Live — 3 分钟对话,验证 WebSocket 不断
4. Multi-Talker — 用内置中英对话模板合成一段
5. Podcast Agent — 短文本(约 500 字)生成 Medium 时长播客
6. 切换深色/浅色主题,刷新后保留

## License

本项目基于 MIT License 发布。

