import asyncio
from typing import Generator, AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from icecream import ic
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import select

from src.configurations.settings import settings
from src.models import books, sellers
from src.models.base import BaseModel
from src.models.books import Book
from src.models.sellers import Seller
from src.services.auth import get_password_hash, create_access_token

from sqlalchemy.pool import NullPool

async_test_engine = create_async_engine(
    settings.database_test_url,
    echo=True,
    poolclass=NullPool,
)

async_test_session = async_sessionmaker(async_test_engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop()
    yield loop
    try:
        loop.close()
    except Exception as e:
        ic(e)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> None:
    async with async_test_engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)
        await connection.run_sync(BaseModel.metadata.create_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_test_engine.connect() as connection:
        async with async_test_session(bind=connection) as session:
            yield session
            await session.rollback()


@pytest.fixture(scope="function")
def override_get_async_session(db_session):
    async def _override_get_async_session():
        yield db_session
    return _override_get_async_session


@pytest.fixture(scope="function")
def test_app(override_get_async_session):
    from src.configurations.database import get_async_session
    from src.main import app

    app.dependency_overrides[get_async_session] = override_get_async_session
    return app


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app):
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def test_seller(db_session):
    seller = Seller(
        first_name="Test",
        last_name="Seller",
        email="test@example.com",
        password=get_password_hash("testpassword")
    )
    db_session.add(seller)
    await db_session.flush()
    return seller


@pytest_asyncio.fixture(scope="function")
async def seller_token(test_seller, async_client):
    response = await async_client.post(
        "/api/v1/token/",
        data={"username": test_seller.email, "password": "testpassword"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]