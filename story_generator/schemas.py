"""
Pydantic 模型定义

定义故事生成的结构化输出模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class WordItem(BaseModel):
    """单词条目模型"""
    word: str = Field(description="The English word or phrase")
    meaning: str = Field(description="Chinese meaning of the word")
    example: str = Field(description="Example sentence using the word")


class StoryFramework(BaseModel):
    """故事框架模型"""
    setting: str = Field(description="The setting/location of the story")
    characters: List[str] = Field(description="List of main characters in the story")
    plot_outline: str = Field(description="Brief outline of the story plot")
    key_expressions: List[str] = Field(description="Key English expressions to be featured")


class DetailedStory(BaseModel):
    """详细故事模型"""
    story_text: str = Field(description="The complete story text in English with dialogues")
    scene_descriptions: List[str] = Field(description="Key scene descriptions for video production")


class VideoOpening(BaseModel):
    """视频开场白模型"""
    greeting: str = Field(description="Opening greeting to viewers")
    topic_introduction: str = Field(description="Brief introduction of the lesson topic")
    learning_objectives: List[str] = Field(description="What learners will achieve")


class VideoClosing(BaseModel):
    """视频结束语模型"""
    summary_points: List[str] = Field(description="Key takeaways from the lesson")
    encouragement: str = Field(description="Encouraging message for learners")
    call_to_action: str = Field(description="What learners should do next")


class LessonSummary(BaseModel):
    """课程总结模型"""
    key_expressions: List[str] = Field(description="Important English expressions learned")
    grammar_points: List[str] = Field(description="Grammar points covered")
    vocabulary_highlights: List[str] = Field(description="Key vocabulary words")
    study_tips: List[str] = Field(description="Tips for further study")


class KeySentences(BaseModel):
    """重要句子模型"""
    sentences: List[str] = Field(description="List of key English sentences from the story")


class NewWords(BaseModel):
    """新词汇模型"""
    words: List[WordItem] = Field(description="List of new vocabulary words with meanings and examples")


class Character(BaseModel):
    """角色定义"""
    name: str = Field(description="角色名称")
    role: str = Field(description="角色类型：main（主要角色）或 supporting（配角）")
    description: str = Field(description="角色外观描述，用于生成插图和人物构图")
    gender: Optional[str] = Field(default=None, description="性别：male/female/other")
    age_range: Optional[str] = Field(default=None, description="年龄范围：young/adult/elderly")
    personality: Optional[str] = Field(default=None, description="性格特点，用于对话风格")
    tts_voice_sample: Optional[str] = Field(default=None, description="TTS 音色样本文件路径（wav 文件）")


class Scene(BaseModel):
    """场景定义"""
    scene_id: str = Field(description="场景 ID，如 scene_1, scene_2")
    description: str = Field(description="场景描述，用于生成插图")
    location: str = Field(default="", description="场景地点")
    transition_duration: float = Field(default=1.0, description="转场静默时长（秒）")


class ScriptLine(BaseModel):
    """剧本行"""
    line_type: str = Field(description="类型：opening（开场白）/dialogue（对话）/transition（转场旁白）/scene_marker（场景标记）/closing（结束语）")
    speaker: Optional[str] = Field(default=None, description="说话人名称（对话时使用）")
    speaker_id: Optional[str] = Field(default=None, description="说话人 ID，如 SPEAKER0, SPEAKER1, NARRATOR")
    content: str = Field(description="内容文本")
    scene_id: Optional[str] = Field(default=None, description="场景 ID")
    timestamp: Optional[float] = Field(default=None, description="时间戳（秒），用于视频合成")


class VideoScript(BaseModel):
    """视频剧本"""
    characters: List[Character] = Field(description="角色列表（主要角色和配角）")
    scenes: List[Scene] = Field(description="场景列表")
    script_lines: List[ScriptLine] = Field(description="剧本行列表，按顺序排列")
    
    def to_tts_format(self) -> str:
        """
        转换为 TTS 格式文本
        格式：[SPEAKER0] text, [SPEAKER1] text, [NARRATOR] text
        将角色名称映射为 SPEAKER0, SPEAKER1, SPEAKER2 等
        场景切换时添加静默标记
        """
        lines = []
        prev_scene_id = None
        
        # 建立角色名称到 SPEAKER ID 的映射
        # 按照 characters 列表的顺序分配 SPEAKER0, SPEAKER1, SPEAKER2...
        name_to_speaker = {}
        for idx, char in enumerate(self.characters):
            # 同时映射完整名称和可能的简称
            full_name = char.name
            name_to_speaker[full_name] = f"SPEAKER{idx}"
            # 如果名称包含空格，也映射第一个词（简称）
            if ' ' in full_name:
                first_name = full_name.split()[0]
                name_to_speaker[first_name] = f"SPEAKER{idx}"
            # 也映射小写版本（大小写不敏感匹配）
            name_to_speaker[full_name.lower()] = f"SPEAKER{idx}"
            if ' ' in full_name:
                name_to_speaker[first_name.lower()] = f"SPEAKER{idx}"
        
        for line in self.script_lines:
            # 检查场景切换
            if line.scene_id and line.scene_id != prev_scene_id:
                if prev_scene_id is not None:
                    # 场景切换，添加静默标记
                    lines.append("")
                    lines.append("[SILENCE]")
                    lines.append("")
                prev_scene_id = line.scene_id
            
            # 根据类型添加内容
            if line.line_type == "opening":
                # 开场白使用 NARRATOR
                lines.append(f"[NARRATOR] {line.content}")
            elif line.line_type == "dialogue":
                # 跳过没有说话人的对话行
                speaker_name = line.speaker or line.speaker_id
                if not speaker_name:
                    continue
                
                content = line.content.strip()
                if not content:
                    continue
                
                # 如果已经是 SPEAKER 格式，直接使用
                if speaker_name.startswith("SPEAKER"):
                    speaker_id = speaker_name
                else:
                    # 从映射中获取 SPEAKER ID（支持完整名称、简称、大小写不敏感）
                    speaker_id = name_to_speaker.get(speaker_name) or name_to_speaker.get(speaker_name.lower())
                    
                    # 如果仍然找不到，尝试模糊匹配（检查是否包含在角色名称中）
                    if not speaker_id:
                        for char in self.characters:
                            char_idx = self.characters.index(char)
                            # 检查 speaker_name 是否在角色名称中，或角色名称是否在 speaker_name 中
                            if (speaker_name.lower() in char.name.lower() or 
                                char.name.lower() in speaker_name.lower() or
                                speaker_name.lower() == char.name.split()[0].lower()):
                                speaker_id = f"SPEAKER{char_idx}"
                                # 缓存这个映射
                                name_to_speaker[speaker_name] = speaker_id
                                name_to_speaker[speaker_name.lower()] = speaker_id
                                break
                    
                    # 如果仍然不是 SPEAKER 格式，尝试按顺序分配
                    if not speaker_id or not speaker_id.startswith("SPEAKER"):
                        # 为未映射的角色分配新的 SPEAKER ID
                        max_idx = len(self.characters)
                        speaker_id = f"SPEAKER{max_idx}"
                        name_to_speaker[speaker_name] = speaker_id
                
                # 确保对话内容有适当的标点符号
                # 如果内容不为空且不以标点符号结尾，添加句号
                # 但保留已有的标点符号（., !, ?, ,, ...）
                if content and not content[-1] in '.!?,。，！？…':
                    # 检查是否以省略号结尾（三个点）
                    if not content.endswith('...'):
                        content = content + '.'
                
                lines.append(f"[{speaker_id}] {content}")
            elif line.line_type == "transition":
                # 转场旁白使用 NARRATOR
                lines.append(f"[NARRATOR] {line.content}")
            elif line.line_type == "scene_marker":
                # 场景标记：可以保留 [SCENE] 或者转换为旁白
                # 这里保留 [SCENE] 格式，也可以选择转换为旁白
                if line.content:
                    # 选项1：保留 [SCENE] 格式
                    lines.append(f"[SCENE] {line.content}")
                    # 选项2：转换为旁白（如果需要，可以取消注释下面这行，并注释上面这行）
                    # lines.append(f"[NARRATOR] {line.content}")
            elif line.line_type == "closing":
                # 结束语使用 NARRATOR
                lines.append(f"[NARRATOR] {line.content}")
        
        return "\n".join(lines)


class StoryContent(BaseModel):
    """完整故事内容模型 - 最终输出格式"""
    topic: str = Field(description="The topic/theme of the story in English")
    story_framework: str = Field(description="Story framework text")
    detailed_story: str = Field(description="Complete detailed story in English")
    opening: str = Field(description="Video opening script in English")
    closing: str = Field(description="Video closing script in English")
    summary: str = Field(description="Lesson summary in English")
    key_sentences: List[str] = Field(description="Key English sentences from the story")
    new_words: List[WordItem] = Field(default_factory=list, description="New vocabulary words")
    video_script: Optional[VideoScript] = Field(default=None, description="视频剧本（包含角色、场景、对话）")
    metadata: Optional[dict] = Field(default_factory=dict, description="元数据，包含视觉种子等信息")
    
    def to_dict_clean(self) -> dict:
        """
        转换为字典，用于保存到 JSON（不包含 thinking 内容）
        """
        return self.model_dump()
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        import json
        return json.dumps(self.to_dict_clean(), indent=indent, ensure_ascii=False)

