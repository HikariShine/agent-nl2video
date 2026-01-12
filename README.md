# NL2TK - Natural Language to TikTok

自动化短视频生成平台

## 项目简介

NL2TK 是一个基于 AI 的自动化短视频生成平台，通过热点追踪、智能剧本生成和视频制作流程，实现从热点发现到视频发布的全自动化工作流。

## 核心功能

1. **热点追踪**: 多源热点数据采集与分析
2. **剧本生成**: 基于热点和 AI 生成视频剧本
3. **视频生成**: 将剧本转换为成品视频
4. **任务调度**: 支持定时自动生成视频

## 项目结构

```
nl2tk/
├── src/                    # 源代码
│   ├── trending_tracker/  # 热点追踪模块
│   ├── script_generator/  # 剧本生成模块
│   ├── video_generator/   # 视频生成模块
│   ├── scheduler/         # 任务调度模块
│   ├── api/               # API服务层
│   └── database/          # 数据存储层
├── config/                # 配置文件
├── storage/               # 存储目录
│   ├── videos/           # 视频文件
│   ├── scripts/          # 剧本文件
│   └── db/               # 数据库文件
├── docs/                  # 文档
├── tests/                 # 测试
├── requirements.txt      # 依赖包
└── main.py               # 主入口
```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# API Keys
QWEN_API_KEY=your_qwen_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 存储路径
STORAGE_PATH=./storage
```

### 3. 运行测试

```bash
# 端到端测试
python test_e2e.py
```

### 4. 启动服务

```bash
# 启动API服务（包含定时任务）
python main.py
```

API 服务将在 `http://localhost:8000` 启动

## API 接口

### 热点追踪

- `GET /api/v1/trending/` - 获取热点列表
- `GET /api/v1/trending/{source}` - 按数据源获取热点

### 剧本生成

- `POST /api/v1/script/generate` - 生成剧本
- `GET /api/v1/script/{script_id}` - 获取剧本详情

### 视频生成

- `POST /api/v1/video/generate` - 生成视频
- `GET /api/v1/video/{video_id}` - 获取视频信息

### 工作流

- `POST /api/v1/workflow/create` - 创建工作流
- `POST /api/v1/workflow/execute` - 执行工作流

## 使用示例

### 1. 获取热点

```bash
curl http://localhost:8000/api/v1/trending/?limit=5
```

### 2. 生成剧本

```bash
curl -X POST http://localhost:8000/api/v1/script/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创作一个关于AI技术的60秒短视频剧本",
    "duration": 60
  }'
```

### 3. 生成视频

```bash
curl -X POST http://localhost:8000/api/v1/video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "script": {
      "title": "AI改变生活",
      "duration": 60,
      "scenes": [
        {
          "scene_id": 1,
          "duration": 20,
          "visual": "展示AI应用场景",
          "narration": "AI正在改变我们的生活",
          "subtitles": "AI改变生活"
        }
      ],
      "hashtags": ["#AI", "#科技"]
    }
  }'
```

### 4. 执行完整工作流

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute?workflow_name=auto_video_generation
```

## 开发计划

- [x] 项目基础搭建
- [x] 热点追踪模块
- [x] 文生剧本模块
- [x] 剧本生视频模块
- [x] 任务调度模块
- [x] API 服务层
- [x] 数据存储层
- [x] 端到端测试

## 注意事项

1. **API密钥**: 需要配置有效的 API 密钥才能使用 AI 功能
2. **视频生成**: 当前使用模拟实现，实际部署需要配置真实的视频生成 API
3. **数据存储**: MVP 版本使用文件存储，生产环境建议使用 PostgreSQL
4. **安全**: 当前版本未实现用户权限和加密，生产环境需要补充

## 许可证

MIT License

