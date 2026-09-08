from langchain_chroma import Chroma
from app.agent.utils.config_handler import chroma_config
from app.agent.model.factory import embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
from app.agent.utils.path_tool import get_abs_path
from app.agent.utils.file_handler import txt_loader_by_city, pdf_loader, csv_loader, listdir_with_allowed_type, get_file_md5_hex
from app.agent.utils.logger_handler import logger
from langchain_core.documents import Document


class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_config["collection_name"],
            embedding_function=embedding_model,
            persist_directory=get_abs_path(chroma_config["persist_directory"]),
        )
        self.slot_store = Chroma(
            collection_name=chroma_config["slot_collection_name"],
            embedding_function=embedding_model,
            persist_directory=get_abs_path(chroma_config["persist_directory"]),
        )
        #文本分割器
        self.spiter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_config["chunk_size"], 
            chunk_overlap=chroma_config["chunk_overlap"],
            separators=chroma_config["separators"],
            #长度统计
            length_function=len,
        )

    #带相似度分数的检索（用于判断知识库是否 miss）
    def search_with_score(self, query: str, k: int | None = None):
        k = k or chroma_config["k"]
        return self.vector_store.similarity_search_with_score(query, k=k)

    #获取槽位示例检索器对象
    def get_slot_retriever(self):
        return self.slot_store.as_retriever(search_kwargs={"k": chroma_config["slot_k"]})

    #检查md5是否已记录（文件是否已加载）
    def _check_md5_hex(self, md5_hex: str) -> bool:
        path = get_abs_path(chroma_config["md5_hex_store"])
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()
            return False
        with open(path, "r", encoding="utf-8") as f:
            return md5_hex in [l.strip() for l in f]

    #记录md5
    def _save_md5_hex(self, md5_hex: str):
        with open(get_abs_path(chroma_config["md5_hex_store"]), "a", encoding="utf-8") as f:
            f.write(md5_hex + "\n")
    
    #加载旅行攻略文档
    def load_document(self):
        """
        从数据文件夹内读取数据文件, 转为向量存入向量库
        计算文件md5做去重, 分文件增量更新：只改哪个文件就只更新哪个
        """
        #获取文档, 配置写了不同文档转换成langchain格式文档的方法, 直接调用
        def get_file_dociuments(file_path: str):
            if file_path.endswith(".txt"):
                return txt_loader_by_city(file_path)
            if file_path.endswith(".pdf"):
                return pdf_loader(file_path)
            if file_path.endswith(".csv"):
                return csv_loader(file_path)
            return []

        allowed_file_path: tuple[str]= listdir_with_allowed_type(
            get_abs_path(chroma_config["data_path"]),
            tuple(chroma_config["allow_knowledge_file_type"])
        )

        # 分文件增量更新：每个文件独立，md5 变了就清空该文件旧数据再重新摄入
        for path in allowed_file_path:
            md5_hex = get_file_md5_hex(path)
            if self._check_md5_hex(md5_hex):
                logger.info(f"[加载知识库] {path}内容已存在, 跳过")
                continue
            try:
                # 清空该文件的旧数据（按 source 过滤），只更新这个文件
                self.vector_store.delete(where={"source": path})

                documents: list[Document] = get_file_dociuments(path)
                if not documents:
                    logger.warning(f"[加载知识库] {path}内容为空, 跳过")
                    continue

                # txt 已按城市切好，直接存；pdf/csv 才需要 split
                if path.endswith(".txt"):
                    final_documents = documents
                else:
                    final_documents = self.spiter.split_documents(documents)
                # 统一给所有 chunk 加 source（来源文件路径），用于分文件增量更新
                for d in final_documents:
                    d.metadata["source"] = path
                if not final_documents:
                    logger.warning(f"[加载知识库] {path}内容分割为空, 跳过")
                    continue
                #将内容存进向量库
                self.vector_store.add_documents(final_documents)
                #保存md5, 避免重复加载
                self._save_md5_hex(md5_hex)
                logger.info(f"[加载知识库] {path}内容已保存")
            except Exception as e:
                #exc_info=True, 记录详细的报错堆栈, 如果为False, 仅记录报错信息本身
                logger.error(f"[加载知识库] {path}内容加载失败: {str(e)}", exc_info=True)
                continue

    #加载槽位填充示例
    def load_slot_examples(self):
        """
        把槽位填充示例(jsonl)入库到独立的 slot_examples 集合
        计算文件md5做去重, 文件变了清空重来
        """
        path = get_abs_path("data/slot_example.jsonl")
        #获取文件的md5
        md5_hex = get_file_md5_hex(path)
        if self._check_md5_hex(md5_hex):
            logger.info(f"[槽位示例] {path}内容已存在, 跳过")
            return 0
        try:
            with open(path, encoding="utf-8") as f:
                items = [json.loads(l) for l in f if l.strip()]
            documents: list[Document] = [Document(page_content=item["query"], metadata={"slots": item["slots"]}) for item in items]
            if not documents:
                logger.warning(f"[槽位示例] {path}内容为空, 跳过")
                return 0
            #清空旧数据, 避免重复
            existing = self.slot_store.get()
            if existing.get("ids"):
                self.slot_store.delete(ids=existing["ids"])
            #将内容存进向量库
            self.slot_store.add_documents(documents)
            #保存md5, 避免重复加载
            self._save_md5_hex(md5_hex)
            logger.info(f"[槽位示例] {path}内容已保存")
            return len(documents)
        except Exception as e:
            #exc_info=True, 记录详细的报错堆栈, 如果为False, 仅记录报错信息本身
            logger.error(f"[槽位示例] {path}内容加载失败: {str(e)}", exc_info=True)
            return 0