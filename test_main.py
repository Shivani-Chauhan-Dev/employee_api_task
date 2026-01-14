import pytest  # type: ignore[import]

from main import app, db, User, Employee


@pytest.fixture()
def client():
    """
    Configure the app for testing and provide a test client.
    A fresh in-memory SQLite database is created for each test.
    """
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as client:
        yield client


def register_user(client, email="user@example.com", password="password123"):
    return client.post(
        "/api/register",
        json={"email": email, "password": password},
    )


def login_user(client, email="user@example.com", password="password123"):
    return client.post(
        "/api/login",
        json={"email": email, "password": password},
    )


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- Auth tests ----------

def test_register_user_success(client):
    resp = register_user(client)
    assert resp.status_code == 201
    assert resp.get_json()["message"] == "User registered successfully"


def test_register_user_duplicate_email(client):
    register_user(client)
    resp = register_user(client)
    assert resp.status_code == 400
    assert "Email already registered" in resp.get_json().get("error", "")


def test_login_success(client):
    register_user(client)
    resp = login_user(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data


def test_login_invalid_credentials(client):
    register_user(client)
    resp = login_user(client, password="wrongpassword")
    assert resp.status_code == 401


def test_login_user_not_found(client):
    resp = login_user(client)
    assert resp.status_code == 404


# ---------- Employee tests ----------

def get_auth_token(client) -> str:
    register_user(client)
    resp = login_user(client)
    return resp.get_json()["token"]


def test_create_employee_requires_token(client):
    resp = client.post(
        "/api/employees",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert resp.status_code == 401


def test_create_employee_success(client):
    token = get_auth_token(client)
    resp = client.post(
        "/api/employees",
        headers=auth_header(token),
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "department": "IT",
            "role": "Engineer",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"


def test_create_employee_duplicate_email(client):
    token = get_auth_token(client)
    payload = {"name": "John Doe", "email": "john@example.com"}

    client.post("/api/employees", headers=auth_header(token), json=payload)
    resp = client.post("/api/employees", headers=auth_header(token), json=payload)

    assert resp.status_code == 400
    assert "Email already exists" in resp.get_json().get("error", "")


def test_list_employees(client):
    token = get_auth_token(client)

    # create two employees
    client.post(
        "/api/employees",
        headers=auth_header(token),
        json={"name": "John Doe", "email": "john@example.com"},
    )
    client.post(
        "/api/employees",
        headers=auth_header(token),
        json={"name": "Jane Smith", "email": "jane@example.com"},
    )

    resp = client.get("/api/employees/", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_get_employee_and_not_found(client):
    token = get_auth_token(client)

    # create employee
    resp_create = client.post(
        "/api/employees",
        headers=auth_header(token),
        json={"name": "John Doe", "email": "john@example.com"},
    )
    emp_id = resp_create.get_json()["id"]

    # valid fetch
    resp = client.get(f"/api/employees/{emp_id}/", headers=auth_header(token))
    assert resp.status_code == 200

    # non-existing
    resp = client.get("/api/employees/does-not-exist/", headers=auth_header(token))
    assert resp.status_code == 404


def test_update_employee_and_email_conflict(client):
    token = get_auth_token(client)

    # create two employees
    resp1 = client.post(
        "/api/employees",
        headers=auth_header(token),
        json={"name": "John", "email": "john@example.com"},
    )
    resp2 = client.post(
        "/api/employees",
        headers=auth_header(token),
        json={"name": "Jane", "email": "jane@example.com"},
    )

    emp1_id = resp1.get_json()["id"]
    emp2_id = resp2.get_json()["id"]

    # successful update
    resp_ok = client.put(
        f"/api/employees/{emp1_id}/",
        headers=auth_header(token),
        json={"name": "John Updated"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["name"] == "John Updated"

    # conflict: try to change emp2's email to emp1's email
    resp_conflict = client.put(
        f"/api/employees/{emp2_id}/",
        headers=auth_header(token),
        json={"email": "john@example.com"},
    )
    assert resp_conflict.status_code == 400
    assert "Email already taken" in resp_conflict.get_json().get("error", "")


def test_delete_employee(client):
    token = get_auth_token(client)

    # create employee
    resp_create = client.post(
        "/api/employees",
        headers=auth_header(token),
        json={"name": "John Doe", "email": "john@example.com"},
    )
    emp_id = resp_create.get_json()["id"]

    # delete
    resp_del = client.delete(
        f"/api/employees/{emp_id}/", headers=auth_header(token)
    )
    assert resp_del.status_code == 204

    # verify it's gone
    resp_get = client.get(f"/api/employees/{emp_id}/", headers=auth_header(token))
    assert resp_get.status_code == 404


