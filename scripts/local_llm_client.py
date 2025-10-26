"""
本地大模型API客户端
用于调用本地部署的大语言模型
"""

import requests
import json
from typing import Optional, Dict, Any


class LocalLLMClient:
    """本地大模型客户端类"""
    
    def __init__(self, api_url: str = "http://36.213.46.197:5000/api/infer"):
        """
        初始化本地LLM客户端
        
        参数:
            api_url: 本地大模型的API地址
        """
        self.api_url = api_url
        
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        调用本地大模型生成回答
        
        参数:
            prompt: 输入提示词
            max_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            **kwargs: 其他可选参数
            
        返回:
            生成的文本回答
        """
        try:
            # 构建请求数据
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            # 发送POST请求到本地API
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=6000  # 60秒超时
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 根据API返回格式提取文本
            # 这里假设返回格式为 {"response": "生成的文本"}
            # 如果实际格式不同，需要调整
            if isinstance(result, dict):
                return result.get("response", result.get("text", str(result)))
            else:
                return str(result)
                
        except requests.exceptions.Timeout:
            return "错误：请求超时，本地模型响应时间过长"
        except requests.exceptions.ConnectionError:
            return f"错误：无法连接到本地模型API ({self.api_url})，请检查服务是否运行"
        except requests.exceptions.RequestException as e:
            return f"错误：API请求失败 - {str(e)}"
        except Exception as e:
            return f"错误：生成回答时出现异常 - {str(e)}"
    
    def test_connection(self) -> bool:
        """
        测试与本地API的连接
        
        返回:
            连接是否成功
        """
        try:
            response = requests.get(
                self.api_url.replace("/api/infer", "/health"),
                timeout=5
            )
            return response.status_code == 200
        except:
            # 如果没有health端点，尝试发送一个简单的请求
            try:
                test_response = self.generate("测试", max_tokens=10)
                return "错误" not in test_response
            except:
                return False
