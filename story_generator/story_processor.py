"""
故事处理器

处理故事生成、内容提取和格式化
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

from .vllm_client import VLLMClient

logger = logging.getLogger(__name__)


@dataclass
class StoryContent:
    """故事内容数据类"""
    topic: str
    story_framework: str
    detailed_story: str
    opening: str
    closing: str
    summary: str
    key_sentences: List[str]
    new_words: List[Dict[str, str]]  # [{"word": "coffee", "meaning": "咖啡", "example": "I'd like a cup of coffee."}]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class StoryProcessor:
    """故事处理器"""
    
    # 提示词模板
    STORY_FRAMEWORK_TEMPLATE = """请为英语教学视频生成一个故事框架。

场景主题：{topic}

要求：
1. 故事应该围绕这个场景展开
2. 适合英语学习者理解
3. 包含实用的英语表达
4. 故事长度适中（约200-300字）

请直接输出故事框架，不要添加额外说明。"""

    DETAILED_STORY_TEMPLATE = """请将以下故事框架细化为完整的故事情节。

故事框架：
{framework}

要求：
1. 丰富对话和场景描述
2. 使用自然、实用的英语表达
3. 适合制作教学视频
4. 总长度约500-800字

请直接输出细化后的完整故事，不要添加额外说明。"""

    OPENING_TEMPLATE = """请为以下英语教学视频生成开场白。

场景主题：{topic}
故事概要：{story_summary}

要求：
1. 简洁有趣，吸引学习者注意
2. 介绍本课的学习目标
3. 长度约50-100字
4. 使用简单易懂的英语

请直接输出开场白，不要添加额外说明。"""

    CLOSING_TEMPLATE = """请为以下英语教学视频生成结束语。

场景主题：{topic}
故事概要：{story_summary}

要求：
1. 总结本课重点
2. 鼓励学习者练习
3. 长度约50-100字
4. 使用简单易懂的英语

请直接输出结束语，不要添加额外说明。"""

    SUMMARY_TEMPLATE = """请为以下英语教学故事生成课程总结。

场景主题：{topic}
完整故事：
{story}

要求：
1. 总结故事中的关键英语表达
2. 提取重要的语法点和词汇
3. 提供学习建议
4. 长度约150-200字

请直接输出课程总结，不要添加额外说明。"""

    EXTRACT_KEY_SENTENCES_TEMPLATE = """请从以下故事中提取5-8个重要的英语句子。

故事内容：
{story}

要求：
1. 选择最实用、最常用的表达
2. 句子应该适合英语学习者学习
3. 按在故事中出现的顺序排列
4. 只输出句子，每行一句，不要编号

请直接输出句子列表，不要添加额外说明。"""

    EXTRACT_NEW_WORDS_TEMPLATE = """请从以下故事中提取10-15个新词汇。

故事内容：
{story}

要求：
1. 选择对英语学习者有用的词汇
2. 为每个词汇提供中文释义
3. 为每个词汇提供一个例句
4. 使用 JSON 格式输出，格式如下：
[
  {{"word": "词汇", "meaning": "中文释义", "example": "例句"}},
  ...
]

请只输出 JSON 数组，不要添加额外说明。"""

    def __init__(
        self,
        vllm_client: Optional[VLLMClient] = None,
        base_url: str = "http://localhost:8000/v1"
    ):
        """
        初始化故事处理器
        
        Args:
            vllm_client: vLLM 客户端实例，如果为 None 则创建新实例
            base_url: vLLM 服务的基础 URL（仅在 vllm_client 为 None 时使用）
        """
        self.vllm_client = vllm_client or VLLMClient(base_url=base_url)
    
    def generate_story_framework(self, topic: str) -> str:
        """
        生成故事框架
        
        Args:
            topic: 场景主题
            
        Returns:
            故事框架文本
        """
        logger.info(f"生成故事框架，主题: {topic}")
        framework = self.vllm_client.generate_with_template(
            self.STORY_FRAMEWORK_TEMPLATE,
            topic=topic
        )
        logger.info("故事框架生成完成")
        return framework
    
    def refine_story(self, framework: str) -> str:
        """
        细化故事情节
        
        Args:
            framework: 故事框架
            
        Returns:
            细化后的完整故事
        """
        logger.info("细化故事情节")
        detailed_story = self.vllm_client.generate_with_template(
            self.DETAILED_STORY_TEMPLATE,
            framework=framework
        )
        logger.info("故事情节细化完成")
        return detailed_story
    
    def generate_opening(self, topic: str, story_summary: str) -> str:
        """
        生成视频开场白
        
        Args:
            topic: 场景主题
            story_summary: 故事概要
            
        Returns:
            开场白文本
        """
        logger.info("生成视频开场白")
        opening = self.vllm_client.generate_with_template(
            self.OPENING_TEMPLATE,
            topic=topic,
            story_summary=story_summary[:200]  # 限制长度
        )
        logger.info("开场白生成完成")
        return opening
    
    def generate_closing(self, topic: str, story_summary: str) -> str:
        """
        生成视频结束语
        
        Args:
            topic: 场景主题
            story_summary: 故事概要
            
        Returns:
            结束语文本
        """
        logger.info("生成视频结束语")
        closing = self.vllm_client.generate_with_template(
            self.CLOSING_TEMPLATE,
            topic=topic,
            story_summary=story_summary[:200]  # 限制长度
        )
        logger.info("结束语生成完成")
        return closing
    
    def generate_summary(self, topic: str, story: str) -> str:
        """
        生成课程总结
        
        Args:
            topic: 场景主题
            story: 完整故事
            
        Returns:
            课程总结文本
        """
        logger.info("生成课程总结")
        summary = self.vllm_client.generate_with_template(
            self.SUMMARY_TEMPLATE,
            topic=topic,
            story=story
        )
        logger.info("课程总结生成完成")
        return summary
    
    def extract_key_sentences(self, story: str) -> List[str]:
        """
        提取重要句子
        
        Args:
            story: 完整故事
            
        Returns:
            重要句子列表
        """
        logger.info("提取重要句子")
        result = self.vllm_client.generate_with_template(
            self.EXTRACT_KEY_SENTENCES_TEMPLATE,
            story=story
        )
        
        # 解析句子列表
        sentences = [
            line.strip() 
            for line in result.split('\n') 
            if line.strip() and not line.strip().startswith('#')
        ]
        
        # 移除可能的编号
        sentences = [
            re.sub(r'^\d+[\.\)]\s*', '', sentence) 
            for sentence in sentences
        ]
        
        logger.info(f"提取到 {len(sentences)} 个重要句子")
        return sentences
    
    def extract_new_words(self, story: str) -> List[Dict[str, str]]:
        """
        提取新词
        
        Args:
            story: 完整故事
            
        Returns:
            新词列表，每个词包含 word, meaning, example
        """
        logger.info("提取新词")
        result = self.vllm_client.generate_with_template(
            self.EXTRACT_NEW_WORDS_TEMPLATE,
            story=story
        )
        
        # 尝试解析 JSON
        try:
            # 清理可能的 markdown 代码块标记
            result = result.strip()
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]
            result = result.strip()
            
            words = json.loads(result)
            
            # 验证格式
            if not isinstance(words, list):
                raise ValueError("返回的不是列表格式")
            
            for word_item in words:
                if not all(key in word_item for key in ['word', 'meaning', 'example']):
                    raise ValueError("词汇项缺少必要字段")
            
            logger.info(f"提取到 {len(words)} 个新词")
            return words
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON 解析失败，尝试手动提取: {e}")
            # 如果 JSON 解析失败，尝试手动提取
            return self._manual_extract_words(result)
    
    def _manual_extract_words(self, text: str) -> List[Dict[str, str]]:
        """
        手动提取词汇（备用方法）
        
        Args:
            text: 文本内容
            
        Returns:
            词汇列表
        """
        words = []
        # 简单的正则匹配提取
        pattern = r'["\']?word["\']?\s*:\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, text, re.IGNORECASE)
        # 这里只是示例，实际应该更完善
        return words
    
    def generate_complete_story(self, topic: str) -> StoryContent:
        """
        生成完整的故事内容
        
        Args:
            topic: 场景主题
            
        Returns:
            完整的故事内容对象
        """
        logger.info(f"开始生成完整故事内容，主题: {topic}")
        
        # 1. 生成故事框架
        framework = self.generate_story_framework(topic)
        
        # 2. 细化故事情节
        detailed_story = self.refine_story(framework)
        
        # 3. 生成开场白
        opening = self.generate_opening(topic, detailed_story)
        
        # 4. 生成结束语
        closing = self.generate_closing(topic, detailed_story)
        
        # 5. 生成课程总结
        summary = self.generate_summary(topic, detailed_story)
        
        # 6. 提取重要句子
        key_sentences = self.extract_key_sentences(detailed_story)
        
        # 7. 提取新词
        new_words = self.extract_new_words(detailed_story)
        
        story_content = StoryContent(
            topic=topic,
            story_framework=framework,
            detailed_story=detailed_story,
            opening=opening,
            closing=closing,
            summary=summary,
            key_sentences=key_sentences,
            new_words=new_words
        )
        
        logger.info("完整故事内容生成完成")
        return story_content
    
    def save_story(self, story_content: StoryContent, filepath: str):
        """
        保存故事内容到文件
        
        Args:
            story_content: 故事内容对象
            filepath: 保存路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(story_content.to_json())
        logger.info(f"故事内容已保存到: {filepath}")
    
    def load_story(self, filepath: str) -> StoryContent:
        """
        从文件加载故事内容
        
        Args:
            filepath: 文件路径
            
        Returns:
            故事内容对象
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        story_content = StoryContent(**data)
        logger.info(f"故事内容已从文件加载: {filepath}")
        return story_content

