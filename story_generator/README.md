# Story Generator 模块

故事生成模块，用于自动生成英语教学视频的故事内容和剧本。

## 概述

Story Generator 是一个基于 LangChain + Pydantic 的故事生成系统，采用**直接生成结构化剧本**的架构：

- 一次性生成完整剧本（角色、场景、对话、旁白）
- 说话者在生成时就已确定，无需后续提取
- 自动保存视觉种子，用于图像生成

## 快速开始

### 基本使用

```python
from story_generator import StoryProcessor

# 初始化处理器
processor = StoryProcessor()

# 生成完整故事
story_content = processor.generate_complete_story(
    topic="在机场候机时与陌生人聊天",
    output_dir="outputs/20260105",
    base_filename="story"
)

# 保存故事
processor.save_story(story_content, "outputs/20260105/story.json")
```

### 命令行使用

```bash
# 基本使用
python test_story_generation.py

# 指定主题文件
python test_story_generation.py --topics-file my_topics.json
```

## 生成流程

```
1. 主题翻译（中文 → 英文）
2. 生成故事概要（summary, characters, key_expressions）
3. 直接生成完整剧本（角色、场景、对话、旁白）
```

## 配置选项

在 `.env` 文件中配置：

```bash
# vLLM API 配置
VLLM_API_URL=http://192.168.1.197:6800/v1
VLLM_API_KEY=sk-yourverystrongrandomkey1234567890abcdef
VLLM_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8
VLLM_ENABLE_THINKING=true
VLLM_MAX_TOKENS=1000000
```

## 输出文件

```
outputs/20260105/Topic_Name/
├── story.json              # 完整故事内容
├── script.json             # 视频剧本
├── tts.txt                 # TTS格式剧本
├── visual_seeds.json       # 视觉种子（用于图像生成）
└── summary.md              # 故事概要
```

## 模块结构

```
story_generator/
├── __init__.py             # 模块导出
├── story_processor.py      # 主处理器
├── story_generators.py     # 故事生成器
├── prompts.py              # LLM 提示词
├── schemas.py              # 数据模型
├── internal_schemas.py     # 内部结构化输出模型
└── file_operations.py      # 文件操作
```

## 主要特性

### 1. 直接生成结构化剧本

- 一次性生成完整剧本，包含角色、场景、对话、旁白
- 说话者在生成时就已确定，避免分配错误
- 简化流程，减少错误

### 2. 视觉种子

自动保存角色视觉描述，用于图像生成一致性：

```python
import json
with open('outputs/story/visual_seeds.json', 'r') as f:
    visual_seeds = json.load(f)
```

### 3. 反 AI 痕迹设计

- 禁止"回音式"对白
- 避免过度巧合
- 自然的对话
