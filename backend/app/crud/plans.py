#导入会话工厂
from app.config.db_config import AsyncSession
#获取操作数据库的方法
from sqlalchemy import select, and_
#导入计划模型
from app.models.plans import Plan


class PlanRepository:
    #效果同操作用户数据库
    def __init__(self, session: AsyncSession):
        self.session = session

    #新增或更新计划（同一用户+城市只保留一条）
    async def set_plan(self, user_id: int, adcode: str, content: str):
        async with self.session.begin():
            stmt = select(Plan).where(
                and_(Plan.user_id == user_id, Plan.adcode == adcode)
            )
            existing = await self.session.scalar(stmt)
            if existing:
                existing.content = content
                return existing
            plan = Plan(user_id=user_id, adcode=adcode, content=content)
            self.session.add(plan)
            return plan

    #获取某城市计划
    async def get_plan(self, user_id: int, adcode: str):
        async with self.session.begin():
            stmt = select(Plan).where(
                and_(Plan.user_id == user_id, Plan.adcode == adcode)
            )
            return await self.session.scalar(stmt)

    #获取用户所有计划
    async def get_plans(self, user_id: int):
        async with self.session.begin():
            stmt = select(Plan).where(Plan.user_id == user_id).order_by(Plan.update_time.desc())
            result = await self.session.scalars(stmt)
            return result.all()

    #删除计划
    async def delete_plan(self, user_id: int, plan_id: int):
        async with self.session.begin():
            stmt = select(Plan).where(
                and_(Plan.id == plan_id, Plan.user_id == user_id)
            )
            plan = await self.session.scalar(stmt)
            if plan:
                await self.session.delete(plan)
                return True
            return False
