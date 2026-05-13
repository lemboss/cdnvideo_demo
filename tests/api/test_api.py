import pytest


@pytest.mark.asyncio
async def test_health_is_public(api_client) -> None:
    client, _geocoder = api_client

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_city_endpoints_require_api_key(api_client) -> None:
    client, _geocoder = api_client

    response = await client.get("/cities")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_create_list_get_delete_city(api_client, api_key: str) -> None:
    client, geocoder = api_client
    headers = {"X-API-Key": api_key}

    created = await client.post("/cities", json={"name": "Москва"}, headers=headers)
    duplicate = await client.post("/cities", json={"name": "  москва  "}, headers=headers)
    listed = await client.get("/cities", headers=headers)
    fetched = await client.get(f"/cities/{created.json()['id']}", headers=headers)
    deleted = await client.delete(f"/cities/{created.json()['id']}", headers=headers)
    missing = await client.get(f"/cities/{created.json()['id']}", headers=headers)

    assert created.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == created.json()["id"]
    assert listed.json()["total"] == 1
    assert fetched.json()["name"] == "Москва"
    assert deleted.status_code == 204
    assert missing.status_code == 404
    assert geocoder.calls == ["Москва"]


@pytest.mark.asyncio
async def test_nearest_returns_sorted_two_cities(api_client, api_key: str) -> None:
    client, _geocoder = api_client
    headers = {"X-API-Key": api_key}
    await client.post("/cities", json={"name": "Москва"}, headers=headers)
    await client.post("/cities", json={"name": "Санкт-Петербург"}, headers=headers)
    await client.post("/cities", json={"name": "Казань"}, headers=headers)

    response = await client.get("/cities/nearest?lat=55.75&lon=37.61", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert [item["name"] for item in data] == ["Москва", "Санкт-Петербург"]
    assert data[0]["distance_km"] < data[1]["distance_km"]


@pytest.mark.asyncio
async def test_validation_error_uses_uniform_format(api_client, api_key: str) -> None:
    client, _geocoder = api_client

    response = await client.get("/cities/nearest?lat=200&lon=37", headers={"X-API-Key": api_key})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["request_id"]


@pytest.mark.asyncio
async def test_cors_allowlist(api_client) -> None:
    client, _geocoder = api_client

    response = await client.options(
        "/cities",
        headers={
            "Origin": "https://client.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://client.example"
