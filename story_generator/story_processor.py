"""
故事处理器

处理故事生成、内容提取和格式化
使用 LangChain + Pydantic 实现结构化输出
"""

import os
import json
from typing import Optional

from langchain_openai import ChatOpenAI

from .schemas import StoryContent, VideoScript, Character, Scene, ScriptLine
from .story_generators import StoryGenerators
from .file_operations import FileOperations
from logger_config import get_logger

logger = get_logger()


class StoryProcessor:
    """故事处理器 - 使用 LangChain 结构化输出"""
    
    def __init__(
        self,
        vllm_client=None,  # 保留兼容性，但不再使用
        base_url: str = None,
        api_key: str = None,
        model: str = None,
        enable_thinking: bool = None
    ):
        """
        初始化故事处理器
        
        Args:
            vllm_client: 兼容旧接口，不再使用
            base_url: vLLM 服务的基础 URL
            api_key: API 密钥
            model: 模型名称
            enable_thinking: 是否启用 thinking 输出
        """
        # 从环境变量读取配置
        self.base_url = base_url or os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("VLLM_API_KEY", "sk-placeholder")
        self.model = model or os.getenv("VLLM_MODEL", "default")
        
        if enable_thinking is None:
            enable_thinking = os.getenv("VLLM_ENABLE_THINKING", "true").lower() == "true"
        
        model_kwargs = None
        if not enable_thinking:
            model_kwargs = {"extra_body": {"enable_thinking": False}}
            logger.info("Thinking output disabled")
        
        default_max_tokens = int(os.getenv("VLLM_MAX_TOKENS", "100000"))
        
        llm_params = {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": default_max_tokens
        }
        
        if model_kwargs:
            llm_params["model_kwargs"] = model_kwargs
        
        self.llm = ChatOpenAI(**llm_params)
        
        # 初始化故事生成模块
        self.story_generators = StoryGenerators(self.llm)
        
        logger.info(f"StoryProcessor initialized with model: {self.model}")
    
    def translate_topic(self, chinese_topic: str) -> str:
        """将中文主题翻译成英文"""
        return self.story_generators.translate_topic(chinese_topic)
    
    def _save_progress(self, story_content: StoryContent, base_path: str, step_name: str):
        """保存生成进度（增量保存）"""
        FileOperations.save_progress(story_content, base_path, step_name)
    
    def save_story(self, story_content: StoryContent, filepath: str):
        """保存故事内容到文件"""
        FileOperations.save_story(story_content, filepath)
    
    def load_story(self, filepath: str) -> StoryContent:
        """从文件加载故事内容"""
        return FileOperations.load_story(filepath)
    
    def generate_complete_story(
        self, 
        topic: str, 
        output_dir: str = None, 
        base_filename: str = None,
        use_streaming: bool = True
    ) -> StoryContent:
        """
        生成完整的故事和剧本
        
        流程：
        1. 翻译主题（如果是中文）
        2. 生成剧情概要
        3. 生成完整剧本（两种模式）
           - 流式生成（推荐）：逐场景生成，避免表达重复
           - 一次性生成：快速但可能有表达重复问题
        
        Args:
            topic: 场景主题（中文或英文）
            output_dir: 输出目录路径
            base_filename: 基础文件名
            use_streaming: 是否使用流式生成（默认True，推荐）
                - True: 逐场景生成，每个场景传入已用表达，避免重复
                - False: 一次性生成，速度快但可能有表达重复
            
        Returns:
            完整的故事内容对象
        """
        mode_str = "STREAMING" if use_streaming else "ONE-SHOT"
        logger.info(f"Starting story generation for topic: {topic} (Mode: {mode_str})")
        
        # 准备保存路径
        base_path = None
        if output_dir and base_filename:
            os.makedirs(output_dir, exist_ok=True)
            base_path = os.path.join(output_dir, base_filename)
        
        self._current_output_dir = output_dir if output_dir else None
        
        # 步骤1: 翻译主题（如果是中文）
        logger.info("Step 1/3: Translating topic...")
        if any('\u4e00' <= c <= '\u9fff' for c in topic):
            english_topic = self.translate_topic(topic)
        else:
            english_topic = topic
        
        # 创建初始 StoryContent 对象
        story_content = StoryContent(
            topic=english_topic,
            story_framework="",
            detailed_story="",
            opening="",
            closing="",
            summary="",
            key_sentences=[],
            new_words=[],
            video_script=None
        )
        
        # 步骤2: 生成剧情概要
        logger.info("Step 2/3: Generating story summary...")
        story_summary = self.story_generators.generate_story_summary(topic, english_topic)
        
        story_content.story_framework = f"""Summary: {story_summary['summary']}

Characters: {story_summary['characters']}

Key Expressions:
{chr(10).join(f"- {exp}" for exp in story_summary['key_expressions'])}"""
        story_content.summary = story_summary['summary']
        
        if base_path:
            self._save_progress(story_content, base_path, "summary")
        
        # 步骤3: 生成完整剧本
        if use_streaming:
            logger.info("Step 3/3: Generating complete script (STREAMING mode)...")
            full_script = self.story_generators.generate_full_script_streaming(
                topic=english_topic,
                story_summary=story_summary
            )
        else:
            logger.info("Step 3/3: Generating complete script (ONE-SHOT mode)...")
            full_script = self.story_generators.generate_full_script(
                topic=english_topic,
                story_summary=story_summary
            )
        
        # 转换为 VideoScript 格式
        video_script = self._convert_full_script_to_video_script(full_script)
        story_content.video_script = video_script
        
        # 设置开场和结束
        story_content.opening = full_script.opening_narration
        story_content.closing = full_script.closing_narration
        
        # 合并场景内容为 detailed_story（向后兼容）
        detailed_parts = []
        for scene in full_script.scenes:
            scene_text = f"=== {scene.scene_id} ===\n"
            scene_text += f"Location: {scene.location}\n\n"
            for line in scene.script_lines:
                if line.line_type == "dialogue":
                    scene_text += f'{line.speaker}: "{line.content}"\n'
                elif line.line_type == "narration":
                    scene_text += f"({line.content})\n"
            detailed_parts.append(scene_text)
        story_content.detailed_story = "\n\n".join(detailed_parts)
        
        # 保存视觉种子
        if self._current_output_dir:
            visual_seeds = {}
            for char in full_script.characters:
                visual_seeds[char.name] = char.description
            
            if story_content.metadata is None:
                story_content.metadata = {}
            story_content.metadata['visual_seeds'] = visual_seeds
            
            visual_seeds_file = os.path.join(self._current_output_dir, "visual_seeds.json")
            try:
                with open(visual_seeds_file, 'w', encoding='utf-8') as f:
                    json.dump(visual_seeds, f, ensure_ascii=False, indent=2)
                logger.info(f"Visual seeds saved to: {visual_seeds_file}")
            except Exception as e:
                logger.error(f"Failed to save visual seeds: {e}")
        
        if base_path:
            self._save_progress(story_content, base_path, "script")
        
        # 统计结果
        total_lines = len(video_script.script_lines) if video_script else 0
        dialogue_lines = len([l for l in video_script.script_lines if l.line_type == "dialogue"]) if video_script else 0
        
        logger.info("Story generation completed successfully!")
        logger.info(f"Generated: {len(video_script.characters) if video_script else 0} characters, "
                   f"{len(video_script.scenes) if video_script else 0} scenes, "
                   f"{total_lines} script lines ({dialogue_lines} dialogues)")
        
        return story_content
    
    def _convert_full_script_to_video_script(self, full_script) -> VideoScript:
        """
        将 GeneratedFullScript 转换为 VideoScript 格式
        """
        # 转换角色
        characters = []
        for char in full_script.characters:
            characters.append(Character(
                name=char.name,
                role=char.role,
                description=char.description,
                gender=char.gender,
                age_range=char.age_range,
                personality=char.personality
            ))
        
        # 转换场景
        scenes = []
        for scene in full_script.scenes:
            scenes.append(Scene(
                scene_id=scene.scene_id,
                description=scene.visual_description,
                location=scene.location
            ))
        
        # 转换剧本行
        script_lines = []
        
        # 添加开场白
        script_lines.append(ScriptLine(
            line_type="opening",
            speaker=None,
            speaker_id="NARRATOR",
            content=full_script.opening_narration
        ))
        
        # 转换每个场景的脚本行
        for scene in full_script.scenes:
            for line in scene.script_lines:
                if line.line_type == "scene_marker":
                    script_lines.append(ScriptLine(
                        line_type="scene_marker",
                        speaker=None,
                        speaker_id=None,
                        content=line.content,
                        scene_id=scene.scene_id
                    ))
                elif line.line_type == "dialogue":
                    script_lines.append(ScriptLine(
                        line_type="dialogue",
                        speaker=line.speaker,
                        speaker_id=line.speaker,
                        content=line.content,
                        scene_id=scene.scene_id
                    ))
                elif line.line_type == "narration":
                    script_lines.append(ScriptLine(
                        line_type="transition",
                        speaker=None,
                        speaker_id="NARRATOR",
                        content=line.content,
                        scene_id=scene.scene_id
                    ))
        
        # 添加结束语
        script_lines.append(ScriptLine(
            line_type="closing",
            speaker=None,
            speaker_id="NARRATOR",
            content=full_script.closing_narration
        ))
        
        return VideoScript(
            characters=characters,
            scenes=scenes,
            script_lines=script_lines
        )
