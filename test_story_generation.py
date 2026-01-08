#!/usr/bin/env python3
"""
故事生成脚本

批量生成故事内容，需要连接到 vLLM 服务
"""

import sys
import os
import argparse
from datetime import datetime
import re
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

# 配置日志
from logger_config import setup_logger, get_logger

setup_logger(
    log_level="INFO",
    log_file="story_generation.log",
    rotation="10 MB",
    retention="7 days"
)

logger = get_logger()

# 导入故事生成模块
from story_generator import StoryProcessor


def generate_story(processor, topic, use_streaming=True):
    """生成完整故事
    
    Args:
        processor: StoryProcessor 实例
        topic: 故事主题
        use_streaming: 是否使用流式生成（默认True）
    """
    # 准备输出目录
    date_str = datetime.now().strftime("%Y%m%d")
    try:
        if re.search(r'[\u4e00-\u9fff]', topic):
            temp_english_topic = processor.translate_topic(topic)
        else:
            temp_english_topic = topic
    except:
        temp_english_topic = "story"
    
    # 清理英文主题，移除特殊字符
    safe_topic = re.sub(r'[^\w\s-]', '', temp_english_topic).strip()
    safe_topic = re.sub(r'[-\s]+', '_', safe_topic)
    
    # 输出目录结构：outputs/{日期}/{english_topic}/
    output_dir = os.path.join("outputs", date_str, safe_topic)
    os.makedirs(output_dir, exist_ok=True)
    base_filename = "story"
    
    # 生成故事（直接生成结构化剧本）
    story_content = processor.generate_complete_story(
        topic,
        output_dir=output_dir,
        base_filename=base_filename,
        use_streaming=use_streaming
    )
    
    # 保存完整版本
    output_file = os.path.join(output_dir, f"{base_filename}.json")
    processor.save_story(story_content, output_file)
    logger.info(f"Story saved to: {output_file}")
    
    # 保存 TTS 格式
    if story_content.video_script:
        tts_file = os.path.join(output_dir, "tts.txt")
        tts_content = story_content.video_script.to_tts_format()
        with open(tts_file, 'w', encoding='utf-8') as f:
            f.write(tts_content)
        logger.info(f"TTS format saved to: {tts_file}")
    
    # 保存 script.json
    if story_content.video_script:
        script_file = os.path.join(output_dir, "script.json")
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(story_content.video_script.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info(f"Script saved to: {script_file}")
    
    return story_content


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
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成英语教学故事')
    parser.add_argument(
        '--topics-file',
        type=str,
        default='topics.json',
        help='主题列表 JSON 文件路径（默认: topics.json）'
    )
    parser.add_argument(
        '--no-streaming',
        action='store_true',
        help='禁用流式生成（使用一次性生成，速度快但可能有表达重复）'
    )
    args = parser.parse_args()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Story Generation")
    logger.info("=" * 60)
    logger.info("Starting story generation...")
    
    # 加载主题列表
    topics = load_topics(args.topics_file)
    if not topics:
        logger.error("No topics loaded")
        return 1
    
    # 初始化处理器
    try:
        processor = StoryProcessor()
    except Exception as e:
        logger.error(f"Failed to initialize StoryProcessor: {e}")
        return 1
    
    # 处理所有主题
    total_topics = len(topics)
    success_count = 0
    failed_topics = []
    
    for idx, topic_item in enumerate(topics, 1):
        topic_id = topic_item.get("id", idx)
        topic_scene = topic_item.get("scene", "")
        topic_description = topic_item.get("description", "")
        
        logger.info(f"Processing [{idx}/{total_topics}] {topic_scene}")
        
        try:
            # 组合主题
            if topic_description:
                topic = f"{topic_scene}：{topic_description}"
            else:
                topic = topic_scene
            
            # 生成故事
            use_streaming = not args.no_streaming
            story_content = generate_story(processor, topic, use_streaming=use_streaming)
            if story_content:
                success_count += 1
                logger.info(f"✓ Completed: {topic_scene}")
            else:
                failed_topics.append({"id": topic_id, "scene": topic_scene})
                logger.error(f"✗ Failed: {topic_scene}")
        
        except Exception as e:
            failed_topics.append({"id": topic_id, "scene": topic_scene})
            logger.error(f"✗ Error processing {topic_scene}: {e}")
            continue
    
    # 输出总结
    logger.info("")
    logger.info(f"Summary: {success_count}/{total_topics} completed")
    if failed_topics:
        logger.warning(f"Failed topics: {len(failed_topics)}")
    
    return 0 if success_count == total_topics else 1


if __name__ == "__main__":
    main()
