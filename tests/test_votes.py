def create_voter(client, name="Ana Gómez", email="ana@example.com"):
    return client.post("/voters", json={"name": name, "email": email, "password": "votante123"})


def create_candidate(client, name="Carlos Ruiz"):
    return client.post("/candidates", json={"name": name, "party": "Partido Verde"})


def test_cast_vote_updates_voter_and_candidate(client):
    voter = create_voter(client).json()
    candidate = create_candidate(client).json()

    response = client.post("/votes", json={"voter_id": voter["id"], "candidate_id": candidate["id"]})

    assert response.status_code == 201
    assert client.get(f"/voters/{voter['id']}").json()["has_voted"] is True
    assert client.get(f"/candidates/{candidate['id']}").json()["votes"] == 1


def test_same_voter_cannot_vote_twice(client):
    voter = create_voter(client).json()
    candidate = create_candidate(client).json()
    payload = {"voter_id": voter["id"], "candidate_id": candidate["id"]}

    assert client.post("/votes", json=payload).status_code == 201
    assert client.post("/votes", json=payload).status_code == 409


def test_missing_candidate_returns_not_found(client):
    voter = create_voter(client).json()

    response = client.post("/votes", json={"voter_id": voter["id"], "candidate_id": 999})

    assert response.status_code == 404


def test_duplicate_email_returns_conflict(client):
    assert create_voter(client).status_code == 201
    assert create_voter(client, name="Otra Persona").status_code == 409


def test_voter_cannot_be_registered_as_candidate(client):
    assert create_voter(client).status_code == 201

    response = create_candidate(client, name="  ana   gómez ")

    assert response.status_code == 409


def test_statistics_without_votes_are_zero(client):
    candidate = create_candidate(client).json()

    response = client.get("/votes/statistics")

    assert response.status_code == 200
    assert response.json() == {
        "total_votes": 0,
        "voters_who_voted": 0,
        "candidates": [
            {
                "candidate_id": candidate["id"],
                "candidate_name": candidate["name"],
                "votes": 0,
                "percentage": 0.0,
            }
        ],
    }


def test_login_returns_jwt(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_invalid_login_is_rejected(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})

    assert response.status_code == 401


def test_voter_login_returns_voter_token(client):
    create_voter(client)

    response = client.post(
        "/auth/voter-login",
        json={"email": "ana@example.com", "password": "votante123"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "voter"


def test_protected_write_without_token_returns_401(client):
    from app.auth import require_admin
    from app.main import app

    app.dependency_overrides.pop(require_admin, None)
    try:
        response = client.post(
            "/voters",
            json={"name": "Sin Token", "email": "sin-token@example.com", "password": "votante123"},
        )
    finally:
        app.dependency_overrides[require_admin] = lambda: "test-admin"

    assert response.status_code == 401


def test_voter_cannot_vote_for_another_voter(client):
    voter = create_voter(client).json()
    candidate = create_candidate(client).json()

    response = client.post(
        "/votes",
        json={"voter_id": voter["id"] + 1, "candidate_id": candidate["id"]},
    )

    assert response.status_code == 403
