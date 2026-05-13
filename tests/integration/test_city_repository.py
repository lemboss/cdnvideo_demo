import pytest

from app.core.database import Database
from app.domain.errors import DuplicateCity
from app.domain.models import Coordinates
from app.repositories.sqlalchemy_city_repository import SqlAlchemyCityRepository


@pytest.mark.asyncio
async def test_repository_creates_lists_and_deletes_city(tmp_path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'repo.db'}")
    await database.connect()
    await database.create_schema()
    try:
        async with database.session() as session:
            repository = SqlAlchemyCityRepository(session)
            city = await repository.create(
                name="Москва",
                normalized_name="москва",
                coordinates=Coordinates(latitude=55.755864, longitude=37.617698),
            )

            fetched = await repository.get_by_id(city.id)
            items, total = await repository.list(offset=0, limit=10)
            deleted = await repository.delete(city.id)

            assert fetched is not None
            assert fetched.name == "Москва"
            assert total == 1
            assert len(items) == 1
            assert deleted is True
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_repository_rejects_duplicate_normalized_name(tmp_path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'duplicate.db'}")
    await database.connect()
    await database.create_schema()
    try:
        async with database.session() as session:
            repository = SqlAlchemyCityRepository(session)
            await repository.create(
                name="Москва",
                normalized_name="москва",
                coordinates=Coordinates(latitude=55.755864, longitude=37.617698),
            )

            with pytest.raises(DuplicateCity):
                await repository.create(
                    name="москва",
                    normalized_name="москва",
                    coordinates=Coordinates(latitude=55.755864, longitude=37.617698),
                )
    finally:
        await database.close()
