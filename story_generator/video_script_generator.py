"""
视频剧本生成模块

从详细故事中生成视频剧本
"""

import time
import traceback
from langchain_core.prompts import ChatPromptTemplate

from .schemas import Character, Scene, ScriptLine, VideoScript
from .internal_schemas import (
    GeneratedCharactersAndScenes,
    GeneratedDialogues,
    GeneratedOpeningAndClosing
)
from .prompts import (
    GENERATE_CHARACTERS_AND_SCENES_SYSTEM,
    GENERATE_CHARACTERS_AND_SCENES_USER,
    GENERATE_DIALOGUES_SYSTEM,
    GENERATE_DIALOGUES_USER,
    GENERATE_OPENING_CLOSING_SYSTEM,
    GENERATE_OPENING_CLOSING_USER,
)
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
    
    def generate_video_script(self, detailed_story: str = None, framework: str = None, scene_details: list = None, story_summary: dict = None) -> VideoScript:
        """
        从详细故事或场景内容中生成视频剧本（使用分步处理，更快）
        
        Args:
            detailed_story: 详细故事文本（旧方式，向后兼容）
            framework: 故事框架文本（旧方式，向后兼容）
            scene_details: 场景详细内容列表（新方式），每个元素包含scene_id和detailed_content
            story_summary: 剧情概要字典（新方式），包含summary, characters, key_expressions
            
        Returns:
            视频剧本对象
        """
        return self._generate_video_script_stepwise(detailed_story, framework, scene_details, story_summary)
    
    def _generate_video_script_stepwise(self, detailed_story: str = None, framework: str = None, scene_details: list = None, story_summary: dict = None) -> VideoScript:
        """分步生成视频剧本（新方式，更快）"""
        logger.info("<cyan>Generating video script (stepwise mode - faster)</cyan>")
        total_start_time = time.time()
        
        try:
            # 准备内容
            if scene_details and story_summary:
                scenes_text = "\n\n".join([
                    f"=== {scene.scene_id} ===\n{scene.detailed_content}"
                    for scene in scene_details.scenes
                ])
                story_content = f"""Story Summary:
{story_summary['summary']}

Characters:
{story_summary['characters']}

Detailed Scene Contents:
{scenes_text}"""
            else:
                story_content = f"Framework:\n{framework}\n\nDetailed Story:\n{detailed_story}"
            
            # 步骤1：提取角色和场景
            logger.info("Step 1/3: Extracting characters and scenes...")
            step_start = time.time()
            prompt1 = ChatPromptTemplate.from_messages([
                ("system", GENERATE_CHARACTERS_AND_SCENES_SYSTEM),
                ("user", GENERATE_CHARACTERS_AND_SCENES_USER)
            ])
            structured_llm1 = self.llm.with_structured_output(GeneratedCharactersAndScenes)
            chain1 = prompt1 | structured_llm1
            result1 = chain1.invoke({"content": story_content})
            step_elapsed = time.time() - step_start
            logger.info(f"<green>✓ Characters and scenes extracted in {step_elapsed:.2f} seconds</green>")
            logger.info(f"  - {len(result1.characters)} characters, {len(result1.scenes)} scenes")
            
            # 步骤2：提取对话、转场和场景标记
            logger.info("Step 2/3: Extracting dialogues, transitions, and scene markers...")
            step_start = time.time()
            # 准备场景信息（包含完整描述，用于对话分配）
            scenes_info = "\n".join([
                f"Scene {idx+1} ({scene.get('scene_id', '')}):\n"
                f"Location: {scene.get('location', '')}\n"
                f"Description: {scene.get('description', '')}"
                for idx, scene in enumerate(result1.scenes)
            ])
            prompt2 = ChatPromptTemplate.from_messages([
                ("system", GENERATE_DIALOGUES_SYSTEM),
                ("user", GENERATE_DIALOGUES_USER)
            ])
            structured_llm2 = self.llm.with_structured_output(GeneratedDialogues)
            chain2 = prompt2 | structured_llm2
            result2 = chain2.invoke({
                "summary": story_summary['summary'] if story_summary else "",
                "characters": story_summary['characters'] if story_summary else "",
                "scenes": scenes_info,
                "scene_contents": story_content
            })
            step_elapsed = time.time() - step_start
            logger.info(f"<green>✓ Dialogues extracted in {step_elapsed:.2f} seconds</green>")
            logger.info(f"  - {len(result2.script_lines)} script lines")
            
            # 验证对话完整性
            self._validate_dialogue_completeness(result2.script_lines, story_content, result1.scenes)
            
            # 步骤3：生成开场和结束
            logger.info("Step 3/3: Generating opening and closing...")
            step_start = time.time()
            prompt3 = ChatPromptTemplate.from_messages([
                ("system", GENERATE_OPENING_CLOSING_SYSTEM),
                ("user", GENERATE_OPENING_CLOSING_USER)
            ])
            structured_llm3 = self.llm.with_structured_output(GeneratedOpeningAndClosing)
            chain3 = prompt3 | structured_llm3
            topic = story_summary.get('summary', '')[:100] if story_summary else ""
            result3 = chain3.invoke({
                "topic": topic,
                "summary": story_summary['summary'] if story_summary else ""
            })
            step_elapsed = time.time() - step_start
            logger.info(f"<green>✓ Opening and closing generated in {step_elapsed:.2f} seconds</green>")
            
            # 合并结果
            all_script_lines = []
            # 添加开场
            if result3.opening:
                all_script_lines.append(result3.opening)
            # 添加对话、转场和场景标记（按时间顺序）
            all_script_lines.extend(result2.script_lines)
            # 添加结束
            if result3.closing:
                all_script_lines.append(result3.closing)
            
            # 转换为 VideoScript 对象
            characters = self._convert_characters(result1.characters)
            scenes = self._convert_scenes(result1.scenes)
            script_lines = self._convert_script_lines(all_script_lines)
            
            video_script = VideoScript(
                characters=characters,
                scenes=scenes,
                script_lines=script_lines
            )
            
            total_elapsed = time.time() - total_start_time
            logger.info(f"<green>Video script generated (stepwise) in {total_elapsed:.2f} seconds: {len(characters)} characters, {len(scenes)} scenes, {len(script_lines)} script lines</green>")
            return video_script
            
        except Exception as e:
            total_elapsed = time.time() - total_start_time
            logger.error(f"Video script generation (stepwise) failed after {total_elapsed:.2f} seconds: {e}")
            logger.error(traceback.format_exc())
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
    
    def _validate_dialogue_completeness(self, script_lines: list, story_content: str, scenes: list):
        """
        验证对话提取的完整性
        
        Args:
            script_lines: 提取的剧本行列表
            story_content: 原始故事内容
            scenes: 场景列表
        """
        try:
            # 统计每个场景的对话数量
            scene_dialogue_count = {}
            dialogue_count = 0
            short_dialogues = []  # 短对话（可能被遗漏的反应词）
            
            for line in script_lines:
                if isinstance(line, dict):
                    line_type = line.get('line_type', '')
                    scene_id = line.get('scene_id', 'unknown')
                    content = line.get('content', '')
                else:
                    # 如果是对象，尝试获取属性
                    line_type = getattr(line, 'line_type', '')
                    scene_id = getattr(line, 'scene_id', 'unknown')
                    content = getattr(line, 'content', '')
                
                if line_type == 'dialogue':
                    dialogue_count += 1
                    if scene_id:
                        scene_dialogue_count[scene_id] = scene_dialogue_count.get(scene_id, 0) + 1
                    
                    # 检查短对话（可能是反应词）
                    if content and len(content.strip()) <= 10:
                        short_dialogues.append(content.strip())
            
            # 统计场景数量
            scene_count = len(scenes) if scenes else 0
            
            # 输出验证信息
            logger.info(f"<cyan>Dialogue completeness validation:</cyan>")
            logger.info(f"  - Total dialogues extracted: {dialogue_count}")
            logger.info(f"  - Total scenes: {scene_count}")
            logger.info(f"  - Dialogues per scene: {dict(scene_dialogue_count)}")
            
            # 检查是否有场景缺少对话
            scenes_with_dialogues = set(scene_dialogue_count.keys())
            if scene_count > 0:
                expected_scenes = {f"scene_{i+1}" for i in range(scene_count)}
                missing_scenes = expected_scenes - scenes_with_dialogues
                if missing_scenes:
                    logger.warning(f"  - ⚠️ Scenes without dialogues: {missing_scenes}")
                else:
                    logger.info(f"  - ✓ All scenes have dialogues")
            
            # 检查短对话（反应词）
            if short_dialogues:
                logger.info(f"  - Short dialogues/reactions found: {len(short_dialogues)}")
                logger.debug(f"    Examples: {short_dialogues[:5]}")
            
            # 基本完整性检查
            if dialogue_count == 0:
                logger.warning("  - ⚠️ WARNING: No dialogues extracted!")
            elif dialogue_count < scene_count * 2:
                logger.warning(f"  - ⚠️ WARNING: Very few dialogues ({dialogue_count}) for {scene_count} scenes. Expected at least {scene_count * 2} dialogues.")
            else:
                logger.info(f"  - ✓ Dialogue count looks reasonable")
            
            # 检查故事内容中是否包含对话标记（引号）
            quote_count = story_content.count("'") + story_content.count('"')
            if quote_count > 0 and dialogue_count < quote_count / 4:
                logger.warning(f"  - ⚠️ WARNING: Story contains {quote_count} quote marks but only {dialogue_count} dialogues extracted. Some dialogues may be missing.")
            
        except Exception as e:
            logger.warning(f"Dialogue validation failed: {e}")
            logger.debug(traceback.format_exc())

