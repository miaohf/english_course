"""
内容提取模块

包含从故事中提取关键句子和词汇的方法
"""

import time
from typing import List
from langchain_core.prompts import ChatPromptTemplate

from .schemas import WordItem
from .internal_schemas import ExtractedSentences, ExtractedWords
from .prompts import (
    EXTRACT_KEY_SENTENCES_SYSTEM,
    EXTRACT_KEY_SENTENCES_USER,
    EXTRACT_NEW_WORDS_SYSTEM,
    EXTRACT_NEW_WORDS_USER,
)
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
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_KEY_SENTENCES_SYSTEM),
            ("user", EXTRACT_KEY_SENTENCES_USER)
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(ExtractedSentences)
        chain = prompt | structured_llm
        
        result = chain.invoke({"story": story})
        sentences = result.sentences
        
        elapsed = time.time() - start_time
        logger.info(f"<green>Extracted {len(sentences)} key sentences in {elapsed:.2f} seconds</green>")
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
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_NEW_WORDS_SYSTEM),
            ("user", EXTRACT_NEW_WORDS_USER)
        ])
        
        # 使用结构化输出
        structured_llm = self.llm.with_structured_output(ExtractedWords)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"story": story})
            words = result.words
            elapsed = time.time() - start_time
            logger.info(f"<green>Extracted {len(words)} vocabulary words in {elapsed:.2f} seconds</green>")
            return words
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Vocabulary extraction failed after {elapsed:.2f} seconds: {e}")
            return []

