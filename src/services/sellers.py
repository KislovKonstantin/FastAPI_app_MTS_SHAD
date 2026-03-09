__all__ = ["SellerService"]

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.models.sellers import Seller
from src.schemas.sellers import IncomingSeller, PatchSeller
from src.services.auth import get_password_hash

class SellerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_seller(self, seller_data: IncomingSeller) -> Seller:
        existing = await self.get_seller_by_email(seller_data.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")
        hashed_password = get_password_hash(seller_data.password)
        new_seller = Seller(
            first_name=seller_data.first_name,
            last_name=seller_data.last_name,
            email=seller_data.email,
            password=hashed_password,
        )
        self.session.add(new_seller)
        try:
            await self.session.flush()
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Email already registered")
        return new_seller

    async def get_all_sellers(self) -> list[Seller]:
        query = select(Seller)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_seller_by_id(self, seller_id: int, load_books: bool = False) -> Seller | None:
        query = select(Seller).where(Seller.id == seller_id)
        if load_books:
            query = query.options(selectinload(Seller.books))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_seller_by_email(self, email: str) -> Seller | None:
        query = select(Seller).where(Seller.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_seller(self, seller_id: int, patch_data: PatchSeller) -> Seller | None:
        seller = await self.session.get(Seller, seller_id)
        if not seller:
            return None

        if patch_data.first_name is not None:
            seller.first_name = patch_data.first_name
        if patch_data.last_name is not None:
            seller.last_name = patch_data.last_name
        if patch_data.email is not None:
            seller.email = patch_data.email

        await self.session.flush()
        return seller

    async def delete_seller(self, seller_id: int) -> bool:
        seller = await self.session.get(Seller, seller_id)
        if seller:
            await self.session.delete(seller)
            return True
        return False