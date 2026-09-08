#获取会话工厂
from app.config.db_config import async_session_factory
#邮件发送模块依赖注入
from app.core.mail import create_mail

#定义获取会话的函数
async def get_session():
    session = async_session_factory()
    #返回会话对象
    try:
        yield session
    #确保会话关闭
    finally:
        await session.close()

#发送邮件的依赖注入
async def get_mail():
    return create_mail()

