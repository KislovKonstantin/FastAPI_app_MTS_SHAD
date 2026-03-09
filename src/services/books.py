__all__ = ["BookService"]

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.books import Book
from src.models.sellers import Seller
from src.schemas.books import IncomingBook, PatchBook, ReturnedBook


class BookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_book(self, book: IncomingBook) -> Book | None:
        seller = await self.session.get(Seller, book.seller_id)
        if not seller:
            return None

        new_book = Book(
            title=book.title,
            author=book.author,
            year=book.year,
            pages=book.pages,
            seller_id=book.seller_id,
        )
        self.session.add(new_book)
        await self.session.flush()
        return new_book

    async def delete_book(self, book_id: int) -> bool:
        book = await self.session.get(Book, book_id)
        if book:
            await self.session.delete(book)
            return True
        return False

    async def update_book(self, book_id: int, new_book_data: ReturnedBook) -> Book | None:
        book = await self.session.get(Book, book_id)
        if not book:
            return None

        if new_book_data.seller_id != book.seller_id:
            seller = await self.session.get(Seller, new_book_data.seller_id)
            if not seller:
                return None

        book.title = new_book_data.title
        book.author = new_book_data.author
        book.year = new_book_data.year
        book.pages = new_book_data.pages
        book.seller_id = new_book_data.seller_id

        await self.session.flush()
        return book

    async def partial_update_book(self, book_id: int, patch_data: PatchBook) -> Book | None:
        book = await self.session.get(Book, book_id)
        if not book:
            return None

        if patch_data.seller_id is not None and patch_data.seller_id != book.seller_id:
            seller = await self.session.get(Seller, patch_data.seller_id)
            if not seller:
                return None
            book.seller_id = patch_data.seller_id

        if patch_data.title is not None:
            book.title = patch_data.title
        if patch_data.author is not None:
            book.author = patch_data.author
        if patch_data.year is not None:
            book.year = patch_data.year
        if patch_data.pages is not None:
            book.pages = patch_data.pages

        await self.session.flush()
        return book

    async def get_single_book(self, book_id: int) -> Book | None:
        return await self.session.get(Book, book_id)

    async def get_all_books(self) -> list[Book]:
        query = select(Book)
        result = await self.session.execute(query)
        return result.scalars().all()