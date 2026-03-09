import pytest
from fastapi import status
from sqlalchemy import select

from src.models.sellers import Seller
from src.models.books import Book

API_V1_URL_PREFIX = "/api/v1/seller"


@pytest.mark.asyncio()
async def test_create_seller(async_client):
    data = {
        "first_name": "Robert",
        "last_name": "Martin",
        "e_mail": "robert.martin@example.com",
        "password": "secret123"
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    print(response.text)
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert result["first_name"] == "Robert"
    assert result["last_name"] == "Martin"
    assert result["email"] == "robert.martin@example.com"
    assert "id" in result
    assert "password" not in result


@pytest.mark.asyncio()
async def test_get_all_sellers(db_session, async_client):
    seller1 = Seller(
        first_name="Robert", last_name="Martin", email="robert.martin@example.com", password="hash"
    )
    seller2 = Seller(
        first_name="Martin", last_name="Robert", email="martin.robert@example.com", password="hash"
    )
    db_session.add_all([seller1, seller2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")
    print(response.json())

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["sellers"]
    assert len(data) == 2
    assert all("password" not in s for s in data)


@pytest.mark.asyncio()
async def test_get_single_seller_with_books(async_client, test_seller, seller_token):
    response = await async_client.get(
        f"/api/v1/seller/{test_seller.id}",
        headers={"Authorization": f"Bearer {seller_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_seller.id


@pytest.mark.asyncio()
async def test_get_single_seller_without_token(async_client, db_session):
    seller = Seller(
        first_name="Robert", last_name="Martin", email="robert.martin@example.com", password="hash"
    )
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{seller.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_update_seller(db_session, async_client):
    seller = Seller(
        first_name="Robert", last_name="Martin", email="robert.martin@example.com", password="hash"
    )
    db_session.add(seller)
    await db_session.flush()

    update_data = {
        "first_name": "Martin",
        "last_name": "Robert",
        "e_mail": "robert.martin@example.com"
    }
    response = await async_client.put(f"{API_V1_URL_PREFIX}/{seller.id}", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    updated = response.json()
    assert updated["first_name"] == "Martin"
    assert updated["last_name"] == "Robert"
    assert updated["email"] == "robert.martin@example.com"
    assert "id" in updated
    assert "password" not in updated


@pytest.mark.asyncio()
async def test_delete_seller(db_session, async_client, test_seller):
    delete_response = await async_client.delete(f"/api/v1/seller/{test_seller.id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()

    all_sellers = await db_session.execute(select(Seller))
    res = all_sellers.scalars().all()
    assert len(res) == 0


@pytest.mark.asyncio()
async def test_delete_seller_cascades_books(db_session, async_client, test_seller):
    book = Book(
        author="Lermontov",
        title="Mtziri",
        pages=510,
        year=2024,
        seller_id=test_seller.id
    )
    db_session.add(book)
    await db_session.flush()

    delete_response = await async_client.delete(f"/api/v1/seller/{test_seller.id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()

    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()
    assert len(res) == 0

@pytest.mark.asyncio()
async def test_token_creation(async_client, test_seller):
    response = await async_client.post(
        "/api/v1/token/",
        data={
            "username": test_seller.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"