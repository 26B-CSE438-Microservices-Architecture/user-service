import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app.models.address  # noqa: F401 – registers Address with Base
import app.models.favorite  # noqa: F401 – registers UserFavorite with Base
import app.models.password_reset  # noqa: F401 – registers PasswordResetToken with Base
from app.database import get_db
from app.main import app
from app.models.address import Address
from app.models.favorite import UserFavorite
from app.models.password_reset import PasswordResetToken
from app.models.user import Base, User, UserRole
from app.routers.users import hash_password

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/userdb_test",
)

engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS user_role CASCADE"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS user_role CASCADE"))


@pytest_asyncio.fixture
async def db_session():
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        name="Test",
        surname="User",
        email="test@example.com",
        phone="5551234567",
        hashed_password=hash_password("password123"),
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_address(db_session: AsyncSession, test_user: User) -> Address:
    address = Address(
        user_id=test_user.id,
        address_title="Home",
        city="Istanbul",
        district="Besiktas",
        neighborhood="Levent",
        street="Test Caddesi",
        building_no="1",
        floor="2",
        apartment_no="3",
        phone="5551234567",
    )
    db_session.add(address)
    await db_session.commit()
    await db_session.refresh(address)
    return address
