"""
故事生成模块

提供基于 vLLM 的英语教学故事生成功能，包括：
- 故事框架生成
- 故事情节细化
- 开场白和结束语生成
- 课程总结和关键词提取
"""

from .story_processor import StoryProcessor
from .vllm_client import VLLMClient

__all__ = ['StoryProcessor', 'VLLMClient']

