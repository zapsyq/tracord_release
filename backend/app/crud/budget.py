#导入会话工厂
from app.config.db_config import AsyncSession
#获取操作数据库的方法
from sqlalchemy import select, and_
#导入预算模型
from app.models.budget import Budget

from decimal import Decimal


class BudgetRepository:
    #效果同操作用户数据库
    def __init__(self, session: AsyncSession):
        self.session = session

    #设置预算（同用户+城市+分类只保留一条，自动更新金额）
    async def set_budget(self, user_id: int, adcode: str, category: int, amount: Decimal, custom_category: str | None = None):
        async with self.session.begin():
            stmt = select(Budget).where(
                and_(
                    Budget.user_id == user_id,
                    Budget.adcode == adcode,
                    Budget.category == category,
                )
            )
            existing = await self.session.scalar(stmt)
            if existing:
                existing.amount = amount
                existing.custom_category = custom_category
                return existing
            budget = Budget(user_id=user_id, adcode=adcode, category=category, amount=amount, custom_category=custom_category)
            self.session.add(budget)
            return budget

    #获取用户预算（可选按城市过滤）
    async def get_budgets(self, user_id: int, adcode: str | None = None):
        async with self.session.begin():
            conditions = [Budget.user_id == user_id]
            if adcode:
                conditions.append(Budget.adcode == adcode)
            stmt = select(Budget).where(and_(*conditions)).order_by(Budget.update_time.desc())
            result = await self.session.scalars(stmt)
            return result.all()

    #获取单个预算
    async def get_budget(self, user_id: int, budget_id: int):
        async with self.session.begin():
            stmt = select(Budget).where(and_(Budget.id == budget_id, Budget.user_id == user_id))
            return await self.session.scalar(stmt)

    #删除预算
    async def delete_budget(self, user_id: int, budget_id: int):
        async with self.session.begin():
            stmt = select(Budget).where(and_(Budget.id == budget_id, Budget.user_id == user_id))
            budget = await self.session.scalar(stmt)
            if budget:
                await self.session.delete(budget)
                return True
            return False
