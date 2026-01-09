#!/usr/bin/env python3
"""
故事生成测试脚本
"""

import sys
import os
import argparse
from datetime import datetime
import re
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

from logger_config import setup_logger, get_logger

setup_logger(
    log_level="INFO",
    log_file="story_generation.log",
    rotation="10 MB",
    retention="7 days"
)

logger = get_logger()

from story_generator import StoryProcessor


def generate_story(processor, topic):
    """生成完整故事"""
    date_str = datetime.now().strftime("%Y%m%d")
    try:
        if re.search(r'[\u4e00-\u9fff]', topic):
            temp_english_topic = processor.translate_topic(topic)
        else:
            temp_english_topic = topic
    except:
        temp_english_topic = "story"
    
    # 清理英文主题，限制长度
    safe_topic = re.sub(r'[^\w\s-]', '', temp_english_topic).strip()
    safe_topic = re.sub(r'[-\s]+', '_', safe_topic)
    safe_topic = safe_topic[:50]
    
    output_dir = os.path.join("outputs", date_str, safe_topic)
    os.makedirs(output_dir, exist_ok=True)
    
    video_script = processor.generate_complete_story(
        topic,
        output_dir=output_dir
    )
    
    return video_script


def load_topics(json_file="topics.json"):
    """从 JSON 文件加载主题列表"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        return topics
    except Exception as e:
        logger.error(f"Error loading topics: {e}")
        return []


def main():
    """主流程"""
    parser = argparse.ArgumentParser(description='生成英语教学故事')
    parser.add_argument(
        '--topics-file',
        type=str,
        default='topics.json',
        help='主题列表 JSON 文件路径'
    )
    args = parser.parse_args()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Story Generation")
    logger.info("=" * 60)
    
    topics = load_topics(args.topics_file)
    if not topics:
        logger.error("No topics loaded")
        return 1
    
    try:
        processor = StoryProcessor()
    except Exception as e:
        logger.error(f"Failed to initialize StoryProcessor: {e}")
        return 1
    
    total_topics = len(topics)
    success_count = 0
    
    for idx, topic_item in enumerate(topics, 1):
        topic_scene = topic_item.get("scene", "")
        topic_description = topic_item.get("description", "")
        
        logger.info(f"Processing [{idx}/{total_topics}] {topic_scene}")
        
        try:
            if topic_description:
                topic = f"{topic_scene}：{topic_description}"
            else:
                topic = topic_scene
            
            video_script = generate_story(processor, topic)
            if video_script:
                success_count += 1
                logger.info(f"✓ Completed: {topic_scene}")
            else:
                logger.error(f"✗ Failed: {topic_scene}")
        
        except Exception as e:
            logger.error(f"✗ Error processing {topic_scene}: {e}")
            continue
    
    logger.info("")
    logger.info(f"Summary: {success_count}/{total_topics} completed")
    
    return 0 if success_count == total_topics else 1


if __name__ == "__main__":
    main()

