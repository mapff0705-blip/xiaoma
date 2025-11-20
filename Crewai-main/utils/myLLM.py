
import os
from crewai import LLM
from dotenv import load_dotenv
load_dotenv(override=True)


DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
QWEN_API_KEY=os.getenv("QWEN_API_KEY")
# deepseek模型相关配置
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_CHAT_API_KEY = DEEPSEEK_API_KEY
DEEPSEEK_CHAT_MODEL = "deepseek/deepseek-chat"
# 通义千问
QWENAPI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWENAPI_CHAT_API_KEY = QWEN_API_KEY
QWENAPI_CHAT_MODEL = "openai/qwen-plus"


# 定函数 模型初始化
def my_llm(llmType):

    if llmType == "deepseek":
        llm = LLM(
            base_url=QWENAPI_API_BASE,
            api_key=QWENAPI_CHAT_API_KEY,
            model=QWENAPI_CHAT_MODEL,  # 本次使用的模型
            temperature=0.7,
        )
    else:
        llm = LLM(
            base_url=DEEPSEEK_API_BASE,  # 请求的API服务地址
            api_key=DEEPSEEK_CHAT_API_KEY,  # API Key
            model=DEEPSEEK_CHAT_MODEL,  # 本次使用的模型

        )
    return llm