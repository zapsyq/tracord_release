#导入会话工厂
from app.config.db_config import AsyncSession
#获取操作数据库的方法(select:参数里填写要查询的对象)
from sqlalchemy import select, exists
#导入用户模型
from app.models.user import User
#导入pydantic里校验过的创建用户的user类
from app.schemas.user import CreateUserInput

class UserRepository:
    #下面的方法都是异步，因此传入的会话应该是异步版本
    def __init__(self, session: AsyncSession):
        #定义一个自身的属性，把传入的会话赋给自身，方便调用session里的方法
        self.session = session
    
    #定义方法通过邮箱获取用户
    async def get_by_email(self, email: str): 
        #开启会话事务
        async with self.session.begin():
            #scalar是查询方法，select参数里填要查询的对象
            user = await self.session.scalar(select(User).where(User.email == email))
            return user
        
    async def email_is_exist(self, email: str): 
        async with self.session.begin():
            #stmt是编程里的常用缩写，意思是状态，如果select里填的是对象，则返回对象信息，如果填的是exist，则返回bool
            stmt = select(exists().where(User.email == email))
            return await self.session.scalar(stmt)

    async def create_user(self, user_schema: CreateUserInput):
        async with self.session.begin():
            #定义user变量接收User类的内容，通过会话添加到数据库中，直接返回user
            #用pydantic的model_dump方法将user_schema转换成字典，还需要在前面加**将字典传换成关键字参数
            user = User(**user_schema.model_dump())
            self.session.add(user)
            return user
            

