#JWT 配置: 密钥从 .env 读取(必须32字节以上, 泄漏的旧密钥务必更换)
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(".env 里缺少 JWT_SECRET_KEY, 请参照 .env.example 配置")

#登录token有效期
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)

#刷新token有效期
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=365)
