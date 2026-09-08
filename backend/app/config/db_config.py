#数据库连接: 从 .env 读取, 本地开发有默认值
import os
from dotenv import load_dotenv

load_dotenv()

# sqlalchemy 异步引擎
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "tracord")

#数据库url
async_database_url = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

#创建异步引擎, 管理数据库连接的创建、连接池的维护、SQL语句的翻译, 不直接操作数据库
async_engine = create_async_engine(
    async_database_url,
    echo = False,
    pool_size = 10,
    max_overflow = 20,
    pool_timeout = 10,
    pool_recycle = 3600,
    pool_pre_ping = True
)

#创建会话工厂
async_session_factory = sessionmaker(
    bind = async_engine,
    class_ = AsyncSession,
    #查找数据库前是否更新数据库，防止遗漏数据
    autoflush = False,
    #提交数据后是否关闭会话
    expire_on_commit = False
)
