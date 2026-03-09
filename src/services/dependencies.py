from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations.database import get_async_session
from src.configurations.settings import settings
from src.models.sellers import Seller
from src.services.sellers import SellerService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


async def get_current_seller(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> Seller:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        seller_id: int = payload.get("sub")
        if seller_id is None:
            raise credentials_exception
        seller_id = int(seller_id)
    except JWTError:
        raise credentials_exception

    seller = await SellerService(session).get_seller_by_id(seller_id)
    if seller is None:
        raise credentials_exception
    return seller