from dotenv import load_dotenv
import os

load_dotenv()

#数组维护key池
map_key = [k for k in (os.getenv("TIANDITU_KEYS") or "").split(",") if k]

#全局指针
index = 0

def get_key():
    #global声明此方法会修改全局变量index
    global index
    #获取当前索引对应的key
    key = map_key[index]
    #指针+1
    index = (index + 1) % len(map_key)
    return key

