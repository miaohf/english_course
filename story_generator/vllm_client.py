"""
vLLM 客户端

用于调用本地部署的 vLLM 服务生成文本内容
已重构为使用 LangChain，提供更好的模板支持和结构化输出能力
"""

import os
from typing import Optional
from warnings import warn

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from logger_config import get_logger

logger = get_logger()


class VLLMClient:
    """
    vLLM API 客户端（使用 LangChain 实现）
    
    注意：推荐使用 StoryProcessor，它提供了更完整的功能和结构化输出。
    此类保留用于向后兼容和简单的文本生成场景。
    """
    
    def __init__(
        self,
        base_url: str = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 300
    ):
        """
        初始化 vLLM 客户端
        
        Args:
            base_url: vLLM 服务的基础 URL（默认从环境变量读取）
            api_key: API 密钥（默认从环境变量读取）
            model: 模型名称（默认从环境变量读取）
            timeout: 请求超时时间（秒，LangChain 会自动处理）
        """
        # 从环境变量读取配置（使用大写环境变量名）
        self.base_url = base_url or os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("VLLM_API_KEY", "sk-placeholder")
        self.model = model or os.getenv("VLLM_MODEL", "default")
        self.timeout = timeout
        
        # 从环境变量读取 max_tokens，默认 100000（模型支持最大 1M）
        default_max_tokens = int(os.getenv("VLLM_MAX_TOKENS", "100000"))
        
        # 初始化 LangChain ChatOpenAI 客户端
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            temperature=0.7,
            max_tokens=default_max_tokens,
            timeout=self.timeout
        )
        self.default_max_tokens = default_max_tokens
        
        logger.info(f"VLLMClient initialized with endpoint: {self.base_url}")
        logger.warning("VLLMClient is deprecated. Consider using StoryProcessor for better features.")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        生成文本内容（使用 LangChain ChatPromptTemplate）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数（None 表示使用默认值，从环境变量或 100000）
            model: 模型名称（如果使用特定模型，会创建新的 llm 实例）
            
        Returns:
            生成的文本内容
        """
        # 如果没有指定 max_tokens，使用默认值
        if max_tokens is None:
            max_tokens = self.default_max_tokens
        
        # 如果指定了不同的模型或参数，创建临时 llm 实例
        if model or temperature != 0.7 or max_tokens != self.default_max_tokens:
            llm = ChatOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                model=model or self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
        else:
            llm = self.llm
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))
        
        # 使用 LangChain ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_messages(messages)
        chain = prompt_template | llm | StrOutputParser()
        
        try:
            result = chain.invoke({})
            logger.info(f"Successfully generated content, length: {len(result)} characters")
            return result.strip()
        except Exception as e:
            logger.error(f"vLLM API call failed: {e}")
            raise
    
    def generate_with_template(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        使用模板生成内容（使用 LangChain ChatPromptTemplate）
        
        Args:
            template: 提示词模板，支持 {variable} 格式的占位符
            **kwargs: 模板变量
            
        Returns:
            生成的文本内容
        """
        # 使用 LangChain 的模板系统
        prompt_template = ChatPromptTemplate.from_template(template)
        chain = prompt_template | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke(kwargs)
            logger.info(f"Successfully generated content with template, length: {len(result)} characters")
            return result.strip()
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            raise
    
    def test_connection(self, model: Optional[str] = None) -> bool:
        """
        测试与 vLLM 服务的连接
        
        Args:
            model: 模型名称（可选，如果不指定则使用服务默认模型）
        
        Returns:
            连接是否成功
        """
        try:
            # 发送一个简单的测试请求
            test_prompt = "Say 'OK' if you can hear me."
            result = self.generate(test_prompt, max_tokens=10, model=model)
            logger.info("vLLM connection test successful")
            return True
        except Exception as e:
            logger.error(f"vLLM connection test failed: {e}")
            return False
