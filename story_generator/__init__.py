"""
故事生成模块

提供基于 vLLM 的英语教学故事生成功能，包括：
- 故事框架生成
- 故事情节细化
- 开场白和结束语生成
- 课程总结和关键词提取

使用 LangChain + Pydantic 实现结构化输出
"""

from .story_processor import StoryProcessor
from .vllm_client import VLLMClient
from .schemas import (
    StoryContent,
    WordItem,
    Character,
    Scene,
    ScriptLine,
    VideoScript
)

__all__ = [
    'StoryProcessor',
    'VLLMClient',
    'StoryContent',
    'WordItem',
    'Character',
    'Scene',
    'ScriptLine',
    'VideoScript',
]

