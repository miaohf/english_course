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


class ExtractedSentences(BaseModel):
    """提取的重要句子"""
    sentences: List[str] = Field(description="5-8 key English sentences from the story")


class ExtractedWords(BaseModel):
    """提取的新词汇"""
    words: List[WordItem] = Field(description="10-15 new vocabulary words with meanings and examples")


class GeneratedStorySummary(BaseModel):
    """生成的剧情概要"""
    summary: str = Field(description="Brief story summary/outline (200-300 words) that describes the overall plot, main characters, and key story progression")
    characters: str = Field(description="Description of main characters (names, roles, basic traits)")
    key_expressions: List[str] = Field(description="5-8 CLASSIC, POPULAR, and COMMONLY USED English expressions that native speakers use in daily life. These should be high-frequency, practical, natural expressions that are contextually appropriate for the specific scenario.")


class SceneDescription(BaseModel):
    """单个场景描述"""
    scene_id: str = Field(description="Scene ID (e.g., scene_1, scene_2)")
    description: str = Field(description="Detailed visual description for image generation")
    location: str = Field(description="Where the scene takes place")
    brief_content: str = Field(description="What happens in this scene in 1-2 sentences")


class GeneratedSceneDescriptions(BaseModel):
    """生成的场景描述列表"""
    scenes: List[SceneDescription] = Field(description="List of 5-8 scenes")


class GeneratedSceneDetails(BaseModel):
    """生成的单个场景详细内容"""
    scene_id: str = Field(description="Scene ID (e.g., scene_1)")
    detailed_content: str = Field(description="Detailed scene content with rich dialogues, descriptions, and character interactions (400-600 words per scene)")


class GeneratedAllScenesDetails(BaseModel):
    """生成的所有场景详细内容"""
    scenes: List[GeneratedSceneDetails] = Field(description="List of detailed scene contents, one for each scene")



class GeneratedCharactersAndScenes(BaseModel):
    """生成的角色和场景（分步处理步骤1）"""
    characters: List[dict] = Field(description="List of characters, each containing: name, role (main/supporting), description, gender (male/female/other), age_range (young/adult/elderly), personality")
    scenes: List[dict] = Field(description="List of scenes, each containing: scene_id (e.g., scene_1), description (EXTREMELY DETAILED 200-300 words for image generation), location")


class GeneratedDialogues(BaseModel):
    """生成的对话（分步处理步骤2）"""
    script_lines: List[dict] = Field(description="List of script lines (dialogues, transitions, scene_markers only), each containing: line_type (dialogue/transition/scene_marker), speaker (character name, optional), speaker_id, content, scene_id")


class GeneratedOpeningAndClosing(BaseModel):
    """生成的开场和结束（分步处理步骤3）"""
    opening: dict = Field(description="Opening script line with line_type='opening', speaker_id='NARRATOR', content, scene_id=null")
    closing: dict = Field(description="Closing script line with line_type='closing', speaker_id='NARRATOR', content, scene_id=null")

