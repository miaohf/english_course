"""
内容提取模块

包含从故事中提取关键句子和词汇的方法
"""

from typing import List
from langchain_core.prompts import ChatPromptTemplate

from .schemas import WordItem
from .internal_schemas import ExtractedSentences, ExtractedWords
from logger_config import get_logger

logger = get_logger()


class ContentExtractors:
    """内容提取器 - 包含所有内容提取相关方法"""
    
    def __init__(self, llm):
        """
        初始化内容提取器
        
        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm
    
    def extract_key_sentences(self, story: str) -> List[str]:
        """
        提取重要句子
        
        Args:
            story: 完整故事
            
        Returns:
            重要句子列表
        """
        logger.info("<cyan>Extracting key sentences from story</cyan>")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an English teaching expert.
Extract 5-8 key English sentences from the story that are:
1. Most practical and commonly used
2. Good examples of natural English
3. Suitable for learners to memorize and practice
4. Arranged in order of appearance in the story"""),
            ("user", "Extract key sentences from this story:\n\n{story}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(ExtractedSentences)
        chain = prompt | structured_llm
        
        result = chain.invoke({"story": story})
        sentences = result.sentences
        
        logger.info(f"<green>Extracted {len(sentences)} key sentences</green>")
        return sentences
    
    def extract_new_words(self, story: str) -> List[WordItem]:
        """
        提取新词
        
        Args:
            story: 完整故事
            
        Returns:
            新词列表
        """
        logger.info("<cyan>Extracting new vocabulary from story</cyan>")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an English vocabulary expert.
Extract 10-15 useful vocabulary words from the story.
For each word, provide:
- The English word or phrase
- Chinese meaning
- An example sentence"""),
            ("user", "Extract vocabulary from this story:\n\n{story}")
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(ExtractedWords)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"story": story})
            words = result.words
            logger.info(f"<green>Extracted {len(words)} vocabulary words</green>")
            return words
        except Exception as e:
            logger.warning(f"Vocabulary extraction failed: {e}")
            return []

