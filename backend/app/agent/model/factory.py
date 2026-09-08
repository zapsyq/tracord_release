from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.agent.utils.config_handler import model_config

import httpx
import requests as req

# 自定义传输层，兼容 llama.cpp 的 HTTP 服务, 本地模型
class RequestsTransport(httpx.BaseTransport):
    """用 requests 替代 httpx 的 HTTP 传输层，兼容 llama.cpp 的 HTTP 服务。"""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        headers = dict(request.headers)
        # 移除 httpx 默认的压缩请求头，llama.cpp 在 CPU 模式下处理压缩响应可能异常
        headers.pop("accept-encoding", None)

        resp = req.request(
            method=request.method.decode() if isinstance(request.method, bytes) else request.method,
            url=str(request.url),
            headers=headers,
            data=request.content,
            timeout=httpx.Timeout(120).connect,
        )
        return httpx.Response(
            status_code=resp.status_code,
            headers=list(resp.headers.items()),
            content=resp.content,
            request=request,
        )


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(BaseModelFactory):
    def generator(self, temperature: float = 0.5) -> Optional[Embeddings | BaseChatModel]:
        return ChatOpenAI(
            model=model_config["chat_model_name"],
            base_url="http://127.0.0.1:8080/v1",
            api_key="sk-no-key-required",
            temperature=temperature,
            http_client=httpx.Client(transport=RequestsTransport()),
        )
    
class EmbeddingFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return OpenAIEmbeddings(
            model=model_config["embedding_model_name"],
            base_url="http://127.0.0.1:8081/v1",
            api_key="sk-no-key-required",
            http_client=httpx.Client(transport=RequestsTransport()),
            check_embedding_ctx_length=False,  # 关掉 tiktoken 本地分词，发原始文本给 m3e
        )
    
chat_model = ChatModelFactory().generator()
# supervisor 只做意图路由，用低温保证确定性，避免随机选错子助手
supervisor_model = ChatModelFactory().generator(temperature=0.1)
embedding_model = EmbeddingFactory().generator()