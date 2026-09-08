import os, hashlib
from app.agent.utils.logger_handler import logger
from langchain_core.documents import Document
#langchain社区文档加载器，用于加载pdf和txt文件
from langchain_community.document_loaders import PyPDFLoader, CSVLoader

#文件处理工具
#获取文件的md5的十六进制字符串
def get_file_md5_hex(file_path: str):
    if not os.path.exists(file_path):
        logger.error(f"[md5计算]文件 {file_path}不存在")
        return None
    if not os.path.isfile(file_path):
        logger.error(f"[md5计算]路径 {file_path}非文件")
        return None
    
    md5_obj = hashlib.md5()

    #分片读取，避免大文件一次性进内存
    chunk_size = 4096
    try:
        #必须以二进制模式读取
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件 {file_path} md5失败, {str(e)}")
        return None
   
#返回文件夹内的文件列表(只允许返回指定类型的文件)
def listdir_with_allowed_type(file_path: str, allowed_types: tuple[str]):
    files = []
    if not os.path.isdir(file_path):
        logger.error(f"[文件列表]路径 {file_path}非文件夹")
        return ()
    
    for f in os.listdir(file_path):
        if f.endswith(allowed_types):
            files.append(os.path.join(file_path, f))
    return tuple(files)

def pdf_loader(file_path: str, password: str = None) -> list[Document]:
    return PyPDFLoader(file_path, password=password).load()

def txt_loader_by_city(file_path: str) -> list[Document]:
    """按 ### 标记切分攻略 txt，每个城市一个 Document。"""
    with open(file_path, encoding="utf-8") as f:
        text = f.read()

    docs = []
    for part in text.split("###"):
        part = part.strip()
        if part:
            docs.append(Document(page_content=part))
    return docs

def csv_loader(file_path: str) -> list[Document]:
    return CSVLoader(file_path, encoding="utf-8").load()
