"""
旅游攻略问答服务类: 用户提问, 搜索本地攻略知识库, 将提问和参考资料提交给模型, 让模型总结回复
知识库 miss(检索不中)时返回失败话术, 交给 harness 折返: 摘掉 travel_agent 重开一轮 → 闲聊兜底
"""
from app.agent.travel.services.vector_store import VectorStoreService
from app.agent.utils.prompt_loader import load_rag_prompt
from langchain_core.prompts import PromptTemplate
from app.agent.model.factory import chat_model
from langchain_core.output_parsers import StrOutputParser

# distance 阈值：检索结果的最小 distance 超过它，判定本地知识库 miss（实测：命中 0.61 左右，不相关 0.70 往上）
MISS_THRESHOLD = 0.68


class RagSummaryService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.prompt_text = load_rag_prompt()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self.prompt_template | self.model | StrOutputParser()

    def _build_context(self, query: str) -> str:
        """拼 context：本地知识库命中返回参考资料, miss 返回空字符串"""
        hits = self.vector_store.search_with_score(query)
        if hits and hits[0][1] <= MISS_THRESHOLD:
            context = ""
            for i, (doc, _) in enumerate(hits, 1):
                context += f"[参考资料{i}]: {doc.page_content}\n"
            return context
        return ""

    def rag_summary(self, query: str) -> str:
        context = self._build_context(query)
        if not context:
            return "抱歉，暂时没找到相关资料。"
        return self.chain.invoke({"input": query, "context": context})
