"""
内部 Pydantic 模型定义

用于 LangChain 结构化输出的内部模型
"""

from typing import List
from pydantic import BaseModel, Field

from .schemas import WordItem


class TranslatedTopic(BaseModel):
    """翻译后的主题"""
    english_topic: str = Field(description="The topic translated to English, must be concise (less than 50 characters)")


class GeneratedStoryFramework(BaseModel):
    """生成的故事框架"""
    setting: str = Field(description="The setting/location of the story")
    characters: str = Field(description="Description of main characters")
    plot_outline: str = Field(description="Outline of the story plot with key events")
    key_expressions: List[str] = Field(description="5-8 CLASSIC, POPULAR, and COMMONLY USED English expressions that native speakers use in daily life. These should be high-frequency, practical, natural expressions that are contextually appropriate for the specific scenario. Avoid rare, overly formal, or context-limited expressions. The expressions must match the scenario topic naturally.")
    
    def to_text(self) -> str:
        """转换为文本格式"""
        expressions = "\n".join(f"- {exp}" for exp in self.key_expressions)
        return f"""Setting: {self.setting}

Characters: {self.characters}

Plot Outline: {self.plot_outline}

Key Expressions:
{expressions}"""


class GeneratedDetailedStory(BaseModel):
    """生成的详细故事"""
    story: str = Field(description="Complete story in English with natural dialogues, 2500-3500 words. The story should have well-developed plot with multiple scenes, rich character interactions, detailed dialogues, and natural story progression.")


class GeneratedOpening(BaseModel):
    """生成的开场白"""
    opening_script: str = Field(description="Video opening script in simple English, 50-100 words")


class GeneratedClosing(BaseModel):
    """生成的结束语"""
    closing_script: str = Field(description="Video closing script in simple English, 50-100 words")


class GeneratedSummary(BaseModel):
    """生成的课程总结"""
    summary: str = Field(description="Lesson summary in English, 150-200 words")


class ExtractedSentences(BaseModel):
    """提取的重要句子"""
    sentences: List[str] = Field(description="5-8 key English sentences from the story")


class ExtractedWords(BaseModel):
    """提取的新词汇"""
    words: List[WordItem] = Field(description="10-15 new vocabulary words with meanings and examples")


class GeneratedScript(BaseModel):
    """生成的剧本"""
    characters: List[dict] = Field(description="List of characters, each containing: name, role (main/supporting), description, gender (male/female/other), age_range (young/adult/elderly), personality")
    scenes: List[dict] = Field(description="List of scenes, each containing: scene_id (e.g., scene_1), description, location")
    script_lines: List[dict] = Field(description="List of script lines in chronological order, each containing: line_type (opening/dialogue/transition/scene_marker/closing), speaker (character name, optional), speaker_id (SPEAKER0/SPEAKER1/NARRATOR), content (dialogue or narration text), scene_id (optional, null for opening/closing)")

