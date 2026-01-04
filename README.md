# 一个仅需要输入场景主题就可以自动生成英语教学视频的工具

一个基于 AI 的英语教学视频自动生成工具，只需输入场景主题，即可自动生成包含故事、语音、插图和字幕的完整教学视频。

## 技术架构

- **内容生成**：通过调用本地 vLLM（大语言模型）生成故事内容
- **语音合成**：通过本地 TTS（文本转语音）合成自然语音
- **图像生成**：通过 ComfyUI API 生成故事剧情插图
- **视频合成**：使用 ffmpeg-python 合成最终视频

## 功能模块

### 课程主题故事生成
- 根据场景主题自动生成故事框架
- 细化故事情节，丰富故事内容
- 生成视频开场白、视频结束语
- 生成英语课程总结
- 提取重要句子和新词

### TTS 合成语音
- 将主题内容切片并生成语音文件
- 自动生成字幕文件（支持时间戳对齐）

### 生成插图
- 根据主题故事和字幕文件自动生成不同场景的插图
- 提供带有时间戳的 JSON 文件，用于视频合成时的时间对齐
- 使用 ComfyUI LoRA 模型进行风格化合成

### 视频合成
- 使用 ffmpeg-python 将语音、插图和字幕合成为最终视频
- 支持自动时间轴对齐和转场效果

## 使用示例

### 基本使用

```python
# 输入场景主题
topic = "在咖啡店点餐"

# 自动生成流程
# 1. 生成故事内容
story = generate_story(topic)

# 2. 生成语音和字幕
audio_files, subtitle_file = generate_audio_and_subtitle(story)

# 3. 生成插图
images, timestamp_json = generate_images(story, subtitle_file)

# 4. 合成视频
video = compose_video(audio_files, images, subtitle_file, timestamp_json)
```

### 输入格式

- **场景主题**：简单的文本描述，例如：
  - "在咖啡店点餐"
  - "机场办理登机手续"
  - "酒店入住登记"

### 输出内容

- **视频文件**：完整的英语教学视频（MP4 格式）
- **字幕文件**：SRT 或 VTT 格式的字幕文件
- **插图文件**：各场景对应的插图图片
- **时间戳 JSON**：插图与视频时间轴的对应关系

## 项目结构

```
english_courses/
├── README.md                 # 项目说明文档
├── pyproject.toml           # 项目依赖配置
├── logger_config.py         # 日志配置模块（loguru）
├── story_generator/          # 故事生成模块
│   ├── __init__.py          # 模块导出
│   ├── schemas.py           # Pydantic 数据模型定义
│   ├── story_processor.py   # 故事处理器（LangChain + 结构化输出）
│   └── vllm_client.py       # vLLM 客户端（向后兼容）
├── tts_module/              # TTS 语音合成模块
│   ├── tts_engine.py        # TTS 引擎封装
│   └── subtitle_generator.py # 字幕生成
├── image_generator/         # 图像生成模块
│   ├── comfyui_client.py    # ComfyUI API 客户端
│   └── image_processor.py   # 图像处理和时间戳生成
├── video_composer/          # 视频合成模块
│   └── ffmpeg_composer.py   # FFmpeg 视频合成
├── test_story_generation.py # 故事生成测试脚本
└── main.py                  # 主程序入口
```

## 技术细节

### 故事生成模块特性
- **中文主题自动翻译**：输入中文主题自动翻译为英文后生成英文故事
- **结构化输出**：使用 LangChain + Pydantic 实现结构化 JSON 输出
- **思考内容处理**：模型的 `<think>` 内容记录到日志但不保存到最终 JSON
- **日志规范**：使用 loguru 配置日志，所有日志输出为英文

### vLLM 配置
- 支持本地部署的大语言模型
- 使用 LangChain 的 ChatOpenAI 接口调用 vLLM（兼容 OpenAI API）
- 可配置模型路径和 API 端点
- 支持自定义提示词模板

### TTS 配置
- 支持多种本地 TTS 引擎
- 可配置语音参数（语速、音调、音色）
- 支持多语言语音合成

### ComfyUI 配置
- 通过 API 调用 ComfyUI 服务
- 支持 LoRA 模型加载和切换
- 可配置图像生成参数（分辨率、风格等）

### FFmpeg 配置
- 使用 ffmpeg-python 进行视频合成
- 支持自定义视频参数（分辨率、帧率、编码格式）
- 自动处理音频和视频同步