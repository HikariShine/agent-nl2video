# AI 视频生成方案说明

## 当前现实情况

### 为什么当前只有彩色背景？

**真正的AI视频生成**需要以下条件之一：

1. **Sora (OpenAI)** - 目前未公开API，需要等待
2. **Gemini Video** - 需要Google API密钥
3. **阿里云视频生成** - 需要阿里云账号和API密钥
4. **本地部署模型** - 需要高端GPU（至少8GB显存）

**当前的"本地策略"只是一个占位实现**，用于测试工作流程是否正常运行。

---

## 可用的AI视频生成方案

### 方案1: 阿里云视频生成 API（推荐）

**优点**：
- 国内服务，访问稳定
- 成本相对较低
- 支持中文

**配置方式**：
1. 注册阿里云账号
2. 开通通义万相视频生成服务
3. 获取API密钥
4. 配置到 `.env` 文件

**费用**：约 0.1-0.5 元/秒视频

### 方案2: 智谱AI CogVideoX

**优点**：
- 国内服务
- 支持API调用
- 质量较好

**配置方式**：
1. 注册智谱AI账号
2. 获取API密钥
3. 调用CogVideoX API

### 方案3: Runway Gen-2/Gen-3

**优点**：
- 质量高
- 支持API

**缺点**：
- 国外服务，可能需要VPN
- 费用较高

### 方案4: 本地部署 CogVideoX（需要GPU）

**要求**：
- NVIDIA GPU，至少 16GB 显存
- 约 20GB 磁盘空间

**安装**：
```bash
pip install diffusers transformers accelerate
```

**使用**：
```python
from diffusers import CogVideoXPipeline
import torch

pipe = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-2b",
    torch_dtype=torch.float16
)
pipe = pipe.to("cuda")

# 生成视频
video = pipe(
    prompt="一个美丽的日落场景",
    num_inference_steps=50,
    guidance_scale=6.0,
).frames[0]
```

---

## 推荐方案

### 短期（MVP阶段）

**使用阿里云视频生成API**：
1. 成本可控
2. 国内访问稳定
3. 质量可接受

### 长期（产品化阶段）

**混合策略**：
1. 优先使用 Sora（如果API开放）
2. 降级使用阿里云
3. 本地部署作为备用

---

## 如何集成阿里云视频生成

### 1. 创建阿里云视频生成策略

```python
# src/video_generator/aliyun_strategy.py

import dashscope
from dashscope import VideoGeneration

class AliyunVideoStrategy(VideoGenerationStrategy):
    async def generate(self, script, output_path=None):
        # 将剧本转换为提示词
        prompt = self._script_to_prompt(script)
        
        # 调用阿里云API
        response = VideoGeneration.call(
            model="video-generation",
            prompt=prompt,
            duration=script.duration,
        )
        
        # 下载视频并保存
        video_url = response.output.video_url
        # ...保存视频到本地
```

### 2. 配置

```env
# .env
ALIYUN_VIDEO_API_KEY=your_api_key
```

```python
# 配置
VIDEO_CONFIG = {
    "strategy": "aliyun",
    "strategy_config": {
        "api_key": settings.aliyun_video_api_key,
    },
}
```

---

## 当前代码的作用

当前的 `LocalVideoStrategy` 是一个**测试用的占位实现**：

- ✅ 验证工作流程是否正常
- ✅ 测试字幕、音乐等后期处理功能
- ✅ 确保代码架构正确
- ❌ 不能生成真正的AI视频内容

**要生成真正的AI视频，需要集成上述API之一**。

---

## 下一步行动

1. **选择一个视频生成API**（推荐阿里云）
2. **获取API密钥**
3. **实现对应的Strategy类**
4. **配置并测试**

如果你告诉我你选择哪个方案，我可以帮你实现具体的集成代码。

