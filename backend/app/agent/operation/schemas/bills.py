from pydantic import BaseModel, Field

#agent工具校验
class BillItem(BaseModel):
    amount: float = Field(description="消费金额")
    category: int = Field(
        description=
                    """
                    消费分类：
                    1=交通（打车、公交、地铁、飞机、火车等）
                    2=餐饮（吃饭、早餐、午餐、晚餐、咖啡、奶茶等）
                    3=购物（买东西、商品、纪念品等）
                    4=住宿（酒店、民宿等）
                    5=娱乐（景区门票、电影、游玩等）
                    根据用户消费内容选择对应编号。
                    """
    )

class BillInput(BaseModel):
    city_name: str = Field(description="消费所在城市")
    bills: list[BillItem] = Field(description="消费明细列表，支持一次记多笔")
