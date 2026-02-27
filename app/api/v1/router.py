from re import search

from fastapi import APIRouter

from app.api.v1.endpoints import data
from app.api.v1.endpoints import search
from app.api.v1.endpoints import agent

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(search.router, prefix="/search", tags =["search"])
api_router.include_router(agent.router, prefix="/chat", tags=["agent"])