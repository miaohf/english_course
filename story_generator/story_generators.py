"""
故事生成模块

包含故事框架、详细故事、开场白、结束语、总结的生成方法
"""

import re
import time
from langchain_core.prompts import ChatPromptTemplate

from .internal_schemas import (
    TranslatedTopic,
    GeneratedStorySummary,
    GeneratedSceneDescriptions,
    GeneratedAllScenesDetails
)
from .prompts import (
    TRANSLATE_TOPIC_SYSTEM,
    TRANSLATE_TOPIC_USER,
    GENERATE_STORY_SUMMARY_SYSTEM,
    GENERATE_STORY_SUMMARY_USER,
    GENERATE_SCENE_DESCRIPTIONS_SYSTEM,
    GENERATE_SCENE_DESCRIPTIONS_USER,
    REFINE_SCENES_SYSTEM,
    REFINE_SCENES_USER,
)
from logger_config import get_logger

logger = get_logger()


class StoryGenerators:
    """故事生成器 - 包含所有故事生成相关方法"""
    
    def __init__(self, llm):
        """
        初始化故事生成器
        
        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
    
    def translate_topic(self, chinese_topic: str) -> str:
        """
        将中文主题翻译成英文（使用结构化输出确保结果简洁）
        
        Args:
            chinese_topic: 中文主题
            
        Returns:
            英文主题（简洁版本）
        """
        logger.info(f"Translating topic from Chinese: {chinese_topic}")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", TRANSLATE_TOPIC_SYSTEM),
            ("user", TRANSLATE_TOPIC_USER)
        ])
        
        # 使用结构化输出确保返回简洁的翻译结果
        structured_llm = self.llm.with_structured_output(TranslatedTopic)
        chain = prompt | structured_llm
        
        result = chain.invoke({"topic": chinese_topic})
        english_topic = result.english_topic.strip().strip('"').strip("'")
        
        elapsed = time.time() - start_time
        logger.info(f"Topic translated to English: {english_topic} (took {elapsed:.2f} seconds)")
        return english_topic
    
    def generate_story_summary(self, topic: str, english_topic: str = None) -> dict:
        """
        生成剧情概要（新流程步骤2）
        
        Args:
            topic: 原始主题（可能是中文）
            english_topic: 英文主题（如果已翻译）
            
        Returns:
            包含summary, characters, key_expressions的字典
        """
        if not english_topic:
            english_topic = self.translate_topic(topic) if re.search(r'[\u4e00-\u9fff]', topic) else topic
        
        logger.info(f"Generating story summary for topic: {english_topic}")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_STORY_SUMMARY_SYSTEM),
            ("user", GENERATE_STORY_SUMMARY_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedStorySummary)
        chain = prompt | structured_llm
        
        result = chain.invoke({"topic": english_topic})
        
        elapsed = time.time() - start_time
        logger.info(f"Story summary generation completed in {elapsed:.2f} seconds")
        return {
            "summary": result.summary,
            "characters": result.characters,
            "key_expressions": result.key_expressions
        }
    
    def generate_scene_descriptions(self, story_summary: dict, english_topic: str):
        """
        生成各个场景描述（新流程步骤3）
        
        Args:
            story_summary: 剧情概要字典
            english_topic: 英文主题
            
        Returns:
            GeneratedSceneDescriptions对象，包含结构化的场景描述列表
        """
        logger.info("Generating scene descriptions...")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_SCENE_DESCRIPTIONS_SYSTEM),
            ("user", GENERATE_SCENE_DESCRIPTIONS_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedSceneDescriptions)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "topic": english_topic,
            "summary": story_summary["summary"],
            "characters": story_summary["characters"]
        })
        
        elapsed = time.time() - start_time
        logger.info(f"Generated {len(result.scenes)} scene descriptions in {elapsed:.2f} seconds")
        return result
    
    def refine_scenes(self, story_summary: dict, scene_descriptions_obj, english_topic: str):
        """
        细化各场景剧情（新流程步骤4）
        
        Args:
            story_summary: 剧情概要字典
            scene_descriptions_obj: GeneratedSceneDescriptions对象，包含结构化的场景描述
            english_topic: 英文主题
            
        Returns:
            GeneratedAllScenesDetails对象，包含结构化的场景详细内容列表
        """
        logger.info(f"Refining {len(scene_descriptions_obj.scenes)} scenes with detailed content...")
        start_time = time.time()
        
        # 使用结构化数据，直接访问属性
        scenes_text = "\n\n".join([
            f"Scene {idx+1} ({scene.scene_id}):\n"
            f"Location: {scene.location}\n"
            f"Description: {scene.description}\n"
            f"Content: {scene.brief_content}"
            for idx, scene in enumerate(scene_descriptions_obj.scenes)
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", REFINE_SCENES_SYSTEM),
            ("user", REFINE_SCENES_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedAllScenesDetails)
        chain = prompt | structured_llm
        
        expressions_text = "\n".join(f"- {exp}" for exp in story_summary["key_expressions"])
        
        result = chain.invoke({
            "topic": english_topic,
            "summary": story_summary["summary"],
            "characters": story_summary["characters"],
            "expressions": expressions_text,
            "scenes": scenes_text
        })
        
        elapsed = time.time() - start_time
        logger.info(f"Generated detailed content for {len(result.scenes)} scenes in {elapsed:.2f} seconds")
        return result
    
