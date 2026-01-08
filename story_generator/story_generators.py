"""
故事生成模块

直接生成完整的结构化剧本
支持一次性生成和流式生成两种模式
"""

import time
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate

from .internal_schemas import (
    TranslatedTopic,
    GeneratedStorySummary,
    GeneratedFullScript,
    # 流式生成相关
    GeneratedScenePlan,
    GeneratedCharactersOnly,
    GeneratedSingleScene,
    GeneratedNarrations,
    GeneratedCharacterInfo,
    SceneWithScript,
    ScriptLineItem,
)
from .prompts import (
    TRANSLATE_TOPIC_SYSTEM,
    TRANSLATE_TOPIC_USER,
    GENERATE_STORY_SUMMARY_SYSTEM,
    GENERATE_STORY_SUMMARY_USER,
    GENERATE_FULL_SCRIPT_SYSTEM,
    GENERATE_FULL_SCRIPT_USER,
    # 流式生成相关
    GENERATE_SCENE_PLAN_SYSTEM,
    GENERATE_SCENE_PLAN_USER,
    GENERATE_CHARACTERS_ONLY_SYSTEM,
    GENERATE_CHARACTERS_ONLY_USER,
    GENERATE_SINGLE_SCENE_STREAMING_SYSTEM,
    GENERATE_SINGLE_SCENE_STREAMING_USER,
    GENERATE_NARRATIONS_SYSTEM,
    GENERATE_NARRATIONS_USER,
)
from logger_config import get_logger

logger = get_logger()


class StoryGenerators:
    """故事生成器"""
    
    def __init__(self, llm):
        """初始化故事生成器"""
        self.llm = llm
    
    def translate_topic(self, chinese_topic: str) -> str:
        """将中文主题翻译成英文"""
        logger.info(f"Translating topic from Chinese: {chinese_topic}")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", TRANSLATE_TOPIC_SYSTEM),
            ("user", TRANSLATE_TOPIC_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(TranslatedTopic)
        chain = prompt | structured_llm
        
        result = chain.invoke({"topic": chinese_topic})
        english_topic = result.english_topic.strip().strip('"').strip("'")
        
        elapsed = time.time() - start_time
        logger.info(f"Topic translated to English: {english_topic} (took {elapsed:.2f} seconds)")
        return english_topic
    
    def generate_story_summary(self, topic: str, english_topic: str = None) -> dict:
        """生成剧情概要"""
        if not english_topic:
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in topic)
            english_topic = self.translate_topic(topic) if has_chinese else topic
        
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
    
    def generate_full_script(
        self,
        topic: str,
        story_summary: dict
    ) -> GeneratedFullScript:
        """
        直接生成完整的结构化剧本
        
        一次性生成完整的剧本，包括：
        - 角色定义（带详细视觉描述）
        - 场景（带视觉描述和脚本行）
        - 开场白和结束语
        
        Args:
            topic: 英文主题
            story_summary: 剧情概要字典，包含 summary, characters, key_expressions
            
        Returns:
            GeneratedFullScript 对象，包含完整的结构化剧本
        """
        logger.info("Generating full script...")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_FULL_SCRIPT_SYSTEM),
            ("user", GENERATE_FULL_SCRIPT_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedFullScript)
        chain = prompt | structured_llm
        
        expressions_text = ", ".join(story_summary.get("key_expressions", []))
        
        result = chain.invoke({
            "topic": topic,
            "summary": story_summary["summary"],
            "key_expressions": expressions_text
        })
        
        elapsed = time.time() - start_time
        
        # 统计生成结果
        total_lines = sum(len(scene.script_lines) for scene in result.scenes)
        dialogue_lines = sum(
            len([l for l in scene.script_lines if l.line_type == "dialogue"]) 
            for scene in result.scenes
        )
        
        logger.info(f"✓ Full script generated in {elapsed:.2f} seconds")
        logger.info(f"  - Characters: {len(result.characters)}")
        logger.info(f"  - Scenes: {len(result.scenes)}")
        logger.info(f"  - Total lines: {total_lines}")
        logger.info(f"  - Dialogue lines: {dialogue_lines}")
        
        return result
    
    # ========================================================================
    # 流式生成方法（逐场景生成，避免表达重复）
    # ========================================================================
    
    def generate_scene_plan(
        self,
        topic: str,
        story_summary: dict
    ) -> GeneratedScenePlan:
        """
        生成场景规划，将关键表达分配到各个场景
        
        这是流式生成的第一步，确保每个表达只被分配到一个场景
        """
        logger.info("Generating scene plan with expression distribution...")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_SCENE_PLAN_SYSTEM),
            ("user", GENERATE_SCENE_PLAN_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedScenePlan)
        chain = prompt | structured_llm
        
        expressions_text = "\n".join(f"- {exp}" for exp in story_summary.get("key_expressions", []))
        
        result = chain.invoke({
            "topic": topic,
            "summary": story_summary["summary"],
            "characters": story_summary["characters"],
            "key_expressions": expressions_text
        })
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Scene plan generated in {elapsed:.2f} seconds")
        logger.info(f"  - Scenes planned: {len(result.scenes)}")
        
        # 验证表达分配
        all_assigned = []
        for scene in result.scenes:
            all_assigned.extend(scene.target_expressions)
        logger.info(f"  - Expressions assigned: {len(all_assigned)}")
        
        return result
    
    def generate_characters_only(
        self,
        topic: str,
        story_summary: dict
    ) -> GeneratedCharactersOnly:
        """
        仅生成角色信息
        
        流式生成的第二步
        """
        logger.info("Generating character profiles...")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_CHARACTERS_ONLY_SYSTEM),
            ("user", GENERATE_CHARACTERS_ONLY_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedCharactersOnly)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "topic": topic,
            "summary": story_summary["summary"],
            "characters_description": story_summary["characters"]
        })
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Characters generated in {elapsed:.2f} seconds")
        logger.info(f"  - Characters: {len(result.characters)}")
        for char in result.characters:
            logger.info(f"    - {char.name} ({char.role}, {char.gender}, {char.age_range})")
        
        return result
    
    def generate_single_scene(
        self,
        topic: str,
        story_summary: dict,
        characters: List[GeneratedCharacterInfo],
        scene_plan: dict,
        scene_number: int,
        used_expressions: List[str],
        used_phrases: List[str],
        previous_scene_ending: str = "",
        previous_scenes_summary: str = ""
    ) -> GeneratedSingleScene:
        """
        生成单个场景
        
        流式生成的核心方法，每次只生成一个场景
        
        Args:
            topic: 主题
            story_summary: 故事概要
            characters: 角色列表
            scene_plan: 当前场景的规划（scene_id, location, brief_content, target_expressions）
            scene_number: 场景序号（1-based）
            used_expressions: 已使用的关键表达列表
            used_phrases: 已使用的常见短语列表（用于去重）
            previous_scene_ending: 上一场景的结尾状态
            previous_scenes_summary: 前面所有场景的摘要（用于内容去重）
        """
        logger.info(f"Generating scene {scene_number} ({scene_plan['scene_id']})...")
        start_time = time.time()
        
        # 格式化角色名称列表（只允许这些角色说话）
        allowed_characters = ", ".join([char.name for char in characters])
        
        # 构建 system prompt，填入已用表达、短语和目标表达
        system_prompt = GENERATE_SINGLE_SCENE_STREAMING_SYSTEM.format(
            used_expressions="\n".join(f"- {exp}" for exp in used_expressions) if used_expressions else "(None yet - this is the first scene)",
            used_phrases="\n".join(f"- {phrase}" for phrase in used_phrases) if used_phrases else "(None yet - this is the first scene)",
            target_expressions="\n".join(f"- {exp}" for exp in scene_plan.get("target_expressions", [])),
            allowed_characters=allowed_characters,
            previous_scene_ending=previous_scene_ending if previous_scene_ending else "(None - this is the first scene)",
            previous_scenes_summary=previous_scenes_summary if previous_scenes_summary else "(None - this is the first scene)"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", GENERATE_SINGLE_SCENE_STREAMING_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedSingleScene)
        chain = prompt | structured_llm
        
        # 格式化角色信息（带说明只能使用这些角色）
        characters_text = "\n".join([
            f"- {char.name} ({char.gender}, {char.age_range}): {char.personality}"
            for char in characters
        ])
        
        result = chain.invoke({
            "scene_number": scene_number,
            "scene_id": scene_plan["scene_id"],
            "topic": topic,
            "summary": story_summary["summary"],
            "characters": characters_text,
            "location": scene_plan["location"],
            "brief_content": scene_plan["brief_content"],
            "target_expressions": "\n".join(f"- {exp}" for exp in scene_plan.get("target_expressions", [])),
            "used_expressions": "\n".join(f"- {exp}" for exp in used_expressions) if used_expressions else "(None)",
            "used_phrases": "\n".join(f"- {phrase}" for phrase in used_phrases) if used_phrases else "(None)",
            "previous_scene_ending": previous_scene_ending if previous_scene_ending else "(First scene)",
            "previous_scenes_summary": previous_scenes_summary if previous_scenes_summary else "(First scene)"
        })
        
        elapsed = time.time() - start_time
        dialogue_count = len([l for l in result.script_lines if l.line_type == "dialogue"])
        
        # 强制修正 scene_id 确保连续
        expected_scene_id = f"scene_{scene_number}"
        if result.scene_id != expected_scene_id:
            logger.warning(f"Fixing scene_id in result: {result.scene_id} -> {expected_scene_id}")
            result.scene_id = expected_scene_id
        
        logger.info(f"✓ Scene {scene_number} generated in {elapsed:.2f} seconds")
        logger.info(f"  - Dialogues: {dialogue_count}")
        logger.info(f"  - Expressions used: {result.used_expressions}")
        logger.info(f"  - Common phrases used: {result.common_phrases_used}")
        
        return result
    
    def generate_narrations(
        self,
        topic: str,
        story_summary: dict,
        scenes_overview: str
    ) -> GeneratedNarrations:
        """
        生成开场和结束旁白
        
        流式生成的最后一步
        """
        logger.info("Generating opening and closing narrations...")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATE_NARRATIONS_SYSTEM),
            ("user", GENERATE_NARRATIONS_USER)
        ])
        
        structured_llm = self.llm.with_structured_output(GeneratedNarrations)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "topic": topic,
            "summary": story_summary["summary"],
            "scenes_overview": scenes_overview
        })
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Narrations generated in {elapsed:.2f} seconds")
        
        return result
    
    def generate_full_script_streaming(
        self,
        topic: str,
        story_summary: dict
    ) -> GeneratedFullScript:
        """
        流式生成完整剧本（逐场景生成）
        
        流程：
        1. 生成场景规划（分配关键表达）
        2. 生成角色信息
        3. 逐个场景生成（传入已用表达和上一场景状态）
        4. 生成开场和结束旁白
        5. 组装完整剧本
        
        优点：
        - 避免关键表达重复（显式追踪已用表达）
        - 保持场景连续性（传入上一场景结尾状态）
        - 更好的质量控制
        """
        logger.info("=" * 60)
        logger.info("Starting STREAMING script generation...")
        logger.info("=" * 60)
        total_start = time.time()
        
        # 步骤1: 生成场景规划
        logger.info("\n[Step 1/4] Generating scene plan...")
        scene_plan = self.generate_scene_plan(topic, story_summary)
        
        # 修复场景编号，确保连续（scene_1, scene_2, scene_3...）
        for i, scene in enumerate(scene_plan.scenes, 1):
            expected_id = f"scene_{i}"
            if scene.scene_id != expected_id:
                logger.warning(f"Fixing scene_id: {scene.scene_id} -> {expected_id}")
                scene.scene_id = expected_id
        
        logger.info(f"  - Scene IDs: {[s.scene_id for s in scene_plan.scenes]}")
        
        # 步骤2: 生成角色信息
        logger.info("\n[Step 2/4] Generating characters...")
        characters_result = self.generate_characters_only(topic, story_summary)
        characters = characters_result.characters
        
        # 步骤3: 逐场景生成
        logger.info(f"\n[Step 3/4] Generating {len(scene_plan.scenes)} scenes...")
        
        used_expressions: List[str] = []
        used_phrases: List[str] = []
        previous_scene_ending: str = ""
        previous_scenes_summary: str = ""
        generated_scenes: List[SceneWithScript] = []
        scene_summaries: List[str] = []
        
        for i, scene_brief in enumerate(scene_plan.scenes, 1):
            scene_dict = {
                "scene_id": scene_brief.scene_id,
                "location": scene_brief.location,
                "brief_content": scene_brief.brief_content,
                "target_expressions": scene_brief.target_expressions
            }
            
            scene_result = self.generate_single_scene(
                topic=topic,
                story_summary=story_summary,
                characters=characters,
                scene_plan=scene_dict,
                scene_number=i,
                used_expressions=used_expressions,
                used_phrases=used_phrases,
                previous_scene_ending=previous_scene_ending,
                previous_scenes_summary=previous_scenes_summary
            )
            
            # 更新已用表达
            used_expressions.extend(scene_result.used_expressions)
            
            # 更新已用短语（用于对话去重）
            used_phrases.extend(scene_result.common_phrases_used)
            
            # 更新上一场景结尾状态
            previous_scene_ending = scene_result.scene_ending_state
            
            # 更新场景摘要（用于内容去重）
            if scene_result.scene_summary:
                scene_summaries.append(f"Scene {i}: {scene_result.scene_summary}")
            previous_scenes_summary = "\n".join(scene_summaries)
            
            # 转换为 SceneWithScript
            scene_with_script = SceneWithScript(
                scene_id=scene_result.scene_id,
                location=scene_result.location,
                visual_description=scene_result.visual_description,
                script_lines=scene_result.script_lines
            )
            generated_scenes.append(scene_with_script)
        
        # 步骤4: 生成旁白
        logger.info("\n[Step 4/4] Generating narrations...")
        scenes_overview = "\n".join([
            f"- Scene {i}: {scene.location} - {scene_plan.scenes[i-1].brief_content}"
            for i, scene in enumerate(generated_scenes, 1)
        ])
        
        narrations = self.generate_narrations(topic, story_summary, scenes_overview)
        
        # 组装完整剧本
        full_script = GeneratedFullScript(
            characters=characters,
            scenes=generated_scenes,
            opening_narration=narrations.opening_narration,
            closing_narration=narrations.closing_narration
        )
        
        total_elapsed = time.time() - total_start
        
        # 统计
        total_lines = sum(len(scene.script_lines) for scene in full_script.scenes)
        dialogue_lines = sum(
            len([l for l in scene.script_lines if l.line_type == "dialogue"]) 
            for scene in full_script.scenes
        )
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✓ STREAMING generation completed in {total_elapsed:.2f} seconds")
        logger.info(f"  - Characters: {len(full_script.characters)}")
        logger.info(f"  - Scenes: {len(full_script.scenes)}")
        logger.info(f"  - Total lines: {total_lines}")
        logger.info(f"  - Dialogue lines: {dialogue_lines}")
        logger.info(f"  - Key expressions used: {len(used_expressions)}")
        logger.info(f"  - Common phrases tracked: {len(used_phrases)}")
        logger.info(f"  - Expressions list: {used_expressions}")
        logger.info(f"  - Phrases list: {used_phrases}")
        logger.info("=" * 60)
        
        return full_script
