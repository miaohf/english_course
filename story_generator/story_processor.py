"""
故事处理器

使用 LangChain + vLLM 生成结构化故事内容
"""

import os
import json
import re
from datetime import datetime
from typing import Optional

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
        logger.info(f"Topic translated: {topic} -> {translated}")
        return translated.strip()
    
    def generate_complete_story(
        self,
        topic: str,
        output_dir: Optional[str] = None
    ) -> VideoScript:
        """生成完整故事
        
        Args:
            topic: 故事主题（中文或英文）
            output_dir: 输出目录
            
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
        
        # 生成视频剧本
        video_script = self._generate_video_script(topic_english, topic_chinese)
        
        # 添加图像提示词
        self._add_image_prompts(video_script)
        
        # 保存 script.json
        if output_dir:
            self.save_script(video_script, output_dir)
        
        logger.info(f"Story generation completed for: {topic}")
        return video_script
    
    def _generate_video_script(self, topic_english: str, topic_chinese: Optional[str] = None) -> VideoScript:
        """生成视频剧本"""
        logger.info("Generating video script...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_script_system_prompt()),
            ("human", "Generate a complete video script for the topic: {topic}")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({"topic": topic_english})
        
        content = self._clean_thinking(result.content)
        script_data = self._parse_json_response(content)
        
        try:
            video_script = self._build_video_script(script_data, topic_english, topic_chinese)
            logger.info(f"Video script generated: {len(video_script.scenes)} scenes")
            return video_script
        except Exception as e:
            logger.error(f"Failed to build video script: {e}")
            raise
    
    def _get_script_system_prompt(self) -> str:
        """获取剧本生成的系统提示词"""
        return """You are an expert English teaching content creator. Generate a complete video script for an English learning video.

## Requirements:
1. Create exactly 5 scenes with sequential IDs (scene_1 to scene_5)
2. Create 2 main characters with distinct personalities
3. Each scene should have 10-20 dialogue turns
4. Include opening and closing narration for each scene
5. Include 5-8 key expressions distributed across scenes (no repetition)
6. Visual descriptions should be 200-300 words per scene

## Output Format (JSON):
```json
{{
  "summary": "Brief story summary in English",
  "summary_chinese": "故事概要中文",
  "characters": [
    {{
      "id": "character_1",
      "name": "Emily",
      "gender": "female",
      "age_range": "25-30",
      "appearance": "Detailed appearance description...",
      "personality": "Friendly and outgoing",
      "voice_style": "Warm and cheerful"
    }}
  ],
  "scenes": [
    {{
      "scene_id": "scene_1",
      "title": "First Meeting",
      "title_chinese": "初次见面",
      "location": "Coffee shop",
      "visual_description": "Detailed visual description (200-300 words)...",
      "narration": {{
        "opening": "Opening narration in English...",
        "opening_chinese": "开场旁白中文...",
        "closing": "Closing narration in English...",
        "closing_chinese": "结束旁白中文..."
      }},
      "dialogues": [
        {{
          "id": "scene_1_001",
          "speaker": "character_1",
          "text": "Hi, is this seat taken?",
          "chinese": "你好，这个座位有人吗？",
          "emotion": "friendly"
        }}
      ],
      "key_expressions": ["Is this seat taken?"]
    }}
  ],
  "key_expressions": [
    {{
      "word": "Is this seat taken?",
      "phonetic": "/ɪz ðɪs siːt ˈteɪkən/",
      "chinese": "这个座位有人吗？",
      "example": "Excuse me, is this seat taken?"
    }}
  ]
}}
```

## Quality Guidelines:
- Dialogues should sound natural with hesitations, interruptions
- Avoid AI-like patterns: no "echo" responses, no philosophical conclusions
- Each key expression should only appear once across all scenes
- Character appearances must remain consistent across all scenes
- Visual descriptions must match dialogue content"""
    
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
        """解析 JSON 响应"""
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
    
    def _build_video_script(self, data: dict, topic_english: str, topic_chinese: Optional[str]) -> VideoScript:
        """从解析的数据构建 VideoScript 对象"""
        # 构建角色列表
        characters = []
        for char_data in data.get("characters", []):
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

