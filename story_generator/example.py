"""
story_generator 使用示例
"""

import logging
from story_processor import StoryProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """示例：生成完整的故事内容"""
    
    # 初始化故事处理器
    # 默认连接到 http://localhost:8000/v1
    processor = StoryProcessor()
    
    # 或者指定自定义的 vLLM 服务地址
    # processor = StoryProcessor(base_url="http://your-vllm-server:8000/v1")
    
    # 测试连接
    if not processor.vllm_client.test_connection():
        print("无法连接到 vLLM 服务，请检查服务是否运行")
        return
    
    # 输入场景主题
    topic = "在咖啡店点餐"
    
    print(f"开始生成故事内容，主题: {topic}\n")
    
    # 生成完整的故事内容
    story_content = processor.generate_complete_story(topic)
    
    # 输出结果
    print("=" * 60)
    print("生成的故事内容")
    print("=" * 60)
    print(f"\n主题: {story_content.topic}")
    print(f"\n开场白:\n{story_content.opening}")
    print(f"\n完整故事:\n{story_content.detailed_story}")
    print(f"\n结束语:\n{story_content.closing}")
    print(f"\n课程总结:\n{story_content.summary}")
    print(f"\n重要句子:")
    for i, sentence in enumerate(story_content.key_sentences, 1):
        print(f"  {i}. {sentence}")
    print(f"\n新词:")
    for word_item in story_content.new_words:
        print(f"  - {word_item['word']}: {word_item['meaning']}")
        print(f"    例句: {word_item['example']}")
    
    # 保存到文件
    output_file = f"story_{topic.replace(' ', '_')}.json"
    processor.save_story(story_content, output_file)
    print(f"\n故事内容已保存到: {output_file}")
    
    # 也可以单独调用各个方法
    print("\n" + "=" * 60)
    print("单独调用示例")
    print("=" * 60)
    
    # 只生成故事框架
    framework = processor.generate_story_framework("机场办理登机手续")
    print(f"\n故事框架:\n{framework}")


if __name__ == "__main__":
    main()

