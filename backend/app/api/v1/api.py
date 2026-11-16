from fastapi import APIRouter

from backend.app.api.v1.endpoints import admin, analitica, encuestas

api_router = APIRouter()

api_router.include_router(encuestas.router, prefix="/encuestas", tags=["Encuestas"])
api_router.include_router(analitica.router, prefix="/encuestas", tags=["Analítica"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])
