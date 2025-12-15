"""Pytest configuration and fixtures."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from custom_components.ingolstadt_mensa.api import THIMensaApiClient
from custom_components.ingolstadt_mensa.const import DEFAULT_LOCATIONS, PRICE_GROUPS


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    return AsyncMock()


@pytest.fixture
def api_client(mock_session):
    """Create an API client with a mocked session."""
    return THIMensaApiClient(session=mock_session)


@pytest.fixture
def sample_meal_data():
    """Sample meal data from the API."""
    return {
        "foodData": [
            {
                "timestamp": "2025-01-15T00:00:00Z",
                "meals": [
                    {
                        "id": "1",
                        "mealId": "meal-1",
                        "category": "main",
                        "restaurant": "IngolstadtMensa",
                        "name": {
                            "de": "Spaghetti Bolognese",
                            "en": "Spaghetti Bolognese",
                        },
                        "prices": {"student": 3.5, "employee": 4.5, "guest": 5.5},
                        "allergens": ["gluten", "milk"],
                        "flags": ["vegetarian"],
                    },
                    {
                        "id": "2",
                        "mealId": "meal-2",
                        "category": "salad",
                        "restaurant": "IngolstadtMensa",
                        "name": {"de": "Griechischer Salat", "en": "Greek Salad"},
                        "prices": {"student": 2.5, "employee": 3.0, "guest": 3.5},
                        "allergens": [],
                        "flags": ["vegetarian", "vegan"],
                    },
                ],
            },
            {
                "timestamp": "2025-01-16T00:00:00Z",
                "meals": [
                    {
                        "id": "3",
                        "mealId": "meal-3",
                        "category": "main",
                        "restaurant": "IngolstadtMensa",
                        "name": {"de": "Pizza Margherita", "en": "Pizza Margherita"},
                        "prices": {"student": 4.0, "employee": 5.0, "guest": 6.0},
                        "allergens": ["gluten", "milk"],
                        "flags": ["vegetarian"],
                    },
                ],
            },
        ],
        "errors": [],
    }


@pytest.fixture
def sample_api_response(sample_meal_data):
    """Sample API response."""
    return {"data": {"food": sample_meal_data}}


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test-entry-id"
    entry.data = {
        "location": DEFAULT_LOCATIONS[0],
        "price_group": PRICE_GROUPS[0],
    }
    entry.options = {}
    return entry
