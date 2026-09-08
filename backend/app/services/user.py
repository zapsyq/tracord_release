from app.crud.user import UserRepository
from app.schemas.user import RegisterIn, LoginIn
from app.core.token import AuthHandler
from app.cache.verify_code import check_code
from fastapi import HTTPException
from app.schemas.user import CreateUserInput


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
        self.auth_handler = AuthHandler()

    #注册
    async def register(self, data: RegisterIn):
        #判断邮箱是否存在，存在则执行注册流程
        email_exist = await self.repo.email_is_exist(email=str(data.email))
        if email_exist:
            raise HTTPException(status_code=400, detail="该邮箱已存在")
        #校验验证码是否正确
        code_check = await check_code(email=str(data.email), input_code=str(data.code))
        if not code_check:
            raise HTTPException(status_code=400, detail="邮箱或验证码错误")
        #校验成功则在数据库中创建用户，错误则返回
        try:
            user = await self.repo.create_user(CreateUserInput(
                email=str(data.email),
                username=data.username,
                password=data.password
            ))
            tokens = self.auth_handler.encode_login_token(user.id)
        except Exception:
            raise HTTPException(status_code=500, detail="注册失败")
        return {
            "user": user,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"]
        }
    
    #登录
    async def login(self, data: LoginIn):
        user = await self.repo.get_by_email(email=str(data.email)) 
        if not user:
            raise HTTPException(status_code=400, detail="该用户不存在")
        if not user.check_password(str(data.password)):
            raise HTTPException(status_code=400, detail="邮箱或密码错误")
        #若校验成功则生成token
        tokens = self.auth_handler.encode_login_token(user.id)
        return {
            "user": user,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"]
        }