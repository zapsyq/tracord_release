from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import EmailStr
#Annotated可以为参数添加额外的注释，供fastapi和pydantic使用
from typing import Annotated
from app.core.dependencies import get_mail, get_session
from fastapi_mail import FastMail, MessageSchema, MessageType
from app.cache.verify_code import set_code
from app.crud.user import UserRepository
from app.schemas.user import RegisterIn, LoginIn, LoginOut
from app.config.db_config import AsyncSession
from app.schemas import ResponseOut
from app.core.token import AuthHandler
from app.config.cache_config import redis_client
from app.services.map_key_pool import get_key
from app.services.user import UserService


router = APIRouter(prefix="/user", tags=["user"])

auth_handler = AuthHandler()

@router.post("/verify-code", response_model=ResponseOut)
async def get_mail_code(
    #Query表示该参数从路由中获取，email参数表示收件人邮箱
    email: Annotated[EmailStr, Body(..., embed=True)],
   
    #fastapi的发信工具，内含发件人邮箱
    mail: FastMail = Depends(get_mail),
):
    result = await set_code(email)
    if result is False:
        ttl = await redis_client.ttl(f"cooldown:{email}")
        raise HTTPException(status_code=429, detail=f"请等待{ttl}秒后再试", headers={"Retry-After": str(ttl)})
    if result is None: 
        raise HTTPException(status_code=500, detail="获取验证码失败")
    
    code = result
    
    #邮件内容
    message = MessageSchema(
        subject="[迹录]验证码",
        recipients=[email],
        body=f"您的验证码为：{code}, 有效期为5分钟",
        subtype=MessageType.plain
    )

    try:
        await mail.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="验证码发送失败")
    #返回封装的响应
    return ResponseOut()
    

@router.post("/register", response_model=LoginOut)
async def register(
    data: RegisterIn,
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session=session)
    service = UserService(user_repo)
    return await service.register(data)

            
@router.post("/login", response_model=LoginOut)
async def login(
    data: LoginIn,
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session=session)
    service = UserService(user_repo)
    return await service.login(data)


#长效登录实现：使用refresh_token刷新access_token
#refresh_token过长，因此使用body传参，embed=True表示直接从json对象中取出相应对象作为参数
@router.post("/refresh-token")
def refresh_access_token(refresh_token: str = Body(..., embed=True)):
    try:
        user_id = auth_handler.decode_refresh_token(refresh_token)
        new_access_token = auth_handler.encode_update_token(user_id)
        return new_access_token
    except HTTPException:
        raise
  
@router.get("/map/key")
def get_map_key():
    key = get_key()
    return{
        "key": key
    }