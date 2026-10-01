import src.app as activity_app
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 3,
            "participants": ["existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(activity_app, "activities", activities)

    with TestClient(activity_app.app) as test_client:
        yield test_client


# Verifies the app root redirects to the static activity page.
def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


# Verifies activity listing returns participant data without cache storage.
def test_get_activities_returns_data_without_caching(client):
    # Arrange
    expected_participants = ["existing@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants
    assert response.headers["cache-control"] == "no-store"


# Verifies a successful signup appears in the next activity listing.
def test_signup_adds_participant(client):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email in participants


# Verifies duplicate signup returns 400 without changing participants.
def test_duplicate_signup_does_not_change_participants(client):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == [email]


# Verifies signup for an unknown activity returns 404 without changing data.
def test_signup_unknown_activity_returns_not_found(client):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Unknown%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == ["existing@mergington.edu"]


# Verifies unregister removes a participant from the next activity listing.
def test_unregister_removes_participant(client):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.delete("/activities/Chess%20Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Chess Club"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email not in participants


# Verifies unregistering a missing participant returns 404 without changing data.
def test_unregister_missing_participant_returns_not_found(client):
    # Arrange
    email = "missing@mergington.edu"

    # Act
    response = client.delete("/activities/Chess%20Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == ["existing@mergington.edu"]


# Verifies unregistering from an unknown activity returns 404 without changing data.
def test_unregister_unknown_activity_returns_not_found(client):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown%20Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == [email]