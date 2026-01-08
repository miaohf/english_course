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


class CharacterVisualSeed(BaseModel):
    """角色视觉种子"""
    character_name: str = Field(description="Character name")
    visual_prompt: str = Field(description="Fixed image prompt for this character, e.g., '30s, navy blue scrubs, messy bun, tired eyes'")


class GeneratedVisualSeeds(BaseModel):
    """生成的视觉种子列表"""
    visual_seeds: List[CharacterVisualSeed] = Field(description="List of visual seeds for all characters, extracted from Scene 1")


# ============================================================================
# 新的结构化剧本生成 Schema（直接生成对话，不需要后续提取）
# ============================================================================

class ScriptLineItem(BaseModel):
    """单个剧本行"""
    line_type: str = Field(description="Type: 'dialogue' for character speech, 'narration' for narrator/action description, 'scene_marker' for scene start")
    speaker: str = Field(default="", description="Speaker name for dialogue (e.g., 'Elena', 'Leo'). Empty for narration/scene_marker")
    content: str = Field(description="The actual text content")


class SceneWithScript(BaseModel):
    """带剧本的完整场景"""
    scene_id: str = Field(description="Scene ID (e.g., scene_1, scene_2)")
    location: str = Field(description="Where the scene takes place")
    visual_description: str = Field(description="DETAILED visual description for image generation (200-300 words): lighting, colors, character positions, expressions, clothing, atmosphere")
    script_lines: list[ScriptLineItem] = Field(description="List of script lines in chronological order. Include scene_marker at start, then mix of dialogues and narrations")


class GeneratedScenesWithScript(BaseModel):
    """生成的所有场景（带剧本）"""
    scenes: list[SceneWithScript] = Field(description="List of 5-8 complete scenes with visual descriptions and script lines")


class GeneratedCharacterInfo(BaseModel):
    """生成的角色信息"""
    name: str = Field(description="Character's full name (e.g., 'Elena Rodriguez')")
    role: str = Field(description="'main' for protagonists, 'supporting' for secondary characters")
    gender: str = Field(description="'male', 'female', or 'other'")
    age_range: str = Field(description="'child', 'young', 'adult', or 'elderly'")
    description: str = Field(description="Detailed visual description: appearance, clothing, mannerisms, expressions")
    personality: str = Field(description="Brief personality traits that affect speech style")


class GeneratedFullScript(BaseModel):
    """完整的故事剧本（一次性生成）"""
    characters: list[GeneratedCharacterInfo] = Field(description="List of all characters in the story")
    scenes: list[SceneWithScript] = Field(description="List of 5-8 complete scenes with visual descriptions and script lines")
    opening_narration: str = Field(description="Opening narration to introduce the story (2-4 sentences, natural and engaging)")
    closing_narration: str = Field(description="Closing narration to wrap up the story (2-4 sentences, subtle and non-preachy)")


# ============================================================================
# 流式生成 Schema（逐场景生成，避免表达重复）
# ============================================================================

class GeneratedSceneBrief(BaseModel):
    """场景简述（用于规划）"""
    scene_id: str = Field(description="Scene ID (e.g., scene_1, scene_2)")
    location: str = Field(description="Where the scene takes place")
    brief_content: str = Field(description="What happens in this scene in 1-2 sentences")
    target_expressions: List[str] = Field(description="1-2 key expressions to use in THIS scene ONLY")


class GeneratedScenePlan(BaseModel):
    """场景规划（分配关键表达）"""
    scenes: List[GeneratedSceneBrief] = Field(description="List of 5-8 scene briefs with assigned expressions")


class GeneratedSingleScene(BaseModel):
    """单个场景的完整内容（流式生成）"""
    scene_id: str = Field(description="Scene ID (e.g., scene_1)")
    location: str = Field(description="Where the scene takes place")
    visual_description: str = Field(description="DETAILED visual description for image generation (200-300 words)")
    script_lines: list[ScriptLineItem] = Field(description="List of script lines in chronological order")
    used_expressions: List[str] = Field(description="List of key expressions actually used in this scene")
    common_phrases_used: List[str] = Field(default=[], description="List of common phrases/responses used in this scene (e.g., 'Deal', 'Fair enough', 'No worries') for deduplication")
    scene_ending_state: str = Field(description="Brief description of how this scene ends (character positions, emotional states, ongoing topics) - used for continuity in next scene")
    scene_summary: str = Field(default="", description="Brief 1-2 sentence summary of what happened in this scene (for content deduplication)")


class GeneratedCharactersOnly(BaseModel):
    """仅生成角色信息（流式生成第一步）"""
    characters: list[GeneratedCharacterInfo] = Field(description="List of all characters in the story")


class GeneratedNarrations(BaseModel):
    """生成开场和结束旁白"""
    opening_narration: str = Field(description="Opening narration to introduce the story (2-4 sentences)")
    closing_narration: str = Field(description="Closing narration to wrap up the story (2-4 sentences, subtle)")

