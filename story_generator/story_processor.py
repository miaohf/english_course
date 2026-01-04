"""
故事处理器

处理故事生成、内容提取和格式化
使用 LangChain + Pydantic 实现结构化输出
"""

import os
import re
from typing import Optional

from langchain_openai import ChatOpenAI

from .schemas import StoryContent
from .story_generators import StoryGenerators
from .content_extractors import ContentExtractors
from .video_script_generator import VideoScriptGenerator
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
            enable_thinking: 是否启用 thinking 输出（None 表示使用环境变量或默认值）
                           如果为 False，会禁用 thinking 输出（可能影响推理质量）
                           如果为 True 或 None，允许模型进行推理，但只提取最终结果
        """
        # 从环境变量读取配置（使用大写环境变量名，符合最佳实践）
        self.base_url = base_url or os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("VLLM_API_KEY", "sk-placeholder")
        self.model = model or os.getenv("VLLM_MODEL", "default")
        
        # 决定是否禁用 thinking
        # 如果明确设置为 False，则禁用（可能影响推理质量，但输出更简洁）
        # 如果为 None 或 True，允许模型推理，但通过结构化输出只提取最终结果
        if enable_thinking is None:
            # 从环境变量读取，默认为 True（允许推理）
            enable_thinking = os.getenv("VLLM_ENABLE_THINKING", "true").lower() == "true"
        
        # 构建 model_kwargs
        # 只有在需要禁用 thinking 时才设置 model_kwargs
        model_kwargs = None
        if not enable_thinking:
            # 只有在明确禁用时才设置
            model_kwargs = {
                "extra_body": {"enable_thinking": False}
            }
            logger.info("Thinking output disabled (may affect reasoning quality)")
        else:
            logger.info("Thinking output enabled (reasoning content will be logged but not saved)")
        
        # 从环境变量读取 max_tokens，默认 100000（模型支持最大 1M）
        default_max_tokens = int(os.getenv("VLLM_MAX_TOKENS", "100000"))
        
        # 初始化 LangChain ChatOpenAI 客户端
        # 使用结构化输出确保只提取最终结果，即使有 thinking 也不会影响
        llm_params = {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": default_max_tokens
        }
        
        # 只有在 model_kwargs 不为 None 时才添加
        if model_kwargs:
            llm_params["model_kwargs"] = model_kwargs
        
        self.llm = ChatOpenAI(**llm_params)
        
        # 初始化各个功能模块
        self.story_generators = StoryGenerators(self.llm)
        self.content_extractors = ContentExtractors(self.llm)
        self.video_script_generator = VideoScriptGenerator(self.llm)
        
        logger.info(f"StoryProcessor initialized with model: {self.model}")
    
    def translate_topic(self, chinese_topic: str) -> str:
        """将中文主题翻译成英文"""
        return self.story_generators.translate_topic(chinese_topic)
    
    def generate_story_framework(self, topic: str, english_topic: str = None) -> str:
        """生成故事框架"""
        return self.story_generators.generate_story_framework(topic, english_topic)
    
    def refine_story(self, framework: str) -> str:
        """细化故事情节"""
        return self.story_generators.refine_story(framework)
    
    def generate_opening(self, topic: str, story_summary: str) -> str:
        """生成视频开场白"""
        return self.story_generators.generate_opening(topic, story_summary)
    
    def generate_closing(self, topic: str, story_summary: str) -> str:
        """生成视频结束语"""
        return self.story_generators.generate_closing(topic, story_summary)
    
    def generate_summary(self, topic: str, story: str) -> str:
        """生成课程总结"""
        return self.story_generators.generate_summary(topic, story)
    
    def extract_key_sentences(self, story: str):
        """提取重要句子"""
        return self.content_extractors.extract_key_sentences(story)
    
    def extract_new_words(self, story: str):
        """提取新词"""
        return self.content_extractors.extract_new_words(story)
    
    def generate_video_script(self, detailed_story: str, framework: str):
        """生成视频剧本"""
        return self.video_script_generator.generate_video_script(detailed_story, framework)
    
    def _save_progress(self, story_content: StoryContent, base_path: str, step_name: str):
        """保存生成进度（增量保存）"""
        FileOperations.save_progress(story_content, base_path, step_name)
    
    def save_story(self, story_content: StoryContent, filepath: str):
        """保存故事内容到文件"""
        FileOperations.save_story(story_content, filepath)
    
    def load_story(self, filepath: str) -> StoryContent:
        """从文件加载故事内容"""
        return FileOperations.load_story(filepath)
    
    def generate_complete_story(self, topic: str, output_dir: str = None, base_filename: str = None) -> StoryContent:
        """
        生成完整的故事内容（支持增量保存）
        
        新的三步流程：
        1. 生成故事框架
        2. 具体化整个故事情节
        3. 从完整故事中提取所有需要的内容（视频剧本，包含开场/转场/结束、角色对话、场景描述等）
        
        Args:
            topic: 场景主题（中文或英文）
            output_dir: 输出目录路径（如果提供，会在每个步骤后保存进度）
            base_filename: 基础文件名（不含扩展名，如果提供 output_dir 则需要）
            
        Returns:
            完整的故事内容对象
        """
        logger.info(f"Starting complete story generation for topic: {topic}")
        
        # 准备保存路径
        base_path = None
        if output_dir and base_filename:
            os.makedirs(output_dir, exist_ok=True)
            base_path = os.path.join(output_dir, base_filename)
        
        # 0. 翻译主题（如果是中文）
        if re.search(r'[\u4e00-\u9fff]', topic):
            english_topic = self.translate_topic(topic)
        else:
            english_topic = topic
        
        # 创建初始 StoryContent 对象
        story_content = StoryContent(
            topic=english_topic,
            story_framework="",
            detailed_story="",
            opening="",  # 将从video_script中提取
            closing="",  # 将从video_script中提取
            summary="",
            key_sentences=[],
            new_words=[],
            video_script=None
        )
        
        # 步骤1: 生成故事框架
        logger.info("Step 1/3: Generating story framework...")
        framework = self.generate_story_framework(topic, english_topic)
        story_content.story_framework = framework
        if base_path:
            self._save_progress(story_content, base_path, "framework")
        
        # 步骤2: 具体化整个故事情节
        logger.info("Step 2/3: Refining story with detailed dialogues...")
        detailed_story = self.refine_story(framework)
        story_content.detailed_story = detailed_story
        if base_path:
            self._save_progress(story_content, base_path, "detailed_story")
        
        # 步骤3: 从完整故事中提取所有需要的内容
        # 包括：开场/转场/结束、角色对话、场景描述（用于生成插图）等
        logger.info("Step 3/3: Extracting video script (opening, dialogues, transitions, closing, scene descriptions)...")
        video_script = self.generate_video_script(detailed_story, framework)
        story_content.video_script = video_script
        
        # 从视频剧本中提取开场和结束（用于向后兼容）
        if video_script and video_script.script_lines:
            for line in video_script.script_lines:
                if line.line_type == "opening" and not story_content.opening:
                    story_content.opening = line.content
                elif line.line_type == "closing" and not story_content.closing:
                    story_content.closing = line.content
        
        # 可选：生成课程总结（用于学习材料，不影响视频制作流程）
        # 如果需要，可以取消注释以下代码
        # logger.info("Generating lesson summary (optional)...")
        # summary = self.generate_summary(english_topic, detailed_story)
        # story_content.summary = summary
        
        # 可选：提取重要句子和新词（用于学习材料）
        # 如果需要，可以取消注释以下代码
        # logger.info("Extracting key sentences and new words (optional)...")
        # key_sentences = self.extract_key_sentences(detailed_story)
        # story_content.key_sentences = key_sentences
        # new_words = self.extract_new_words(detailed_story)
        # story_content.new_words = new_words
        
        if base_path:
            self._save_progress(story_content, base_path, "script")
        
        logger.info("Story generation completed successfully!")
        logger.info(f"Generated: {len(video_script.characters) if video_script else 0} characters, "
                   f"{len(video_script.scenes) if video_script else 0} scenes, "
                   f"{len(video_script.script_lines) if video_script else 0} script lines")
        return story_content

