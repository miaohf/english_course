"""
故事生成模块

提供基于 vLLM 的英语教学故事生成功能
使用 LangChain + Pydantic 实现结构化输出
"""

from .story_processor import StoryProcessor
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
    'StoryContent',
    'WordItem',
    'Character',
    'Scene',
    'ScriptLine',
    'VideoScript',
]

