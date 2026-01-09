"""
故事生成数据模型
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class WordItem(BaseModel):
    """单词/短语项"""
    word: str = Field(..., description="英文单词或短语")
    phonetic: Optional[str] = Field(None, description="音标")
    chinese: Optional[str] = Field(None, description="中文释义")
    example: Optional[str] = Field(None, description="例句")


class Character(BaseModel):
    """角色定义"""
    id: str = Field(..., description="角色ID，如 character_1")
    name: str = Field(..., description="角色名称")
    gender: Literal["male", "female"] = Field(..., description="性别")
    age_range: str = Field(..., description="年龄范围，如 25-30")
    appearance: str = Field(..., description="外观描述")
    personality: Optional[str] = Field(None, description="性格特点")
    voice_style: Optional[str] = Field(None, description="语音风格描述")
    image_prompt: Optional[str] = Field(None, description="角色图像生成提示词")


class ScriptLine(BaseModel):
    """剧本台词行"""
    id: str = Field(..., description="台词ID，如 scene_1_001")
    speaker: str = Field(..., description="说话人：narrator / character_1 / character_2")
    text: str = Field(..., description="英文台词")
    chinese: Optional[str] = Field(None, description="中文翻译（可选，后期添加）")
    emotion: Optional[str] = Field(None, description="情感/语气")
    action: Optional[str] = Field(None, description="伴随动作描述")


class SceneNarration(BaseModel):
    """场景旁白"""
    opening: Optional[str] = Field(None, description="开场旁白")
    opening_chinese: Optional[str] = Field(None, description="开场旁白中文")
    closing: Optional[str] = Field(None, description="结束旁白")
    closing_chinese: Optional[str] = Field(None, description="结束旁白中文")


class Scene(BaseModel):
    """场景定义"""
    scene_id: str = Field(..., description="场景ID，如 scene_1")
    title: str = Field(..., description="场景标题")
    title_chinese: Optional[str] = Field(None, description="场景标题中文")
    location: str = Field(..., description="场景地点")
    visual_description: str = Field(..., description="视觉描述，200-300词")
    narration: Optional[SceneNarration] = Field(None, description="场景旁白")
    dialogues: List[ScriptLine] = Field(default_factory=list, description="对话列表")
    key_expressions: List[str] = Field(default_factory=list, description="本场景的关键表达")
    image_prompt: Optional[str] = Field(None, description="场景图像生成提示词")


class VideoScript(BaseModel):
    """完整视频剧本"""
    topic: str = Field(..., description="英文主题")
    topic_chinese: Optional[str] = Field(None, description="中文主题")
    summary: str = Field(..., description="故事概要")
    summary_chinese: Optional[str] = Field(None, description="故事概要中文")
    characters: List[Character] = Field(default_factory=list, description="角色列表")
    scenes: List[Scene] = Field(default_factory=list, description="场景列表")
    key_expressions: List[WordItem] = Field(default_factory=list, description="关键表达汇总")
    
    def get_character_name(self, speaker_id: str) -> str:
        """获取角色名称"""
        for char in self.characters:
            if char.id == speaker_id:
                return char.name
        return speaker_id

