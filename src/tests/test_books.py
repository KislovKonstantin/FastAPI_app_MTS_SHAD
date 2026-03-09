import pytest
from fastapi import status
from sqlalchemy import select

from src.models.books import Book

API_V1_URL_PREFIX = "/api/v1/books"


@pytest.mark.asyncio()
async def test_create_book(async_client, test_seller, seller_token):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": test_seller.id
    }
    headers = {"Authorization": f"Bearer {seller_token}"}
    response = await async_client.post("/api/v1/books/", json=data, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert result["pages"] == 300
    assert result["seller_id"] == test_seller.id
    assert "id" in result


@pytest.mark.asyncio()
async def test_create_book_without_token(async_client, test_seller):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": test_seller.id,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_create_book_with_old_year(async_client, test_seller, seller_token):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1000,
        "seller_id": test_seller.id,
    }
    headers = {"Authorization": f"Bearer {seller_token}"}
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio()
async def test_create_book_for_alien_seller(async_client, seller_token):
    data = {
        "title": "Alien",
        "author": "Author",
        "count_pages": 100,
        "year": 2026,
        "seller_id": 99999
    }
    headers = {"Authorization": f"Bearer {seller_token}"}
    response = await async_client.post("/api/v1/books/", json=data, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio()
async def test_get_books(db_session, async_client, test_seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2021,
        pages=104,
        seller_id=test_seller.id
    )
    book_2 = Book(
        author="Lermontov",
        title="Mziri",
        year=2021,
        pages=108,
        seller_id=test_seller.id
    )
    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["books"]
    assert len(data) == 2
    assert all("seller_id" in b for b in data)
    assert data[0]["seller_id"] == test_seller.id
    assert data[1]["seller_id"] == test_seller.id


@pytest.mark.asyncio()
async def test_get_single_book(db_session, async_client, test_seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id
    )
    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{book.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Eugeny Onegin"
    assert data["seller_id"] == test_seller.id


@pytest.mark.asyncio()
async def test_update_book(db_session, async_client, test_seller, seller_token):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id
    )
    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "count_pages": 250,
        "year": 2024,
        "id": book.id,
        "seller_id": test_seller.id,
    }
    headers = {"Authorization": f"Bearer {seller_token}"}
    response = await async_client.put(f"{API_V1_URL_PREFIX}/{book.id}", json=data, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    await db_session.refresh(book)
    assert book.title == "Mziri"
    assert book.author == "Lermontov"
    assert book.pages == 250
    assert book.year == 2024
    assert book.seller_id == test_seller.id


@pytest.mark.asyncio()
async def test_update_book_without_token(db_session, async_client, test_seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id
    )
    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
        "id": book.id,
        "seller_id": test_seller.id,
    }
    response = await async_client.put(f"{API_V1_URL_PREFIX}/{book.id}", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_delete_book(db_session, async_client, test_seller):
    book = Book(
        author="Lermontov",
        title="Mtziri",
        pages=510,
        year=2024,
        seller_id=test_seller.id
    )
    db_session.add(book)
    await db_session.flush()
    book_id = book.id

    delete_response = await async_client.delete(f"/api/v1/books/{book_id}")
    assert delete_response.status_code == 204

    await db_session.flush()

    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()
    assert len(res) == 0