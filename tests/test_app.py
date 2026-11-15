from copy import deepcopy

import pytest


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_details_without_mutating_state(client, activity_state):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activity_state
    assert client.get("/activities").json() == activity_state


def test_signup_adds_participant_and_preserves_other_data(client, activity_state):
    email = "student+chess@example.com"
    expected = deepcopy(activity_state)
    expected["Chess Club"]["participants"].append(email)

    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert client.get("/activities").json() == expected


def test_duplicate_signup_returns_error_without_adding_participant_twice(client):
    email = "new@example.com"
    first = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert first.status_code == 200
    after_first_signup = client.get("/activities").json()

    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Already signed up for this activity"}
    assert client.get("/activities").json() == after_first_signup


def test_signup_for_unknown_activity_returns_error_without_changes(client, activity_state):
    response = client.post(
        "/activities/Unknown/signup", params={"email": "new@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == activity_state


def test_unregister_removes_only_selected_participant_and_allows_signup(
    client, activity_state
):
    email = activity_state["Chess Club"]["participants"][0]
    expected = deepcopy(activity_state)
    expected["Chess Club"]["participants"].remove(email)

    response = client.delete(
        "/activities/Chess%20Club/unregister", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert client.get("/activities").json() == expected

    signup = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert signup.status_code == 200
    expected["Chess Club"]["participants"].append(email)
    assert client.get("/activities").json() == expected


def test_unregister_last_participant_leaves_empty_list(client, activity_state):
    email = "student+art@example.com"
    signup = client.post("/activities/Art%20Club/signup", params={"email": email})
    assert signup.status_code == 200

    response = client.delete(
        "/activities/Art%20Club/unregister", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Art Club"}
    assert client.get("/activities").json() == activity_state


@pytest.mark.parametrize(
    ("activity", "detail"),
    [
        ("Unknown", "Activity not found"),
        ("Chess%20Club", "Participant not found"),
    ],
)
def test_unregister_missing_activity_or_participant_returns_error_without_changes(
    client, activity_state, activity, detail
):
    response = client.delete(
        f"/activities/{activity}/unregister", params={"email": "missing@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": detail}
    assert client.get("/activities").json() == activity_state


@pytest.mark.parametrize(
    ("method", "endpoint"),
    [("POST", "signup"), ("DELETE", "unregister")],
)
def test_missing_email_returns_validation_error_without_changes(
    client, activity_state, method, endpoint
):
    response = client.request(method, f"/activities/Chess%20Club/{endpoint}")

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"] for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == activity_state
