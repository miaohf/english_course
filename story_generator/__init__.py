"""
故事生成模块

提供基于 vLLM 的英语教学故事生成功能
"""

from .story_processor import StoryProcessor
from .schemas import (
    WordItem,
    Character,
    Scene,
    ScriptLine,
    SceneNarration,
    VideoScript
)

__all__ = [
    'StoryProcessor',
    'WordItem',
    'Character',
    'Scene',
    'ScriptLine',
    'SceneNarration',
    'VideoScript',
]

