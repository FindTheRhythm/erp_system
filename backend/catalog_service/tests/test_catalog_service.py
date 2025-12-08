import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


@pytest.fixture
def client(monkeypatch):
    # In-memory SQLite for isolated tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Импортируем модели, чтобы они зарегистрировались в metadata
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Stub external integrations
    async def fake_create_inventory_operation(*args, **kwargs):
        return True

    async def fake_get_sku_total_weight(*args, **kwargs):
        return 0

    def fake_publish_event(event_type, data):
        return None

    monkeypatch.setattr(
        "app.routers.catalog.create_inventory_operation",
        fake_create_inventory_operation,
    )
    monkeypatch.setattr(
        "app.routers.catalog.get_sku_total_weight",
        fake_get_sku_total_weight,
    )
    monkeypatch.setattr(
        "app.routers.catalog.rabbitmq_client.publish_event",
        fake_publish_event,
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _admin_headers():
    return {"X-User-Role": "admin"}


def test_create_units_and_sku_flow(client):
    # Create weight unit
    resp = client.post(
        "/catalog/units",
        json={"name": "kg", "type": "weight", "description": "килограмм"},
        headers=_admin_headers(),
    )
    assert resp.status_code == 201
    weight_unit = resp.json()
    assert weight_unit["name"] == "kg"
    assert weight_unit["type"] == "weight"

    # Create quantity unit
    resp = client.post(
        "/catalog/units",
        json={"name": "pcs", "type": "quantity", "description": "pieces"},
        headers=_admin_headers(),
    )
    assert resp.status_code == 201
    qty_unit = resp.json()
    assert qty_unit["name"] == "pcs"
    assert qty_unit["type"] == "quantity"

    # Create SKU
    resp = client.post(
        "/catalog/skus",
        json={
            "code": "ABCD1234",
            "name": "Test SKU",
            "weight": "10",
            "weight_unit_id": weight_unit["id"],
            "quantity": "5",
            "quantity_unit_id": qty_unit["id"],
            "description": "test item",
            "price": "100",
            "price_unit_id": None,
            "status": "available",
            "photo_url": None,
        },
        headers=_admin_headers(),
    )
    assert resp.status_code == 201
    sku = resp.json()
    assert sku["code"].startswith("ABCD-")
    assert sku["name"] == "Test SKU"
    assert sku["status"] == "available"

    sku_id = sku["id"]

    # Get SKU by id
    resp = client.get(f"/catalog/skus/{sku_id}", headers=_admin_headers())
    assert resp.status_code == 200
    fetched = resp.json()
    assert fetched["id"] == sku_id
    assert fetched["code"] == sku["code"]

    # List SKUs
    resp = client.get("/catalog/skus", headers=_admin_headers())
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == sku_id

