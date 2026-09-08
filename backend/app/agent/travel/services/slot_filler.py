"""
槽位填充服务: 从 RAG 检索相似示例, 喂给模型填出旅行约束
"""

import os, re, httpx
from app.agent.travel.services.vector_store import VectorStoreService
from app.core.constants import CITY_ADCODE_MAP
from langchain_core.documents import Document

LLM_BASE  = os.environ.get("LLM_API_BASE", "http://127.0.0.1:8080/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen")


def _int(s, d):
    try: return int("".join(c for c in s if c.isdigit()))
    except Exception: return d


def _norm_city(city):
    """城市名不在映射表里就打回?"""
    return city if city in CITY_ADCODE_MAP else "?"


async def _call_llm(prompt):
    """异步调 LLM，先试 /completions 再试 /chat/completions，避免阻塞事件循环"""
    # trust_env=False: 绕过系统代理(Windows 代理会劫持 127.0.0.1 → 502), 直接连本地模型
    async with httpx.AsyncClient(base_url=LLM_BASE, timeout=60.0, trust_env=False) as client:
        for ep, payload in [
            ("/completions", {
                "model": LLM_MODEL, "temperature": 0.1, "max_tokens": 2000, "prompt": prompt,
                "stop": ["\n\n", "需求:"],
            }),
            ("/chat/completions", {
                "model": LLM_MODEL, "temperature": 0.1, "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
                "stop": ["\n\n", "需求:"],
            }),
        ]:
            try:
                r = await client.post(ep, json=payload)
                data = r.json()
                if ep == "/completions":
                    text = data["choices"][0]["text"].strip()
                    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
                    if text: return text
                else:
                    m = data["choices"][0]["message"]
                    c = m.get("content", "") or ""
                    rc = m.get("reasoning_content", "") or ""
                    ret = (c or rc).strip()
                    if ret: return ret
            except Exception: continue
    return ""


class SlotFillerService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_slot_retriever()

    #检索相似示例
    def retrieve_examples(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)

    #拼提示词: 槽位说明 + 检索到的示例 + 当前query
    def _build_prompt(self, query: str, docs: list[Document]) -> str:
        lines = ['提取旅行需求，只输出以下字段，如果天数,预算,人数信息不知道的填"?"', "", "示例"]
        for doc in docs:
            slots = doc.metadata["slots"].replace(" ", "\n")
            lines += [f"需求: {doc.page_content}", "输出:", slots, ""]
        lines += [f"需求: {query}", "输出:"]
        return "\n".join(lines)

    #解析模型输出 → 约束dict
    def _parse(self, raw: str) -> dict:
        c = {"start_city": "?", "target_city": "?", "days": 1, "budget": 5000, "people_number": 1}
        raw = (raw or "").replace("；", "\n").replace("：", ":")
        for line in raw.strip().split("\n"):
            if ":" not in line: continue
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            v = re.sub(r'[<>]', '', v).strip()
            if not v: continue
            if k in ("出发","from","出发地","起点","始发"): c["start_city"] = v
            elif k in ("目的","to","目的地","终点","目的城市","目标"): c["target_city"] = v
            elif k in ("天数","days","时长","时间","天"): c["days"] = max(1, _int(v, 1))
            elif k in ("预算","budget","费用","花费"): c["budget"] = max(100, _int(v, 5000))
            elif k in ("人数","people","人员"): c["people_number"] = max(1, _int(v, 1))
        em = {"beijing": "北京", "shanghai": "上海", "guangzhou": "广州", "shenzhen": "深圳",
              "chengdu": "成都", "chongqing": "重庆", "hangzhou": "杭州", "nanjing": "南京",
              "wuhan": "武汉", "suzhou": "苏州"}
        c["start_city"] = em.get(c["start_city"].lower(), c["start_city"])
        c["target_city"] = em.get(c["target_city"].lower(), c["target_city"])
        # 城市名不在映射表里就打回?
        c["start_city"] = _norm_city(c["start_city"])
        c["target_city"] = _norm_city(c["target_city"])
        c["overall_budget"] = c["budget"]
        return c

    #填槽
    async def fill_slots(self, query: str) -> dict:
        docs = self.retrieve_examples(query)
        prompt = self._build_prompt(query, docs)
        raw = await _call_llm(prompt)
        return self._parse(raw)


# 单例：VectorStoreService 初始化会建 Chroma 连接，复用避免每次请求重建
_slot_filler: SlotFillerService | None = None

def get_slot_filler() -> SlotFillerService:
    global _slot_filler
    if _slot_filler is None:
        _slot_filler = SlotFillerService()
    return _slot_filler
