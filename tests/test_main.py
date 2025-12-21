import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.api.app.main import app, get_db
from apps.api.app.db import Base

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. Override the Dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# 3. Create the Test Client
client = TestClient(app)


# 4. The Setup Fixture
# Before every test, create the tables. After, destroy them.
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


def test_upload_and_search_flow(mocker):
    # 1. Mock the extractor
    # Make sure this string is unique so we can spot it easily
    fake_content = "MAGIC_STRING_INVOICE_100"
    mocker.patch("apps.api.app.main.extract_text_generic", return_value="MAGIC_STRING_INVOICE_100")

    # 2. UPLOAD
    upload_url = "/attachments"  # (Keep this as your working URL)
    response = client.post(
        upload_url,
        params={"user_id": 123},
        files={"files": ("test.pdf", b"fake content", "application/pdf")}
    )
    assert response.status_code == 200

    db = TestingSessionLocal()

    db.close()

    # 3. SEARCH
    # We search for "MAGIC" which is definitely in our fake content
    search_url = "/notes/search"  # Check if this needs to be /tasks/search ?
    search_response = client.get(
        search_url,
        params={"q": "MAGIC", "user_id": 123}
    )

    assert search_response.status_code == 200
    results = search_response.json()

    # This print helps us see what the search actually returned
    print(f"Search Results: {results}")

    assert len(results) > 0