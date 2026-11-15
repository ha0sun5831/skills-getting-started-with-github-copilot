from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def activity_state():
    original = deepcopy(activities)
    initial = {
        "Chess Club": {
            "description": "Learn chess strategies",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["alice@example.com", "bob@example.com"],
        },
        "Art Club": {
            "description": "Explore visual arts",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": [],
        },
    }
    try:
        activities.clear()
        activities.update(deepcopy(initial))
        yield initial
    finally:
        activities.clear()
        activities.update(original)


@pytest.fixture
def client(activity_state):
    with TestClient(app) as test_client:
        yield test_client
