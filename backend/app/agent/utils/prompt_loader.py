from app.agent.utils.config_handler import prompts_config
from app.agent.utils.path_tool import get_abs_path
from app.agent.utils.logger_handler import logger

#提示词加载配置
def load_prompt(name: str) -> str:
    """按名字加载提示词, 配置项为 {name}_prompt_path"""
    key = f"{name}_prompt_path"
    path = prompts_config.get(key)
    if not path:
        logger.error(f"[load_prompt] 在yaml中没有{key}配置项")
        return ""
    try:
        return open(get_abs_path(path), "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_prompt] 解析提示词失败: {str(e)}")
        return ""


def load_rag_prompt():
    try:
        rag_prompt_path = get_abs_path(prompts_config["rag_summarize_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_rag_prompt] 在yaml中没有rag_summarize_prompt_path配置项")
        raise e
    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_rag_prompt] 解析rag总结提示词失败: {str(e)}")
        return ""

