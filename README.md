# SisterAI-Chat-Memory
基于 Tkinter 的智能桌面应用，模拟具备长期记忆的拟人化 AI 角色。采用四级记忆架构（短期/长期/潜在/重要记忆），通过 TF-IDF/Cosine 相似度实现语义检索，支持角色设定定制与实时流式交互。

A Tkinter-based chatbot implementing hierarchical memory architecture (short-term/long-term/latent/important) with TF-IDF semantic search. Features role customization and real-time streaming responses.

---

## 项目名称：**SisterAI-Chat**  
`🤖 具有长期记忆的 AI 姐姐角色扮演聊天桌面应用`

---

## 项目简介
一个基于 Tkinter 的智能桌面聊天应用，模拟拥有长期记忆的姐姐角色。通过多级记忆管理系统（短期/长期/潜在/重要记忆）和语义检索技术，实现自然连贯的上下文对话，支持自定义角色设定和流式响应交互。

---

## 核心功能
- 🎭 可定制的姐弟角色扮演对话模式
- 🧠 四级记忆管理系统（自动压缩/检索/存储）
- 🔍 TF-IDF + 余弦相似度语义检索
- 📊 实时对话字数统计与记忆分析
- 🖥️ 桌面悬浮窗设计（支持拖拽/置顶）
- ⚡ 流式响应与线程安全机制

---

## 环境依赖
```bash
# requirements.txt
Python                     3.10.16
openai                     1.65.1
scikit-learn               1.6.1
```

---

## 快速开始
1. **克隆仓库**：
```bash
git clone github.com/ixiaokaikai/SisterAI-Chat-Memory.git
cd SisterAI-Chat
```

2. **安装依赖**：
```bash  
# 创建 Python 3.10 虚拟环境  
conda create --name aitalk python=3.10 -y  

# 激活环境  
conda activate aitalk  

# 安装精确版本依赖  
pip install openai==1.65.1 scikit-learn==1.6.1  
```  

3. **配置环境**：
```python
# 在 main.py 中设置（首次运行自动生成）
AI_API_KEY = "your_api_key_here"  # 支持 OpenAI 格式 API
AI_BASE_URL = "https://your.model.endpoint"  # 云端或本地部署
AI_MODEL = "your-model-name"
```

4. **启动应用**：
```bash
python main.py
```

---

## 项目结构
```
SisterAI-Chat/
├── memory/               # 记忆存储目录
│   ├── 姐姐/            # 角色专属记忆
│   │   ├── full_memory.csv
│   │   ├── short_term_memory.csv
│   │   └── ...
├── main.py               # 主要文件
└── README.md
```

---

## 高级配置
1. **角色定制**：
```python
ROLE_PROFILE = """
你是一个温柔体贴的姐姐，
喜欢用可爱的表情动作...
"""
```

2. **记忆参数**：
```python
# 调整记忆容量
MAX_SHORT_TERM_MEMORY = 20      # 短期记忆容量
MEMORY_COMPRESSION_LENGTH = 15  # 对话压缩阈值
```

3. **本地模型支持**：
```python
# 取消注释使用本地模型
# AI_API_KEY = "none"
# AI_BASE_URL = "http://localhost:1234/v1"
# AI_MODEL = "local-model-name"
```

---

## 提交 Issue 指南
当你提交 Issue 时，请附上以下信息：
- ✅ 操作系统版本
- ✅ Python 环境信息
- ✅ 复现步骤截图

---

## Project Name: **SisterAI-Chat**  
`🤖 AI Sister Role-Playing Chat Desktop App with Long-Term Memory`

---

## Project Overview  
A Tkinter-based intelligent desktop chat application that simulates a sister character with long-term memory. Features multi-level memory management (short-term/long-term/potential/critical memory) and semantic search technology to achieve natural contextual conversations, supporting customizable role configurations and streaming response interactions.

---

## Core Features  
- 🎭 Customizable sibling role-playing dialogue mode  
- 🧠 Four-level memory system (auto-compression/retrieval/storage)  
- 🔍 TF-IDF + Cosine Similarity semantic search  
- 📊 Real-time chat statistics & memory analysis  
- 🖥️ Floating window design (drag-and-drop/always-on-top)  
- ⚡ Streaming response & thread-safe mechanisms  

---

## Environment Requirements  
```bash
# requirements.txt  
Python                     3.10.16  
openai                     1.65.1  
scikit-learn               1.6.1  
```

---

## Quick Start  
1. **Clone repository**:  
```bash  
git clone github.com/ixiaokaikai/SisterAI-Chat-Memory.git  
cd SisterAI-Chat  
```  

2. **Install dependencies**:  
```bash  
# 创建 Python 3.10 虚拟环境  
conda create --name aitalk python=3.10 -y  

# 激活环境  
conda activate aitalk  

# 安装精确版本依赖  
pip install openai==1.65.1 scikit-learn==1.6.1  
```  

3. **Configure environment**:  
```python  
# Set in main.py (auto-generated on first run)  
AI_API_KEY = "your_api_key_here"  # Supports OpenAI-compatible APIs  
AI_BASE_URL = "https://your.model.endpoint"  # Cloud or local deployment  
AI_MODEL = "your-model-name"  
```  

4. **Launch application**:  
```bash  
python main.py  
```  

---

## Project Structure  
```
SisterAI-Chat/  
├── memory/               # Memory storage  
│   ├── 姐姐/            # Role-specific memory  
│   │   ├── full_memory.csv  
│   │   ├── short_term_memory.csv  
│   │   └── ...  
├── main.py               # Main entry  
└── README.md  
```

---

## Advanced Configuration  
1. **Role Customization**:  
```python  
ROLE_PROFILE = """  
You are a gentle and caring elder sister,  
who enjoys using cute emojis and gestures...  
"""  
```  

2. **Memory Parameters**:  
```python  
# Memory capacity settings  
MAX_SHORT_TERM_MEMORY = 20      # Short-term memory slots  
MEMORY_COMPRESSION_LENGTH = 15  # Conversation compression threshold  
```  

3. **Local Model Support**:  
```python  
# Uncomment for local models  
# AI_API_KEY = "none"  
# AI_BASE_URL = "http://localhost:1234/v1"  
# AI_MODEL = "local-model-name"  
```  

---

## Issue Submission Guidelines
When submitting issues, please include the following information:
- ✅ OS version
- ✅ Python environment details
- ✅ Reproduction steps with screenshots

---

希望这些修改能让你的 `README.md` 文件更符合 GitHub 风格并且更易于阅读和理解。如果你还有其他需求或修改意见，请随时告诉我。 
