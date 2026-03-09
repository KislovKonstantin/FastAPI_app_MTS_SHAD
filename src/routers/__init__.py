from fastapi import APIRouter

from .v1 import books_router, sellers_router, token_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(books_router)
api_router.include_router(sellers_router)
api_router.include_router(token_router)
