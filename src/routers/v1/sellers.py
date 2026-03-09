from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.configurations.database import get_async_session
from src.schemas import (
    IncomingSeller,
    ReturnedSeller,
    ReturnedAllSellers,
    PatchSeller,
    ReturnedSellerWithBooks,
)
from src.services import SellerService
from src.services.dependencies import get_current_seller
from src.models.sellers import Seller

sellers_router = APIRouter(prefix="/seller", tags=["sellers"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@sellers_router.post("/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: IncomingSeller, session: DBSession):
    try:
        new_seller = await SellerService(session).create_seller(seller)
    except IntegrityError as e:
        if "sellers_table_e_mail_key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seller with this email already exists"
            )
        raise
    return new_seller


@sellers_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    sellers = await SellerService(session).get_all_sellers()
    return {"sellers": sellers}


@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_single_seller(
    seller_id: int,
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller),
):
    if seller_id != current_seller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only view your own profile"
        )
    seller = await SellerService(session).get_seller_by_id(seller_id, load_books=True)
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    return seller


@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(
    seller_id: int,
    patch_data: PatchSeller,
    session: DBSession,
):
    updated = await SellerService(session).update_seller(seller_id, patch_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    return updated


@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(
    seller_id: int,
    session: DBSession,
):
    deleted = await SellerService(session).delete_seller(seller_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)