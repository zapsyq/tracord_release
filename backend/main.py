from fastapi import FastAPI
from app.routers.user import router as user_router
from app.routers.cities import router as cities_router
from app.routers.trips import router as trips_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.agent import router as agent_router
from app.routers.bills import router as bills_router
from app.routers.notes import router as notes_router
from app.routers.budget import router as budget_router
from app.routers.plans import router as plans_router

app = FastAPI()

app.include_router(user_router)
app.include_router(cities_router)
app.include_router(trips_router)
app.include_router(agent_router)
app.include_router(bills_router)
app.include_router(notes_router)
app.include_router(budget_router)
app.include_router(plans_router)

# CORS：App 用 Bearer Token（Header），不依赖 Cookie，无需 allow_credentials
# 开发期放开所有源；上线应改为指定源列表
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

