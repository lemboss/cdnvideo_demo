from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import DuplicateCity, RepositoryError
from app.domain.models import City, Coordinates
from app.repositories.models import CityORM


class SqlAlchemyCityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, city_id: int) -> City | None:
        result = await self._session.execute(select(CityORM).where(CityORM.id == city_id))
        city = result.scalar_one_or_none()
        return _to_domain(city) if city else None

    async def get_by_normalized_name(self, normalized_name: str) -> City | None:
        result = await self._session.execute(
            select(CityORM).where(CityORM.normalized_name == normalized_name)
        )
        city = result.scalar_one_or_none()
        return _to_domain(city) if city else None

    async def list(self, *, offset: int, limit: int) -> tuple[list[City], int]:
        total_result = await self._session.execute(select(func.count()).select_from(CityORM))
        total = int(total_result.scalar_one())
        rows = await self._session.execute(
            select(CityORM).order_by(CityORM.name, CityORM.id).offset(offset).limit(limit)
        )
        return [_to_domain(city) for city in rows.scalars().all()], total

    async def list_all(self) -> list[City]:
        rows = await self._session.execute(select(CityORM).order_by(CityORM.id))
        return [_to_domain(city) for city in rows.scalars().all()]

    async def create(self, *, name: str, normalized_name: str, coordinates: Coordinates) -> City:
        city = CityORM(
            name=name,
            normalized_name=normalized_name,
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
        )
        self._session.add(city)
        try:
            await self._session.commit()
            await self._session.refresh(city)
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateCity(details={"normalized_name": normalized_name}) from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError() from exc
        return _to_domain(city)

    async def delete(self, city_id: int) -> bool:
        result = await self._session.execute(select(CityORM).where(CityORM.id == city_id))
        city = result.scalar_one_or_none()
        if city is None:
            return False
        await self._session.delete(city)
        try:
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError() from exc
        return True


def _to_domain(city: CityORM) -> City:
    return City(
        id=city.id,
        name=city.name,
        normalized_name=city.normalized_name,
        coordinates=Coordinates(latitude=city.latitude, longitude=city.longitude),
        created_at=city.created_at,
        updated_at=city.updated_at,
    )
