"""
视频剧本生成模块

从详细故事中生成视频剧本
"""

import traceback
from langchain_core.prompts import ChatPromptTemplate

from .schemas import Character, Scene, ScriptLine, VideoScript
from .internal_schemas import GeneratedScript
from logger_config import get_logger

logger = get_logger()


class VideoScriptGenerator:
    """视频剧本生成器"""
    
    def __init__(self, llm):
        """
        初始化视频剧本生成器
        
        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
    
    def generate_video_script(self, detailed_story: str, framework: str) -> VideoScript:
        """
        从详细故事中生成视频剧本
        
        Args:
            detailed_story: 详细故事文本
            framework: 故事框架文本
            
        Returns:
            视频剧本对象
        """
        logger.info("<cyan>Generating video script from story</cyan>")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a video production script expert. Extract and structure a complete video script from the given story, including opening, dialogues, transitions, and closing.

CRITICAL REQUIREMENTS:
1. This is a REAL-LIFE scenario, NOT an English learning lesson. Characters have normal everyday conversations. NO references to "learning English", "practicing English", or educational content.

2. Generate video opening (at the beginning):
   - line_type: "opening"
   - speaker_id: "NARRATOR"
   - content: An engaging opening script (50-100 words) that:
     * Greets viewers warmly
     * Introduces the topic/scenario clearly
     * Sets the context for the story
     * Uses simple, clear English suitable for learners
   - scene_id: null (opening is before any scene)

3. Extract ALL characters who speak (1-2 main + supporting characters):
   - Use REAL character names from the story (e.g., Alex, Sam, Emma)
   - Each character needs: name, role (main/supporting), description (for image generation), gender (male/female/other), age_range (young/adult/elderly), personality

4. Create MULTIPLE scenes with IDs (scene_1, scene_2, scene_3, etc.):
   - IMPORTANT: For a 10-15 minute video, you MUST create 5-8 distinct scenes
   - Divide the story into natural segments based on the story's natural flow:
     * Location changes: When characters move to a different physical location
     * Visual context changes: When the setting, background, or visual elements change significantly
     * Story progression: When the conversation topic shifts or the relationship develops
     * Time progression: When there's a natural break or transition in the narrative
   - Each scene needs: scene_id, description (detailed visual description for image generation), location
   - Each scene should represent a distinct visual moment that would require a different illustration
   - Analyze the story carefully and identify natural break points where the visual representation should change
   - Scenes can contain any number of characters (no limit on participants)
   - Multiple characters can participate in the same scene
   - Monologues (1 person speaking) are allowed
   - Maintain the original chronological order of dialogues
   - Adapt scene divisions to fit the specific story context and setting

5. Extract ALL dialogues and assign to characters AND scenes:
   - line_type: "dialogue" for character speech
   - speaker: character's real name (e.g., Alex, Sam, Emma)
   - speaker_id: same as speaker name (use real character name, NOT SPEAKER0/SPEAKER1)
   - content: the actual dialogue text
   - scene_id: which scene this belongs to (CRITICAL: distribute dialogues across ALL scenes, not just one)
   - All characters can participate in dialogues within the same scene
   - Preserve the original chronological order of all dialogues
   - IMPORTANT: Dialogues must be distributed across multiple scenes based on story progression
   - When location or context changes in the story, assign dialogues to a new scene

6. Add scene transitions between scenes:
   - line_type: "transition" for scene changes
   - speaker_id: "NARRATOR"
   - content: natural transition text that explains the scene change
   - Use natural transitions appropriate to the story context (e.g., "A moment later", "They walked together", "As they settled into their seats", "Later that day", etc.)
   - Add transitions when moving from one scene to the next to help viewers understand the visual change
   - NO mention of learning English
   - Transitions should be contextually appropriate to the story setting and flow

7. Mark scene starts:
   - line_type: "scene_marker"
   - content: brief scene description that includes who is present

8. Generate video closing (at the end):
   - line_type: "closing"
   - speaker_id: "NARRATOR"
   - content: An encouraging closing script (50-100 words) that:
     * Summarizes key points from the story
     * Encourages practice and application
     * Ends with a positive, motivating message
     * Uses simple, clear English suitable for learners
   - scene_id: null (closing is after all scenes)

Output format:
- characters: Array of character objects, each with: name, role, description, gender, age_range, personality
- scenes: Array of scene objects, each with: scene_id, description, location
- script_lines: Array of script line objects in chronological order:
  * First: opening (line_type="opening")
  * Then: scene_marker, dialogues, transitions (in story order)
  * Last: closing (line_type="closing")
  Each script line has: line_type, speaker, speaker_id, content, scene_id

IMPORTANT REMINDERS:
- CRITICAL: You MUST create 5-8 distinct scenes for a complete story (10-15 minute video)
- Each scene should have a unique visual description suitable for generating different illustrations
- Dialogues MUST be distributed across multiple scenes, not all in one scene
- Analyze the story's natural flow and identify where visual breaks should occur based on the specific context
- Scenes can contain any number of characters (no limit)
- Maintain chronological order of all dialogues
- Transition text should naturally explain scene changes and be appropriate to the story's setting
- Opening and closing should be natural and engaging, not educational
- Scene descriptions should be detailed enough for image generation (include setting, characters present, mood, key visual elements)
- Adapt all scene divisions, transitions, and descriptions to fit the specific story topic and setting

Return the data in the exact structure required by the Pydantic model."""),
            ("user", "Generate a complete video script from this story. Extract ALL characters, scenes, dialogues, and create opening and closing. This is a REAL-LIFE scenario:\n\nFramework:\n{framework}\n\nDetailed Story:\n{story}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(GeneratedScript)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({
                "framework": framework,
                "story": detailed_story
            })
            
            # 记录原始结果用于调试
            logger.debug(f"Raw script generation result type: {type(result)}")
            logger.debug(f"Raw characters type: {type(result.characters)}, length: {len(result.characters) if result.characters else 0}")
            logger.debug(f"Raw scenes type: {type(result.scenes)}, length: {len(result.scenes) if result.scenes else 0}")
            logger.debug(f"Raw script_lines type: {type(result.script_lines)}, length: {len(result.script_lines) if result.script_lines else 0}")
            
            # 验证结果
            if not result.characters:
                logger.warning("Generated script has no characters")
            else:
                logger.info(f"Generated {len(result.characters)} characters")
            if not result.scenes:
                logger.warning("Generated script has no scenes")
            else:
                logger.info(f"Generated {len(result.scenes)} scenes")
            if not result.script_lines:
                logger.warning("Generated script has no script lines")
            else:
                logger.info(f"Generated {len(result.script_lines)} script lines")
            
            # 转换为 VideoScript 对象
            characters = self._convert_characters(result.characters)
            scenes = self._convert_scenes(result.scenes)
            script_lines = self._convert_script_lines(result.script_lines)
            
            if not characters or not script_lines:
                logger.error(f"Video script generation incomplete: {len(characters)} characters, {len(scenes)} scenes, {len(script_lines)} script lines")
                # 如果关键数据缺失，返回空对象
                return VideoScript(characters=[], scenes=[], script_lines=[])
            
            video_script = VideoScript(
                characters=characters,
                scenes=scenes,
                script_lines=script_lines
            )
            
            logger.info(f"<green>Video script generated: {len(characters)} characters, {len(scenes)} scenes, {len(script_lines)} script lines</green>")
            return video_script
            
        except Exception as e:
            logger.error(f"Video script generation failed: {e}")
            logger.error(traceback.format_exc())
            # 记录详细错误信息
            logger.warning("Returning empty video script due to generation failure")
            # 返回空剧本而不是 None，避免后续错误
            return VideoScript(characters=[], scenes=[], script_lines=[])
    
    def _convert_characters(self, characters_data) -> list:
        """转换角色数据为 Character 对象列表"""
        characters = []
        for idx, char in enumerate(characters_data):
            logger.debug(f"Processing character {idx}: {type(char)}, value: {char}")
            try:
                # 处理字典类型（Pydantic 可能返回 dict 或已解析的对象）
                if isinstance(char, dict):
                    char_data = {
                        "name": char.get("name", ""),
                        "role": char.get("role", "supporting"),
                        "description": char.get("description", ""),
                        "gender": char.get("gender"),
                        "age_range": char.get("age_range"),
                        "personality": char.get("personality"),
                        "tts_voice_sample": char.get("tts_voice_sample")
                    }
                else:
                    # 如果是其他类型（如 Pydantic 模型），尝试转换为字典
                    if hasattr(char, "model_dump"):
                        char_dict = char.model_dump()
                    elif hasattr(char, "dict"):
                        char_dict = char.dict()
                    else:
                        char_dict = dict(char) if hasattr(char, "__dict__") else {}
                    char_data = {
                        "name": char_dict.get("name", ""),
                        "role": char_dict.get("role", "supporting"),
                        "description": char_dict.get("description", ""),
                        "gender": char_dict.get("gender"),
                        "age_range": char_dict.get("age_range"),
                        "personality": char_dict.get("personality"),
                        "tts_voice_sample": char_dict.get("tts_voice_sample")
                    }
                
                if not char_data["name"] or not char_data["description"]:
                    logger.warning(f"Character missing required fields: {char_data}")
                    continue
                characters.append(Character(**char_data))
            except Exception as e:
                logger.error(f"Failed to create character from {char}: {e}")
                logger.debug(traceback.format_exc())
        return characters
    
    def _convert_scenes(self, scenes_data) -> list:
        """转换场景数据为 Scene 对象列表"""
        scenes = []
        for idx, scene in enumerate(scenes_data):
            logger.debug(f"Processing scene {idx}: {type(scene)}, value: {scene}")
            try:
                # 处理字典类型
                if isinstance(scene, dict):
                    scene_data = {
                        "scene_id": scene.get("scene_id", f"scene_{len(scenes) + 1}"),
                        "description": scene.get("description", ""),
                        "location": scene.get("location", ""),
                        "transition_duration": scene.get("transition_duration", 1.0)
                    }
                else:
                    # 如果是其他类型，尝试转换为字典
                    if hasattr(scene, "model_dump"):
                        scene_dict = scene.model_dump()
                    elif hasattr(scene, "dict"):
                        scene_dict = scene.dict()
                    else:
                        scene_dict = dict(scene) if hasattr(scene, "__dict__") else {}
                    scene_data = {
                        "scene_id": scene_dict.get("scene_id", f"scene_{len(scenes) + 1}"),
                        "description": scene_dict.get("description", ""),
                        "location": scene_dict.get("location", ""),
                        "transition_duration": scene_dict.get("transition_duration", 1.0)
                    }
                scenes.append(Scene(**scene_data))
            except Exception as e:
                logger.error(f"Failed to create scene from {scene}: {e}")
                logger.debug(traceback.format_exc())
        return scenes
    
    def _convert_script_lines(self, script_lines_data) -> list:
        """转换剧本行数据为 ScriptLine 对象列表"""
        script_lines = []
        for idx, line in enumerate(script_lines_data):
            logger.debug(f"Processing script line {idx}: {type(line)}, value: {line}")
            try:
                # 处理字典类型
                if isinstance(line, dict):
                    line_data = {
                        "line_type": line.get("line_type", "dialogue"),
                        "speaker": line.get("speaker"),
                        "speaker_id": line.get("speaker_id"),
                        "content": line.get("content", ""),
                        "scene_id": line.get("scene_id"),
                        "timestamp": line.get("timestamp")
                    }
                else:
                    # 如果是其他类型，尝试转换为字典
                    if hasattr(line, "model_dump"):
                        line_dict = line.model_dump()
                    elif hasattr(line, "dict"):
                        line_dict = line.dict()
                    else:
                        line_dict = dict(line) if hasattr(line, "__dict__") else {}
                    line_data = {
                        "line_type": line_dict.get("line_type", "dialogue"),
                        "speaker": line_dict.get("speaker"),
                        "speaker_id": line_dict.get("speaker_id"),
                        "content": line_dict.get("content", ""),
                        "scene_id": line_dict.get("scene_id"),
                        "timestamp": line_dict.get("timestamp")
                    }
                if not line_data["content"]:
                    logger.warning(f"Script line missing content: {line_data}")
                    continue
                script_lines.append(ScriptLine(**line_data))
            except Exception as e:
                logger.error(f"Failed to create script line from {line}: {e}")
                logger.debug(traceback.format_exc())
        return script_lines

