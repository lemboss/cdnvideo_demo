from fastapi import APIRouter, Request, Response, status

from app.api.schemas import DependencyHealth, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request, response: Response) -> HealthResponse:
    settings = request.app.state.settings
    dependencies: dict[str, DependencyHealth] = {}

    try:
        await request.app.state.db.healthcheck()
        dependencies["database"] = DependencyHealth(status="ok")
    except Exception as exc:
        dependencies["database"] = DependencyHealth(status="error", detail=exc.__class__.__name__)

    if settings.rate_limit_enabled:
        try:
            await request.app.state.redis.ping()
            dependencies["redis"] = DependencyHealth(status="ok")
        except Exception as exc:
            dependencies["redis"] = DependencyHealth(status="error", detail=exc.__class__.__name__)
    else:
        dependencies["redis"] = DependencyHealth(status="skipped")

    overall_status = (
        "ok" if all(item.status in {"ok", "skipped"} for item in dependencies.values()) else "error"
    )
    if overall_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        dependencies=dependencies,
    )
