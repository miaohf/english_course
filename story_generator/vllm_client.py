"""
vLLM 客户端

用于调用本地部署的 vLLM 服务生成文本内容
"""

import json
import requests
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class VLLMClient:
    """vLLM API 客户端"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: Optional[str] = None,
        timeout: int = 300
    ):
        """
        初始化 vLLM 客户端
        
        Args:
            base_url: vLLM 服务的基础 URL
            api_key: API 密钥（如果需要）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.chat_endpoint = f"{self.base_url}/chat/completions"
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None
    ) -> str:
        """
        生成文本内容
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数
            model: 模型名称（如果使用特定模型）
            
        Returns:
            生成的文本内容
            
        Raises:
            requests.RequestException: 请求失败时抛出异常
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model or "default",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            logger.info(f"调用 vLLM API: {self.chat_endpoint}")
            response = requests.post(
                self.chat_endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"成功生成内容，长度: {len(content)} 字符")
            return content.strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"vLLM API 调用失败: {e}")
            raise
    
    def generate_with_template(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        使用模板生成内容
        
        Args:
            template: 提示词模板，支持 {variable} 格式的占位符
            **kwargs: 模板变量
            
        Returns:
            生成的文本内容
        """
        prompt = template.format(**kwargs)
        return self.generate(prompt)
    
    def test_connection(self) -> bool:
        """
        测试与 vLLM 服务的连接
        
        Returns:
            连接是否成功
        """
        try:
            # 发送一个简单的测试请求
            test_prompt = "Say 'OK' if you can hear me."
            result = self.generate(test_prompt, max_tokens=10)
            logger.info("vLLM 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"vLLM 连接测试失败: {e}")
            return False

