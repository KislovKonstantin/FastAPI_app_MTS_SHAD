from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.services.auth import verify_password, create_access_token
from src.services.sellers import SellerService
from src.schemas.token import Token

token_router = APIRouter(prefix="/token", tags=["token"])


@token_router.post("/", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session),
):
    seller = await SellerService(session).get_seller_by_email(form_data.username)
    if not seller or not verify_password(form_data.password, seller.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(seller.id)})
    return Token(access_token=access_token)