"""
Pytest configuration and fixtures for the activity management API tests.
Provides test isolation through fixture-based activity database copying.
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def activity_data():
    """
    Fixture that provides a fresh copy of the activities database.
    This ensures each test has isolated data and modifications don't affect other tests.
    """
    return deepcopy(activities)


@pytest.fixture
def client(activity_data, monkeypatch):
    """
    Fixture that provides a TestClient with fresh activity data.
    Uses monkeypatch to replace the app's activities with a test copy before each test.
    """
    # Replace the app's activities with our test copy
    monkeypatch.setattr("src.app.activities", activity_data)
    
    # Return a TestClient instance for making HTTP requests
    return TestClient(app)
