#初始化模型，添加新模型时，alembic通过init识别模型，生成迁移文件
from .base import Base
from .user import User
from .cities import LightCity
from .trips import Trip
from .bills import Bill
from .budget import Budget
from .notes import Note
from .plans import Plan