"""
文件操作模块

包含故事内容的保存、加载和增量保存功能
"""

import json
import os

from .schemas import StoryContent, WordItem
from logger_config import get_logger

logger = get_logger()


class FileOperations:
    """文件操作类 - 包含所有文件相关方法"""
    
    @staticmethod
    def save_progress(story_content: StoryContent, base_path: str, step_name: str):
        """
        保存生成进度（增量保存）
        
        Args:
            story_content: 当前的故事内容对象（可能不完整）
            base_path: 基础文件路径（不含扩展名）
            step_name: 当前步骤名称
        """
        output_dir = os.path.dirname(base_path) if os.path.dirname(base_path) else "."
        
        # 如果生成了新内容，立即保存对应的 Markdown
        # 文件名不包含时间戳，使用固定的文件名
        if step_name == "framework" and story_content.story_framework:
            framework_md = os.path.join(output_dir, "story_framework.md")
            with open(framework_md, 'w', encoding='utf-8') as f:
                f.write(f"# Story Framework\n\n")
                f.write(f"**Topic:** {story_content.topic}\n\n")
                f.write(f"---\n\n")
                f.write(f"{story_content.story_framework}\n")
            logger.info(f"✓ Framework saved: {framework_md}")
        
        elif step_name == "detailed_story" and story_content.detailed_story:
            story_md = os.path.join(output_dir, "story.md")
            with open(story_md, 'w', encoding='utf-8') as f:
                f.write(f"# Detailed Story\n\n")
                f.write(f"**Topic:** {story_content.topic}\n\n")
                f.write(f"---\n\n")
                f.write(f"{story_content.detailed_story}\n")
            logger.info(f"✓ Detailed story saved: {story_md}")
        
        elif step_name == "script" and story_content.video_script:
            # 检查是否有有效的剧本数据
            if story_content.video_script.script_lines:
                script_json = os.path.join(output_dir, "script.json")
                with open(script_json, 'w', encoding='utf-8') as f:
                    script_dict = story_content.video_script.model_dump()
                    json.dump(script_dict, f, indent=2, ensure_ascii=False)
                logger.info(f"✓ Video script saved: {script_json}")
                
                tts_text = os.path.join(output_dir, "tts.txt")
                tts_content = story_content.video_script.to_tts_format()
                if tts_content.strip():
                    with open(tts_text, 'w', encoding='utf-8') as f:
                        f.write(tts_content)
                    logger.info(f"✓ TTS format saved: {tts_text}")
                else:
                    logger.warning("TTS format is empty, not saving tts.txt")
            else:
                logger.warning("Video script has no script lines, skipping script and TTS file generation")
    
    @staticmethod
    def save_story(story_content: StoryContent, filepath: str):
        """
        保存故事内容到文件
        
        同时保存 JSON 格式和 Markdown 格式文件，方便审阅
        
        Args:
            story_content: 故事内容对象
            filepath: JSON 文件保存路径
        """
        # 保存 JSON 文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(story_content.to_json())
        logger.info(f"Story content saved to: {filepath}")
        
        # 生成对应的 Markdown 文件（用于方便审阅长文本字段）
        output_dir = os.path.dirname(filepath)
        
        # 保存故事框架为 Markdown（文件名不包含时间戳）
        framework_md_path = os.path.join(output_dir, "story_framework.md")
        with open(framework_md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Story Framework\n\n")
            f.write(f"**Topic:** {story_content.topic}\n\n")
            f.write(f"---\n\n")
            f.write(f"{story_content.story_framework}\n")
        logger.info(f"Story framework saved to: {framework_md_path}")
        
        # 保存详细故事为 Markdown（文件名不包含时间戳）
        story_md_path = os.path.join(output_dir, "story.md")
        with open(story_md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Detailed Story\n\n")
            f.write(f"**Topic:** {story_content.topic}\n\n")
            f.write(f"---\n\n")
            f.write(f"{story_content.detailed_story}\n")
        logger.info(f"Detailed story saved to: {story_md_path}")
        
        # 保存视频剧本（如果存在，文件名不包含时间戳）
        if story_content.video_script and story_content.video_script.script_lines:
            # 保存剧本 JSON
            script_json_path = os.path.join(output_dir, "script.json")
            with open(script_json_path, 'w', encoding='utf-8') as f:
                script_dict = story_content.video_script.model_dump()
                json.dump(script_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Video script saved to: {script_json_path}")
            
            # 保存 TTS 格式文本
            tts_text_path = os.path.join(output_dir, "tts.txt")
            tts_content = story_content.video_script.to_tts_format()
            if tts_content.strip():
                with open(tts_text_path, 'w', encoding='utf-8') as f:
                    f.write(tts_content)
                logger.info(f"TTS format text saved to: {tts_text_path}")
            else:
                logger.warning(f"TTS format is empty, not saving tts.txt")
        else:
            logger.warning("Video script is empty or missing, skipping script and TTS file generation")
    
    @staticmethod
    def load_story(filepath: str) -> StoryContent:
        """
        从文件加载故事内容
        
        Args:
            filepath: 文件路径
            
        Returns:
            故事内容对象
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理 new_words 字段
        if 'new_words' in data and data['new_words']:
            data['new_words'] = [
                WordItem(**item) if isinstance(item, dict) else item
                for item in data['new_words']
            ]
        
        story_content = StoryContent(**data)
        logger.info(f"Story content loaded from: {filepath}")
        return story_content

