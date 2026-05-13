from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.repositories.sqlalchemy_city_repository import SqlAlchemyCityRepository
from app.services.city_service import CityService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.db.session() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_city_service(
    request: Request,
    session: DbSessionDep,
) -> CityService:
    repository = SqlAlchemyCityRepository(session)
    return CityService(repository=repository, geocoder=request.app.state.geocoder)


CityServiceDep = Annotated[CityService, Depends(get_city_service)]
RequireApiKey = Depends(require_api_key)
