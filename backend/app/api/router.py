from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.contacts import router as contacts_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(contacts_router)
