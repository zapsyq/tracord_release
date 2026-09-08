from app.crud.plans import PlanRepository
from fastapi import HTTPException


class PlanService:
    def __init__(self, repo: PlanRepository):
        self.repo = repo    # plans表的数据库操作

    #新增或更新计划
    async def set_plan(self, user_id: int, adcode: str, content: str):
        return await self.repo.set_plan(user_id=user_id, adcode=adcode, content=content)

    #获取某城市计划
    async def get_plan(self, user_id: int, adcode: str):
        return await self.repo.get_plan(user_id, adcode)

    #获取用户所有计划
    async def get_plans(self, user_id: int):
        return await self.repo.get_plans(user_id)

    #删除计划
    async def delete_plan(self, user_id: int, plan_id: int):
        result = await self.repo.delete_plan(user_id, plan_id)
        if not result:
            raise HTTPException(status_code=400, detail="计划不存在")
        return result
