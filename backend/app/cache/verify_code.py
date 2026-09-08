from app.config.cache_config import redis_client
from app.agent.utils.logger_handler import logger
import random
import string


#生成随机四位验证码
def create_code():
    source = string.digits * 5
    code = "".join(random.sample(source, 4))
    return code


#设置缓存方法与读取方法
#设置缓存，参数：查找的键，过期时间，值
async def set_code(email: str, expire: int = 300):
    #设置冷却时间，防止用户频繁获取验证码
    cd_time = 60
    #尝试执行
    try:
        code = create_code()
        #设置冷却时间的键名
        cooldown_key = f"cooldown:{email}"
        if await redis_client.exists(cooldown_key):
            return False

        #可以直接用key = email，为了防止冲突，加前缀
        key = f"code:{email}"
        await redis_client.setex(key, expire, code)
        #创建标识，防止用户频繁获取验证码
        await redis_client.setex(cooldown_key, cd_time, "1")
        return code
     #尝试执行失败就抛异常
    except Exception as e:
        logger.error(f"设置缓存失败: {e}")
        return None

#读取字符串,检查验证码
async def check_code(email: str, input_code: str):
    try:
        #设置查找的键名，和设置缓存的键名相同
        key = f"code:{email}"
        #基于连接对象调用get方法根据指定的键获取值
        exist_code = await redis_client.get(key)
        #判断验证码是否存在且输入的验证码是否一致
        if exist_code and exist_code == input_code:
            #验证码一致就删除缓存
            await redis_client.delete(key)
            return True
        return False
    except Exception as e:
        logger.error(f"获取缓存失败: {e}")
        return False

