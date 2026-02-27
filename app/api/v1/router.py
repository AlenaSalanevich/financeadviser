from fastapi import APIRouter

from app.api.v1.endpoints import data

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(data.router, prefix="/data", tags=["data"])