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


def generate_story(processor, topic, optimize=True):
    """生成完整故事
    
    Args:
        processor: StoryProcessor 实例
        topic: 故事主题
        optimize: 是否启用三步优化法（初稿→审查→优化）
    """
    date_str = datetime.now().strftime("%Y%m%d")
    
    # 生成目录名：使用主题的简单哈希或清理后的文本
    # 避免重复调用 translate_topic（generate_complete_story 内部会调用）
    if re.search(r'[\u4e00-\u9fff]', topic):
        # 中文主题：使用场景名称或简单清理
        # 提取场景部分（冒号前的部分）
        scene_part = topic.split('：')[0] if '：' in topic else topic
        # 使用场景名称的拼音或直接使用，这里先用简单清理
        safe_topic = re.sub(r'[^\w\s-]', '', scene_part).strip()
        safe_topic = re.sub(r'[-\s]+', '_', safe_topic)
        if not safe_topic or len(safe_topic) < 3:
            # 如果清理后太短，使用哈希
            import hashlib
            safe_topic = hashlib.md5(topic.encode('utf-8')).hexdigest()[:12]
    else:
        # 英文主题：直接清理
        safe_topic = re.sub(r'[^\w\s-]', '', topic).strip()
        safe_topic = re.sub(r'[-\s]+', '_', safe_topic)
    
    # 限制长度
    safe_topic = safe_topic[:50] if safe_topic else "story"
    
    output_dir = os.path.join("outputs", date_str, safe_topic)
    os.makedirs(output_dir, exist_ok=True)
    
    # generate_complete_story 内部会调用 translate_topic，这里不再重复调用
    video_script = processor.generate_complete_story(
        topic,
        output_dir=output_dir,
        optimize=optimize
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
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='启用额外优化（审查+精炼，通常不需要）'
    )
    args = parser.parse_args()
    
    optimize = args.optimize
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Story Generation (Step-by-Step)")
    if optimize:
        logger.info("额外优化: 启用（审查 + 精炼）")
    else:
        logger.info("模式: 分步生成（内置质量控制）")
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
            
            video_script = generate_story(processor, topic, optimize=optimize)
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

