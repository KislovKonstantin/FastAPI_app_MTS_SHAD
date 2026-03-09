from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.schemas import IncomingBook, PatchBook, ReturnedAllBooks, ReturnedBook
from src.services import BookService
from src.services.dependencies import get_current_seller
from src.models.sellers import Seller

books_router = APIRouter(prefix="/books", tags=["books"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@books_router.get("/", response_model=ReturnedAllBooks)
async def get_all_books(session: DBSession):
    books = await BookService(session).get_all_books()
    return {"books": books}


@books_router.post("/", response_model=ReturnedBook, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: IncomingBook,
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller),
):
    book_data = book.model_dump()
    book_data["seller_id"] = current_seller.id
    if book.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create book for another seller")
    new_book = await BookService(session).add_book(IncomingBook(**book_data))
    if new_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    return new_book


@books_router.get("/{book_id}", response_model=ReturnedBook)
async def get_single_book(book_id: int, session: DBSession):
    book = await BookService(session).get_single_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, session: DBSession):
    deleted = await BookService(session).delete_book(book_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@books_router.put("/{book_id}", response_model=ReturnedBook)
async def update_book(
    book_id: int,
    new_book_data: PatchBook,
    session: DBSession,
    current_seller: Seller = Depends(get_current_seller),
):
    book = await BookService(session).get_single_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if book.seller_id != current_seller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only update your own books"
        )
    if new_book_data.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change book owner")
    updated = await BookService(session).update_book(book_id, new_book_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book or seller not found")
    return updated


@books_router.patch("/{book_id}", response_model=ReturnedBook)
async def patch_book(
    book_id: int,
    patch_data: PatchBook,
    session: DBSession,
):
    updated = await BookService(session).partial_update_book(book_id, patch_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book or seller not found")
    return updated