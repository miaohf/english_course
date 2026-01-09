"""
故事处理器

使用 LangChain + vLLM 生成结构化故事内容
支持三步优化法：初稿生成 → 质量审查 → 对话优化
"""

import os
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .schemas import VideoScript, Character, Scene, ScriptLine, SceneNarration, WordItem

# 获取 logger
try:
    from logger_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class StoryProcessor:
    """故事处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.api_url = os.getenv("VLLM_API_URL", "http://localhost:6801/v1")
        self.api_key = os.getenv("VLLM_API_KEY", "sk-placeholder")
        self.model = os.getenv("VLLM_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8")
        self.max_tokens = int(os.getenv("VLLM_MAX_TOKENS", "100000"))
        
        self.llm = ChatOpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0.7,
        )
        
        logger.info(f"StoryProcessor initialized with model: {self.model}")
    
    def translate_topic(self, topic: str) -> str:
        """将中文主题翻译为英文"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a translator. Translate the following Chinese topic to English. Only output the translation, nothing else."),
            ("human", "{topic}")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({"topic": topic})
        translated = self._clean_thinking(result.content)
        logger.info(f"Topic translated:\n  From: {topic}\n  To: {translated}")
        return translated.strip()
    
    def generate_complete_story(
        self,
        topic: str,
        output_dir: Optional[str] = None,
        optimize: bool = False
    ) -> VideoScript:
        """生成完整故事（分步生成）
        
        Args:
            topic: 故事主题（中文或英文）
            output_dir: 输出目录
            optimize: 是否启用额外优化（默认关闭，分步生成已包含质量控制）
            
        Returns:
            VideoScript: 视频剧本
        """
        logger.info(f"Generating story for topic: {topic}")
        
        # 检测是否为中文主题
        if re.search(r'[\u4e00-\u9fff]', topic):
            topic_english = self.translate_topic(topic)
            topic_chinese = topic
        else:
            topic_english = topic
            topic_chinese = None
        
        # 分步生成剧本（内置质量控制）
        logger.info("📝 Generating script (step-by-step)...")
        video_script = self._generate_video_script(topic_english, topic_chinese)
        
        # 额外优化（可选，一般不需要）
        if optimize:
            logger.info("🔍 Running optional quality refinement...")
            reflections = self._reflect_quality(video_script)
            video_script = self._refine_dialogues(video_script, reflections)
        
        # 添加图像提示词
        self._add_image_prompts(video_script)
        
        # 保存 script.json
        if output_dir:
            self.save_script(video_script, output_dir)
        
        logger.info(f"Story generation completed for: {topic}")
        return video_script
    
    def _generate_video_script(self, topic_english: str, topic_chinese: Optional[str] = None) -> VideoScript:
        """分步生成视频剧本"""
        logger.info("Generating video script (step-by-step)...")
        
        # Step 1: 生成故事大纲
        logger.info("  → Step 1.1: Generating story outline...")
        outline = self._generate_outline(topic_english)
        
        # Step 2: 为每个场景生成详细概要（新增）
        logger.info("  → Step 2: Generating scene summaries...")
        scenes_summaries = []
        previous_scenes_summaries = []
        
        for i, scene_outline in enumerate(outline.get("scenes", []), 1):
            logger.info(f"  → Step 2.{i}: Generating summary for scene {i}/5: {scene_outline.get('title', 'Unknown')}...")
            scene_summary = self._generate_scene_summary(
                scene_outline,
                outline.get("characters", []),
                topic_english,
                scene_number=i,
                previous_scenes_summaries=previous_scenes_summaries
            )
            scenes_summaries.append(scene_summary)
            previous_scenes_summaries.append(scene_summary)
        
        # Step 3: 基于概要逐场景生成对话
        logger.info("  → Step 3: Generating scene dialogues...")
        scenes_data = []
        
        for i, scene_summary in enumerate(scenes_summaries, 1):
            logger.info(f"  → Step 3.{i}: Generating dialogues for scene {i}/5: {scene_summary.get('title', 'Unknown')}...")
            scene_data = self._generate_scene_dialogues(
                scene_summary,
                outline.get("characters", []),
                topic_english,
                scene_number=i
            )
            scenes_data.append(scene_data)
        
        # Step 4: 生成关键表达汇总
        logger.info("  → Step 4: Generating key expressions...")
        key_expressions = self._generate_key_expressions(scenes_data)
        
        # 组装完整数据
        full_data = {
            "summary": outline.get("summary", ""),
            "characters": outline.get("characters", []),
            "scenes": scenes_data,
            "key_expressions": key_expressions
        }
        
        try:
            video_script = self._build_video_script(full_data, topic_english, topic_chinese)
            logger.info(f"Video script generated: {len(video_script.scenes)} scenes")
            return video_script
        except Exception as e:
            logger.error(f"Failed to build video script: {e}")
            raise
    
    def _generate_outline(self, topic: str) -> Dict[str, Any]:
        """生成故事大纲（角色 + 场景框架）"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_outline_prompt()),
            ("human", "Create a story outline for: {topic}")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({"topic": topic})
        content = self._clean_thinking(result.content)
        return self._parse_json_response(content)
    
    def _get_outline_prompt(self) -> str:
        """大纲生成提示词"""
        return """You are an expert English teaching content creator. Create a story OUTLINE.

## Requirements:
- 2 main characters with distinct personalities (appropriate for the topic)
- 5 scene outlines with titles, locations, and brief descriptions
- Each scene must have a UNIQUE EVENT that advances the story
- NO dialogues yet - just the framework

## CRITICAL: Story Progression Rules
1. Each scene MUST have ONE unique event that ONLY happens in that scene
2. NO repetition: If something is discovered/revealed in one scene, it cannot be "discovered" again
3. The story should progress naturally - each scene builds on previous ones
4. Events should be specific and concrete, not vague

## Output Format (JSON):
```json
{{
  "summary": "Brief story summary (2-3 sentences)",
  "characters": [
    {{
      "id": "character_1",
      "name": "...",
      "gender": "...",
      "age_range": "...",
      "appearance": "Detailed appearance (hair, clothes, accessories)...",
      "personality": "...",
      "voice_style": "..."
    }},
    {{
      "id": "character_2",
      "name": "...",
      "gender": "...",
      "age_range": "...",
      "appearance": "Detailed appearance...",
      "personality": "...",
      "voice_style": "..."
    }}
  ],
  "scenes": [
    {{
      "scene_id": "scene_1",
      "title": "Scene title",
      "location": "Specific location",
      "brief_description": "What happens in this scene",
      "unique_event": "The ONE specific thing that happens ONLY in this scene",
      "suggested_key_expression": "A useful English phrase (2-5 words)"
    }}
  ]
}}
```

## Example of Good vs Bad Unique Events:

GOOD (each scene advances story differently):
- Scene 1: Initial encounter/meeting
- Scene 2: First discovery about each other (e.g., common interest, shared goal)
- Scene 3: Deeper conversation (e.g., personal stories, opinions)
- Scene 4: A turning point or key moment (e.g., unexpected event, decision)
- Scene 5: Conclusion (e.g., farewell, future plans)

BAD (repetition - same type of event twice):
- Scene 2: "Discover X in common"
- Scene 4: "Realize they share Y" ← Same type as Scene 2, just different detail!

The KEY is: each scene should have a DIFFERENT TYPE of event, not just different details of the same event.

Keep it concise - this is just the planning phase."""
    
    def _generate_scene_summary(
        self,
        scene_outline: Dict,
        characters: List[Dict],
        topic: str,
        scene_number: int = 1,
        previous_scenes_summaries: List[Dict] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """为单个场景生成详细概要
        
        Args:
            scene_outline: 场景框架（来自大纲）
            characters: 角色列表
            topic: 主题
            scene_number: 场景编号（1-5）
            previous_scenes_summaries: 前面场景的详细概要列表
            max_retries: 最大重试次数
        """
        previous_scenes_summaries = previous_scenes_summaries or []
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_scene_summary_prompt()),
            ("human", """Topic: {topic}

Characters:
{characters}

Scene framework (Scene {scene_number} of 5):
{scene}

Previous scenes summaries:
{previous_scenes}

Generate a detailed summary for this scene.""")
        ])
        
        # 准备前面场景的概要文本
        previous_context = "None (this is the first scene)" if not previous_scenes_summaries else json.dumps(
            previous_scenes_summaries, ensure_ascii=False, indent=2
        )
        
        chain = prompt | self.llm
        
        # 带重试的生成
        last_error = None
        for attempt in range(max_retries):
            try:
                result = chain.invoke({
                    "topic": topic,
                    "characters": json.dumps(characters, ensure_ascii=False, indent=2),
                    "scene": json.dumps(scene_outline, ensure_ascii=False, indent=2),
                    "scene_number": scene_number,
                    "previous_scenes": previous_context
                })
                
                content = self._clean_thinking(result.content)
                scene_summary = self._parse_json_response(content)
                
                # 确保场景ID和基本信息正确
                scene_summary["scene_id"] = scene_outline.get("scene_id", scene_summary.get("scene_id"))
                scene_summary["title"] = scene_outline.get("title", scene_summary.get("title"))
                scene_summary["location"] = scene_outline.get("location", scene_summary.get("location"))
                
                return scene_summary
                
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parse error in scene summary (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying scene summary generation...")
        
        # 所有重试都失败，返回基本概要
        logger.error(f"Failed to generate scene summary after {max_retries} attempts, using fallback")
        return self._create_fallback_scene_summary(scene_outline, scene_number, previous_scenes_summaries)
    
    def _create_fallback_scene_summary(
        self, 
        scene_outline: Dict, 
        scene_number: int,
        previous_scenes_summaries: List[Dict]
    ) -> Dict[str, Any]:
        """创建降级的场景概要"""
        # 根据场景编号推断关系状态
        if scene_number == 1:
            status = "strangers"
            have_introduced = False
        else:
            status = "acquainted"
            have_introduced = True
        
        return {
            "scene_id": scene_outline.get("scene_id", f"scene_{scene_number}"),
            "title": scene_outline.get("title", f"Scene {scene_number}"),
            "location": scene_outline.get("location", "Unknown location"),
            "character_relationship": {
                "status": status,
                "have_introduced": have_introduced,
                "know_each_other": have_introduced,
                "relationship_note": "Fallback summary - relationship inferred from scene number"
            },
            "plot_points": [
                scene_outline.get("brief_description", "Continue the story")
            ],
            "dialogue_objectives": [
                "Advance the story naturally"
            ],
            "connection_to_previous": {
                "references": [],
                "continuation": "Continue from previous scene"
            },
            "important_info": {
                "do_not_repeat": ["introductions"] if have_introduced else [],
                "should_reference": [],
                "key_events": []
            }
        }
    
    def _get_scene_summary_prompt(self) -> str:
        """场景概要生成提示词"""
        return """You are an expert story planner. Create a DETAILED SUMMARY for a scene before writing dialogues.

## Your Task:
Analyze the scene framework and previous scenes to create a comprehensive summary that will guide dialogue generation.

## CRITICAL: Unique Event Enforcement
- The scene framework contains a "unique_event" - this is the ONE thing that should happen in THIS scene
- Check previous scenes' summaries for events that have ALREADY happened
- DO NOT repeat any event from previous scenes
- If an event already happened (e.g., "discovered same destination"), add it to "do_not_repeat"

## Output Format (JSON):
```json
{{
  "scene_id": "scene_1",
  "title": "First Meeting",
  "location": "Airport departure lounge",
  
  "unique_event": "The specific event from the framework that happens ONLY in this scene",
  
  "character_relationship": {{
    "status": "strangers",
    "have_introduced": false,
    "know_each_other": false,
    "relationship_note": "This is their first encounter"
  }},
  
  "plot_points": [
    "Main plot point 1",
    "Main plot point 2"
  ],
  
  "dialogue_objectives": [
    "What the dialogue should achieve 1",
    "What the dialogue should achieve 2"
  ],
  
  "connection_to_previous": {{
    "references": ["What to reference from previous scenes"],
    "continuation": "How this scene continues the story"
  }},
  
  "important_info": {{
    "do_not_repeat": ["List of things that already happened and should NOT be repeated"],
    "should_reference": ["List of previous events/topics to naturally reference"],
    "this_scene_event": "The unique event that happens in THIS scene"
  }}
}}
```

## Character Relationship Status Options:
- "strangers": First meeting, don't know each other
- "acquainted": Have met, know names, basic info
- "familiar": Know each other well, comfortable
- "close": Very familiar, deep connection

## Guidelines:
- For Scene 1: status is "strangers", have_introduced is false
- For Scene 2+: Infer status based on previous scenes
- Analyze what happened in previous scenes to determine relationship
- **Add ALL previous unique_events to "do_not_repeat"** - never repeat discoveries/revelations
- Be specific about what SHOULD be referenced (e.g., previous conversations, shared experiences)

## Example of do_not_repeat for Scene 4:
If previous scenes had:
- Scene 1: "First meeting"
- Scene 2: "Discovered same destination"
- Scene 3: "Shared travel stories"

Then Scene 4's do_not_repeat should include:
["introductions", "discovering same destination", "asking about travel plans"]

IMPORTANT: Output ONLY the JSON, no extra text."""
    
    def _generate_scene_dialogues(
        self, 
        scene_summary: Dict, 
        characters: List[Dict], 
        topic: str,
        scene_number: int = 1,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """基于场景概要生成对话
        
        Args:
            scene_summary: 场景详细概要（包含关系状态、情节要点等）
            characters: 角色列表
            topic: 主题
            scene_number: 场景编号（1-5）
            max_retries: 最大重试次数
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_scene_dialogue_prompt()),
            ("human", """Topic: {topic}

Characters:
{characters}

Scene summary (Scene {scene_number} of 5):
{scene_summary}

Generate natural dialogues for this scene based on the summary above.""")
        ])
        
        chain = prompt | self.llm
        
        # 带重试的生成
        last_error = None
        for attempt in range(max_retries):
            try:
                result = chain.invoke({
                    "topic": topic,
                    "characters": json.dumps(characters, ensure_ascii=False, indent=2),
                    "scene_summary": json.dumps(scene_summary, ensure_ascii=False, indent=2),
                    "scene_number": scene_number
                })
                
                content = self._clean_thinking(result.content)
                scene_data = self._parse_json_response(content)
                
                # 确保场景ID和基本信息正确（从概要中获取）
                scene_data["scene_id"] = scene_summary.get("scene_id", scene_data.get("scene_id"))
                scene_data["title"] = scene_summary.get("title", scene_data.get("title"))
                scene_data["location"] = scene_summary.get("location", scene_data.get("location"))
                
                # 修复 speaker 字段：确保使用 character_1/character_2 而不是角色名称
                scene_data = self._fix_speaker_fields(scene_data, characters)
                
                return scene_data
                
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parse error in scene dialogues (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying scene dialogues generation...")
        
        # 所有重试都失败，返回基本对话
        logger.error(f"Failed to generate scene dialogues after {max_retries} attempts, using fallback")
        return self._create_fallback_scene_dialogues(scene_summary, characters)
    
    def _create_fallback_scene_dialogues(self, scene_summary: Dict, characters: List[Dict]) -> Dict[str, Any]:
        """创建降级的场景对话"""
        scene_id = scene_summary.get("scene_id", "scene_1")
        char_names = [c.get("name", f"Character {i+1}") for i, c in enumerate(characters[:2])]
        
        return {
            "scene_id": scene_id,
            "title": scene_summary.get("title", "Scene"),
            "location": scene_summary.get("location", "Location"),
            "visual_description": f"A scene at {scene_summary.get('location', 'the location')} where {char_names[0]} and {char_names[1] if len(char_names) > 1 else 'another person'} interact.",
            "narration": {
                "opening": "The scene begins.",
                "closing": "The scene concludes."
            },
            "dialogues": [
                {
                    "id": f"{scene_id}_001",
                    "speaker": "character_1",
                    "text": "Hello there.",
                    "emotion": "neutral"
                },
                {
                    "id": f"{scene_id}_002",
                    "speaker": "character_2",
                    "text": "Hi, how are you?",
                    "emotion": "friendly"
                }
            ],
            "key_expressions": []
        }
    
    def _fix_speaker_fields(self, scene_data: Dict, characters: List[Dict]) -> Dict:
        """修复对话中的 speaker 字段，确保使用 character_1/character_2 而不是角色名称"""
        # 构建角色名称到ID的映射
        char_name_to_id = {}
        for char in characters:
            char_name = char.get("name", "")
            char_id = char.get("id", "")
            if char_name and char_id:
                char_name_to_id[char_name] = char_id
        
        # 常见的 speaker 格式映射
        speaker_aliases = {
            "char_1": "character_1",
            "char_2": "character_2",
            "char1": "character_1",
            "char2": "character_2",
            "speaker_1": "character_1",
            "speaker_2": "character_2",
            "speaker1": "character_1",
            "speaker2": "character_2",
            "person_1": "character_1",
            "person_2": "character_2",
            "person1": "character_1",
            "person2": "character_2",
        }
        
        # 修复每个对话的 speaker 字段
        fixed_count = 0
        for dialogue in scene_data.get("dialogues", []):
            speaker = dialogue.get("speaker", "")
            original_speaker = speaker
            
            # 如果是角色名称，转换为ID
            if speaker in char_name_to_id:
                dialogue["speaker"] = char_name_to_id[speaker]
                fixed_count += 1
            # 如果是常见的别名格式，转换为标准格式
            elif speaker.lower() in speaker_aliases:
                dialogue["speaker"] = speaker_aliases[speaker.lower()]
                fixed_count += 1
            # 验证是否为有效ID
            elif speaker not in ["character_1", "character_2", "narrator"]:
                # 尝试从 speaker 中提取数字来判断是哪个角色
                if "1" in speaker:
                    dialogue["speaker"] = "character_1"
                elif "2" in speaker:
                    dialogue["speaker"] = "character_2"
                else:
                    dialogue["speaker"] = "character_1"
                logger.warning(f"Mapped unknown speaker '{original_speaker}' to '{dialogue['speaker']}' in {scene_data.get('scene_id')}")
                fixed_count += 1
        
        if fixed_count > 0:
            logger.info(f"Fixed {fixed_count} speaker field(s) in {scene_data.get('scene_id')}")
        
        return scene_data
    
    def _get_scene_dialogue_prompt(self) -> str:
        """场景对话生成提示词（基于场景概要）"""
        return """You are an expert dialogue writer for English teaching videos.

## Your Task:
Write natural dialogue turns for the given scene based on the scene summary provided.

## Dialogue Count Guidelines:
- Scene 1-3 (establishing relationship): 12-15 dialogue turns
- Scene 4 (climax/key moment): 10-14 dialogue turns
- Scene 5 (resolution/parting): 10-12 dialogue turns (quality over quantity)

## CRITICAL: Follow the Scene Summary
The scene summary contains essential information:
- **Character relationship status**: Use this to determine how characters interact
  * "strangers": First meeting, formal/polite
  * "acquainted": Know names, more comfortable
  * "familiar": Know each other well, casual
  * "close": Very familiar, deep connection
- **Plot points**: Dialogue should advance these plot points
- **Dialogue objectives**: Achieve these objectives in your dialogue
- **Do NOT repeat**: Items listed in "do_not_repeat" (e.g., introductions if already done)
- **Should reference**: Items listed in "should_reference" (e.g., previous conversations)

## Opening Dialogue Guidelines:
- **Base it on the scene summary's plot points and objectives**
- Consider the character relationship status - match the tone
- Scene 1 (strangers): Appropriate first meeting dialogue for the location
- Scene 2+ (acquainted/familiar): Reference previous scenes, continue naturally
- **Be creative and context-specific** - don't use generic templates
- **DO NOT repeat** anything listed in "do_not_repeat"

## Dialogue Guidelines:
- Sound NATURAL: use contractions (I'm, don't, can't)
- Include some fillers sparingly: "um", "well", "you know" (max 3-4 total)
- Vary sentence length: mix short ("Yeah.", "Got it.") with longer responses
- Show emotions naturally: "Oh!", "Really?", "No way!"
- Avoid AI patterns: no echoing, no philosophical conclusions
- Each speaker should have a distinct voice matching their personality
- **Match the dialogue to the character relationship status** from the summary

## Output Format (JSON):
```json
{{
  "visual_description": "Detailed visual description of the scene (150-200 words)...",
  "narration": {{
    "opening": "Brief opening narration setting the scene...",
    "closing": "Brief closing narration wrapping up..."
  }},
  "dialogues": [
    {{
      "id": "scene_X_001",
      "speaker": "character_1",
      "text": "Create a context-specific opening based on the scene's location and situation",
      "emotion": "friendly"
    }},
    {{
      "id": "scene_X_002", 
      "speaker": "character_2",
      "text": "Natural response...",
      "emotion": "polite"
    }}
  ],
  "key_expressions": ["Short phrase (2-5 words)"]
}}
```

## Key Expression Guidelines:
- Must be SHORT: 2-5 words maximum
- Must be REUSABLE: common phrases that can be used in many situations
- Must be NATURAL: phrases native speakers actually use
- GOOD examples: "Small world!", "No worries", "Sounds good", "I'd love that"
- BAD examples: "shared waiting area near Gate 12" (too specific), "Let's swap tips on the best fish-and-chips spot" (too long)

IMPORTANT: 
- Output ONLY the JSON, no extra text
- Your dialogue MUST:
  * Follow the character relationship status from the summary
  * Achieve the dialogue objectives listed in the summary
  * NOT repeat anything in "do_not_repeat" from the summary
  * Reference items in "should_reference" from the summary naturally
  * Advance the plot points listed in the summary
- Use "character_1" or "character_2" for speaker (NOT character names)
- Be creative - don't use generic templates, make it specific to this scene and summary"""
    
    def _generate_key_expressions(self, scenes_data: List[Dict]) -> List[Dict]:
        """汇总并补充关键表达"""
        # 收集所有场景中的关键表达
        all_expressions = []
        for scene in scenes_data:
            for expr in scene.get("key_expressions", []):
                if isinstance(expr, str):
                    all_expressions.append(expr)
                elif isinstance(expr, dict):
                    all_expressions.append(expr.get("word", ""))
        
        # 去重并过滤低质量表达
        unique_expressions = list(dict.fromkeys(all_expressions))
        filtered_expressions = [
            expr for expr in unique_expressions 
            if self._is_valid_key_expression(expr)
        ][:8]
        
        if not filtered_expressions:
            logger.warning("No valid key expressions found, using defaults")
            return []
        
        logger.info(f"Filtered key expressions: {len(unique_expressions)} -> {len(filtered_expressions)}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an English teacher. For each expression, provide phonetic and example sentence.

## Important:
- Only process SHORT, COMMON expressions (2-6 words)
- Skip expressions that are too long or too specific
- Focus on expressions that are useful for English learners

Output JSON array:
```json
[
  {{
    "word": "Small world!",
    "phonetic": "/smɔːl wɜːld/",
    "example": "Small world! I didn't expect to meet you here."
  }}
]
```"""),
            ("human", "Expressions to process: {expressions}")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({"expressions": json.dumps(filtered_expressions)})
        content = self._clean_thinking(result.content)
        
        try:
            return self._parse_json_response(content)
        except:
            # 降级处理：返回简单格式
            return [{"word": expr, "phonetic": "", "example": expr} for expr in filtered_expressions]
    
    def _is_valid_key_expression(self, expr: str) -> bool:
        """验证关键表达是否有效"""
        if not expr or not isinstance(expr, str):
            return False
        
        words = expr.split()
        
        # 长度限制：2-6 个单词
        if len(words) < 2 or len(words) > 6:
            logger.debug(f"Rejected expression (length): {expr}")
            return False
        
        # 排除过于具体的表达（包含专有名词或数字）
        specific_patterns = [
            'Gate', 'Flight', 'Terminal', 'Lounge',  # 机场特定
            'Scene', 'scene_',  # 场景标记
        ]
        for pattern in specific_patterns:
            if pattern in expr:
                logger.debug(f"Rejected expression (specific): {expr}")
                return False
        
        # 排除过长的句子（超过40字符）
        if len(expr) > 40:
            logger.debug(f"Rejected expression (too long): {expr}")
            return False
        
        return True
    
    def _reflect_quality(self, video_script: VideoScript) -> Dict[str, Any]:
        """第二步：质量审查 - 分析对话质量并提出改进建议"""
        
        # 提取所有对话用于审查（只提取英文）
        all_dialogues = []
        for scene in video_script.scenes:
            scene_dialogues = [
                {
                    "scene": scene.title,
                    "speaker": d.speaker,
                    "text": d.text
                }
                for d in scene.dialogues
            ]
            all_dialogues.extend(scene_dialogues)
        
        dialogues_text = json.dumps(all_dialogues, ensure_ascii=False, indent=2)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_reflection_prompt()),
            ("human", "Please analyze the following English teaching dialogues:\n\n{dialogues}")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({"dialogues": dialogues_text})
        
        content = self._clean_thinking(result.content)
        
        try:
            reflections = self._parse_json_response(content)
            issues_count = len(reflections.get("issues", []))
            logger.info(f"Quality reflection completed: found {issues_count} issues to improve")
            return reflections
        except Exception as e:
            logger.warning(f"Failed to parse reflections, using default: {e}")
            return {"issues": [], "general_suggestions": []}
    
    def _get_reflection_prompt(self) -> str:
        """获取质量审查的系统提示词"""
        return """You are an expert in natural English conversation analysis. Analyze the dialogues and identify issues.

## Analysis Criteria:
1. **Naturalness**: Real conversations have hesitations, fillers, interruptions
2. **Authenticity**: Avoid AI-like patterns (echoing, perfect grammar, philosophical endings)
3. **Variety**: Different sentence structures, not just question-answer patterns
4. **Emotion**: Natural emotional responses, not robotic
5. **Flow**: Smooth topic transitions, not abrupt changes

## Common Issues to Find:
- Overly formal/polished language ("I must say...", "Indeed...")
- Echo responses (repeating what the other person just said)
- Perfect grammar where native speakers would use contractions
- Unnatural politeness levels
- Missing conversational fillers (um, well, you know, like)
- Too predictable turn-taking patterns
- Dialogue feels scripted rather than spontaneous

## Output Format (JSON):
```json
{{
  "overall_score": 70,
  "issues": [
    {{
      "scene": "scene title",
      "original_text": "original dialogue line",
      "problem": "Why this is unnatural",
      "suggestion": "More natural alternative"
    }}
  ],
  "general_suggestions": [
    "Add more filler words",
    "Use more contractions"
  ]
}}
```

Be specific and provide actionable suggestions. Focus on the most impactful issues (max 10-15)."""
    
    def _refine_dialogues(self, video_script: VideoScript, reflections: Dict[str, Any]) -> VideoScript:
        """第三步：对话优化 - 根据审查建议优化对话"""
        
        issues = reflections.get("issues", [])
        suggestions = reflections.get("general_suggestions", [])
        
        if not issues and not suggestions:
            logger.info("No issues found, skipping refinement")
            return video_script
        
        # 准备优化请求
        script_data = video_script.model_dump()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_refinement_prompt()),
            ("human", """Original script:
{script}

Issues to fix:
{issues}

General suggestions:
{suggestions}

Please refine the dialogues based on the feedback above.""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({
            "script": json.dumps(script_data, ensure_ascii=False, indent=2),
            "issues": json.dumps(issues, ensure_ascii=False, indent=2),
            "suggestions": json.dumps(suggestions, ensure_ascii=False, indent=2)
        })
        
        content = self._clean_thinking(result.content)
        
        try:
            refined_data = self._parse_json_response(content)
            refined_script = self._build_video_script(
                refined_data, 
                video_script.topic, 
                video_script.topic_chinese
            )
            logger.info("Dialogues refined successfully")
            return refined_script
        except Exception as e:
            logger.warning(f"Failed to parse refined script, using original: {e}")
            return video_script
    
    def _get_refinement_prompt(self) -> str:
        """获取对话优化的系统提示词"""
        return """You are an expert dialogue writer specializing in natural English conversation.

## Your Task:
Refine the dialogues based on the quality issues and suggestions provided.

## Refinement Guidelines:

### 1. Add Natural Elements (USE SPARINGLY - max 20-30% of lines):
   - Contractions: "I am" → "I'm", "do not" → "don't"
   - **VARY** fillers: "um", "well", "you know", "like", "I mean", "actually", "honestly"
   - Hesitations: "I... I think", "Maybe... yeah"
   - **DO NOT add the same filler to every line!**

### 2. Fix Common AI Patterns:
   - Remove echoing (don't repeat what other person said)
   - Avoid philosophical conclusions
   - Remove overly formal phrases
   - Make responses less predictable

### 3. Improve Flow:
   - Vary sentence length (short + long)
   - Add emotional reactions: "Really?", "No way!", "Hmm...", "Oh!", "Wow"
   - Include incomplete sentences where natural
   - Some lines should be SHORT and punchy: "Yeah.", "Got it.", "Makes sense."

### 4. Keep Teaching Value:
   - Preserve key expressions exactly as they are
   - Keep vocabulary level appropriate for learners
   - Maintain scene structure and character consistency

## CRITICAL RULES:
- **NO Chinese translations** - output English only
- **DO NOT overuse any single filler word** (especially "actually")
- Each filler should appear at most 2-3 times in the entire script
- Many lines should have NO fillers at all - just natural speech

## Output Format:
Return the COMPLETE refined script in JSON format.
Include ALL fields: summary, characters, scenes, key_expressions.
**DO NOT include any Chinese fields** (no chinese, no summary_chinese, no title_chinese, etc.)

```json
{{
  "summary": "...",
  "characters": [...],
  "scenes": [...],
  "key_expressions": [...]
}}
```"""
    
    def _add_image_prompts(self, video_script: VideoScript):
        """为角色和场景添加图像生成提示词"""
        logger.info("Adding image prompts...")
        
        for char in video_script.characters:
            if not char.image_prompt:
                char.image_prompt = (
                    f"Portrait of {char.name}, {char.gender}, {char.age_range} years old, "
                    f"{char.appearance}, professional photography, soft lighting"
                )
        
        char_names = ", ".join([c.name for c in video_script.characters])
        for scene in video_script.scenes:
            if not scene.image_prompt:
                scene.image_prompt = (
                    f"{scene.visual_description}, featuring {char_names}, "
                    f"cinematic composition, natural lighting, 16:9 aspect ratio"
                )
    
    def _clean_thinking(self, content: str) -> str:
        """清理模型的思考内容"""
        cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        if '</think>' in cleaned:
            parts = cleaned.split('</think>')
            cleaned = parts[-1].strip()
        
        return cleaned.strip()
    
    def _parse_json_response(self, content: str) -> dict:
        """解析 JSON 响应（带容错处理）"""
        # 提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试找到 JSON 对象或数组
            json_str = content.strip()
            # 查找第一个 { 或 [
            start_obj = json_str.find('{')
            start_arr = json_str.find('[')
            if start_obj >= 0 and (start_arr < 0 or start_obj < start_arr):
                json_str = json_str[start_obj:]
            elif start_arr >= 0:
                json_str = json_str[start_arr:]
        
        # 第一次尝试直接解析
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # 尝试修复常见问题
        json_str = self._fix_json_string(json_str)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON after fixes: {e}")
            # 显示错误位置附近的内容
            error_pos = e.pos if hasattr(e, 'pos') else 0
            start = max(0, error_pos - 50)
            end = min(len(json_str), error_pos + 50)
            logger.error(f"Error near position {error_pos}: ...{json_str[start:end]}...")
            logger.debug(f"Full JSON (first 1000 chars): {json_str[:1000]}")
            raise
    
    def _fix_json_string(self, json_str: str) -> str:
        """尝试修复常见的 JSON 格式问题"""
        # 移除尾部逗号 (trailing commas)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 移除控制字符（保留换行和制表符用于格式）
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        # 修复未转义的换行符在字符串内部
        # 将字符串内的换行替换为 \\n
        def fix_newlines_in_strings(match):
            s = match.group(0)
            # 替换字符串内的换行
            s = s.replace('\n', '\\n').replace('\r', '\\r')
            return s
        
        # 匹配 JSON 字符串（简化版）
        json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_newlines_in_strings, json_str)
        
        # 修复常见的引号问题：单引号替换为双引号（用于键名）
        # 只处理键名，不处理值
        json_str = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', json_str)
        
        # 尝试截断到最后一个完整的 } 或 ]
        last_brace = json_str.rfind('}')
        last_bracket = json_str.rfind(']')
        last_valid = max(last_brace, last_bracket)
        if last_valid > 0:
            json_str = json_str[:last_valid + 1]
        
        # 确保 JSON 对象正确闭合
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        # 添加缺失的闭合符号
        json_str = json_str + (']' * open_brackets) + ('}' * open_braces)
        
        return json_str
    
    def _build_video_script(self, data: dict, topic_english: str, topic_chinese: Optional[str]) -> VideoScript:
        """从解析的数据构建 VideoScript 对象"""
        # 构建角色列表
        characters = []
        for i, char_data in enumerate(data.get("characters", [])):
            # 规范化 gender 字段（LLM 可能返回 "Male"、"Non-binary" 等）
            if "gender" in char_data:
                gender = char_data["gender"].lower()
                # 只接受 "male" 或 "female"，其他值映射为交替的性别
                if gender not in ("male", "female"):
                    # 根据角色索引交替分配性别，保证两个角色性别不同
                    gender = "male" if i % 2 == 0 else "female"
                    logger.warning(f"Normalized invalid gender '{char_data['gender']}' to '{gender}' for character {i+1}")
                char_data["gender"] = gender
            characters.append(Character(**char_data))
        
        # 构建场景列表
        scenes = []
        for scene_data in data.get("scenes", []):
            # 构建对话列表
            dialogues = []
            for dial_data in scene_data.get("dialogues", []):
                dialogues.append(ScriptLine(**dial_data))
            
            # 构建旁白
            narration = None
            if "narration" in scene_data and scene_data["narration"]:
                narration = SceneNarration(**scene_data["narration"])
            
            # 处理 key_expressions - 可能是字符串列表或字典列表
            key_exprs = []
            for expr in scene_data.get("key_expressions", []):
                if isinstance(expr, str):
                    key_exprs.append(expr)
                elif isinstance(expr, dict) and "word" in expr:
                    key_exprs.append(expr["word"])
            
            scene = Scene(
                scene_id=scene_data["scene_id"],
                title=scene_data["title"],
                title_chinese=scene_data.get("title_chinese"),
                location=scene_data["location"],
                visual_description=scene_data["visual_description"],
                narration=narration,
                dialogues=dialogues,
                key_expressions=key_exprs
            )
            scenes.append(scene)
        
        # 构建关键表达列表
        key_expressions = []
        for expr_data in data.get("key_expressions", []):
            key_expressions.append(WordItem(**expr_data))
        
        return VideoScript(
            topic=topic_english,
            topic_chinese=topic_chinese,
            summary=data.get("summary", ""),
            summary_chinese=data.get("summary_chinese"),
            characters=characters,
            scenes=scenes,
            key_expressions=key_expressions
        )
    
    def save_script(self, video_script: VideoScript, output_dir: str):
        """保存剧本到 script.json"""
        os.makedirs(output_dir, exist_ok=True)
        
        script_file = os.path.join(output_dir, "script.json")
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(video_script.model_dump(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Script saved to: {script_file}")

