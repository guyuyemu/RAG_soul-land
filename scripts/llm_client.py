"""
云武AI API客户端
用于调用云武AI的大语言模型API
"""

import requests
import json
from typing import Optional, Dict, Any


class YunWuAIClient:
    """云武AI客户端类"""
    
    def __init__(
        self, 
        api_key,
        api_url
    ):
        """
        初始化云武AI客户端
        
        参数:
            api_key: 云武AI的API密钥
            api_url: 云武AI的API地址
        """
        self.api_key = api_key
        self.api_url = api_url
        
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 500,
        temperature: float = 0.7,
        model: str = "deepseek-v3.2-exp",  # 默认模型，可根据实际支持模型调整
        **kwargs
    ) -> str:
        """
        调用云武AI生成回答
        
        参数:
            prompt: 输入提示词
            max_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            model: 模型名称
            **kwargs: 其他可选参数
            
        返回:
            生成的文本回答
        """
        try:
            # 构建请求数据（遵循OpenAI兼容格式）
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,** kwargs
            }
            
            # 发送POST请求到API
            response = requests.post(
                self.api_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                timeout=60  # 60秒超时
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 提取生成的文本
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0]["message"]["content"]
            else:
                return str(result)
                
        except requests.exceptions.Timeout:
            return "错误：请求超时，API响应时间过长"
        except requests.exceptions.ConnectionError:
            return f"错误：无法连接到云武AI API ({self.api_url})，请检查网络连接"
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return "错误：API密钥无效或未授权"
            return f"错误：HTTP请求失败 ({response.status_code}) - {str(e)}"
        except requests.exceptions.RequestException as e:
            return f"错误：API请求失败 - {str(e)}"
        except Exception as e:
            return f"错误：生成回答时出现异常 - {str(e)}"
    
    def test_connection(self) -> bool:
        """
        测试与云武AI API的连接
        
        返回:
            连接是否成功
        """
        try:
            # 尝试发送一个简单的测试请求
            test_response = self.generate("测试连接", max_tokens=10)
            return "错误" not in test_response
        except:
            return False