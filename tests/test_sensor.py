"""Tests for sensor entities."""

from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from custom_components.thi_mensa.sensor import MensaMealSensor


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "today": {
            "timestamp": "2025-01-15",
            "meals": [
                {
                    "id": "1",
                    "mealId": "meal-1",
                    "name": {"de": "Spaghetti Bolognese", "en": "Spaghetti Bolognese"},
                    "category": "main",
                    "restaurant": "IngolstadtMensa",
                    "prices": {"student": 3.5, "employee": 4.5, "guest": 5.5},
                    "allergens": ["gluten", "milk"],
                    "flags": ["vegetarian"],
                },
                {
                    "id": "2",
                    "name": {"de": "Griechischer Salat", "en": "Greek Salad"},
                    "category": "salad",
                    "prices": {"student": 2.5, "employee": 3.0, "guest": 3.5},
                    "allergens": [],
                    "flags": ["vegetarian", "vegan"],
                },
                {
                    "id": "3",
                    "name": {"de": "Kuchen", "en": "Cake"},
                    "category": "dessert",
                    "prices": {"student": 1.5},
                    "allergens": ["eggs"],
                    "flags": [],
                },
                {
                    "id": "4",
                    "name": {"de": "Suppe", "en": "Soup"},
                    "category": "soup",
                    "prices": {"student": 2.0},
                    "allergens": [],
                    "flags": [],
                },
            ],
        },
        "tomorrow": {
            "timestamp": "2025-01-16",
            "meals": [
                {
                    "id": "3",
                    "name": {"de": "Pizza Margherita", "en": "Pizza Margherita"},
                    "category": "main",
                    "prices": {"student": 4.0},
                    "allergens": ["gluten", "milk"],
                    "flags": ["vegetarian"],
                },
            ],
        },
    }
    return coordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test-entry"
    entry.data = {"location": "IngolstadtMensa", "price_group": "student"}
    entry.options = {}
    return entry


def test_sensor_name_german(mock_coordinator, mock_entry):
    """Test sensor name in German."""
    mock_coordinator.hass.config.language = "de"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor.name == "Spaghetti Bolognese"


def test_sensor_name_english(mock_coordinator, mock_entry):
    """Test sensor name in English."""
    mock_coordinator.hass.config.language = "en"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor.name == "Spaghetti Bolognese"


def test_sensor_name_language_fallback(mock_coordinator, mock_entry):
    """Test sensor name falls back to English when German not available."""
    mock_coordinator.hass.config.language = "de"
    # Modify meal to only have English name
    mock_coordinator.data["today"]["meals"][0]["name"] = {"en": "English Only Meal"}
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor.name == "English Only Meal"


def test_sensor_name_fallback(mock_coordinator, mock_entry):
    """Test sensor name fallback when meal not available."""
    mock_coordinator.hass.config.language = "de"
    sensor = MensaMealSensor(
        mock_coordinator, mock_entry, 5, "today"
    )  # Index out of range

    assert sensor.name == "Gericht 6"


def test_sensor_name_fallback_english(mock_coordinator, mock_entry):
    """Test sensor name fallback in English."""
    mock_coordinator.hass.config.language = "en"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 5, "today")

    assert sensor.name == "Meal 6"


def test_sensor_name_empty_coordinator_data(mock_coordinator, mock_entry):
    """Test sensor name when coordinator data is None."""
    mock_coordinator.hass.config.language = "de"
    mock_coordinator.data = None
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor.name == "Gericht 1"


def test_sensor_available(mock_coordinator, mock_entry):
    """Test sensor availability."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.available is True

    sensor_unavailable = MensaMealSensor(mock_coordinator, mock_entry, 10, "today")
    assert sensor_unavailable.available is False


def test_sensor_available_no_coordinator_data(mock_coordinator, mock_entry):
    """Test sensor availability when coordinator data is None."""
    mock_coordinator.data = None
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.available is False


def test_sensor_native_value(mock_coordinator, mock_entry):
    """Test sensor native value (price)."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.native_value == 3.5


def test_sensor_native_value_different_price_groups(mock_coordinator, mock_entry):
    """Test sensor native value with different price groups."""
    mock_entry.data["price_group"] = "employee"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.native_value == 4.5

    mock_entry.data["price_group"] = "guest"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.native_value == 5.5


def test_sensor_native_value_from_options(mock_coordinator, mock_entry):
    """Test sensor native value uses options over data."""
    mock_entry.options = {"price_group": "employee"}
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.native_value == 4.5


def test_sensor_native_value_none(mock_coordinator, mock_entry):
    """Test sensor native value when meal not available."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 10, "today")
    assert sensor.native_value is None


def test_sensor_native_value_missing_price(mock_coordinator, mock_entry):
    """Test sensor native value when price is missing."""
    mock_entry.data["price_group"] = "guest"
    sensor = MensaMealSensor(
        mock_coordinator, mock_entry, 2, "today"
    )  # Meal 3 has no guest price
    assert sensor.native_value is None


def test_sensor_native_value_rounding(mock_coordinator, mock_entry):
    """Test sensor native value rounding to 2 decimal places."""
    mock_coordinator.data["today"]["meals"][0]["prices"]["student"] = 3.555
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.native_value == 3.56


def test_sensor_suggested_display_precision(mock_coordinator, mock_entry):
    """Test sensor suggested display precision."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.suggested_display_precision == 2


def test_sensor_native_unit_of_measurement(mock_coordinator, mock_entry):
    """Test sensor native unit of measurement."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.native_unit_of_measurement == "EUR"


def test_sensor_icon(mock_coordinator, mock_entry):
    """Test sensor icon based on category."""
    sensor_main = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor_main.icon == "mdi:silverware-fork-knife"

    sensor_salad = MensaMealSensor(mock_coordinator, mock_entry, 1, "today")
    assert sensor_salad.icon == "mdi:bowl-mix"

    sensor_dessert = MensaMealSensor(mock_coordinator, mock_entry, 2, "today")
    assert sensor_dessert.icon == "mdi:cake"

    sensor_soup = MensaMealSensor(mock_coordinator, mock_entry, 3, "today")
    assert sensor_soup.icon == "mdi:bowl"


def test_sensor_icon_unknown_category(mock_coordinator, mock_entry):
    """Test sensor icon with unknown category."""
    mock_coordinator.data["today"]["meals"][0]["category"] = "unknown"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.icon == "mdi:food"


def test_sensor_icon_no_category(mock_coordinator, mock_entry):
    """Test sensor icon when category is None."""
    mock_coordinator.data["today"]["meals"][0]["category"] = None
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.icon == "mdi:food"


def test_sensor_icon_desert_spelling(mock_coordinator, mock_entry):
    """Test sensor icon handles 'desert' spelling variant."""
    mock_coordinator.data["today"]["meals"][0]["category"] = "desert"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor.icon == "mdi:cake"


def test_sensor_extra_state_attributes(mock_coordinator, mock_entry):
    """Test sensor extra state attributes."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    attributes = sensor.extra_state_attributes

    assert "name_de" in attributes
    assert "name_en" in attributes
    assert "category" in attributes
    assert "restaurant" in attributes
    assert "price_student" in attributes
    assert "price_employee" in attributes
    assert "price_guest" in attributes
    assert "allergens" in attributes
    assert "flags" in attributes
    assert "date" in attributes
    assert attributes["name_de"] == "Spaghetti Bolognese"
    assert attributes["name_en"] == "Spaghetti Bolognese"
    assert attributes["category"] == "main"
    assert attributes["restaurant"] == "IngolstadtMensa"
    assert attributes["allergens"] == ["gluten", "milk"]
    assert attributes["flags"] == ["vegetarian"]
    assert attributes["date"] == "2025-01-15"
    assert attributes["price_student"] == 3.5
    assert attributes["price_employee"] == 4.5
    assert attributes["price_guest"] == 5.5


def test_sensor_extra_state_attributes_empty(mock_coordinator, mock_entry):
    """Test sensor extra state attributes when meal not available."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 10, "today")
    attributes = sensor.extra_state_attributes
    assert attributes == {}


def test_sensor_extra_state_attributes_tomorrow(mock_coordinator, mock_entry):
    """Test sensor extra state attributes for tomorrow."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "tomorrow")
    attributes = sensor.extra_state_attributes
    assert attributes["date"] == "2025-01-16"


def test_sensor_preferred_language_de(mock_coordinator, mock_entry):
    """Test preferred language detection for German."""
    mock_coordinator.hass.config.language = "de"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor._get_preferred_language() == "de"


def test_sensor_preferred_language_en(mock_coordinator, mock_entry):
    """Test preferred language detection for English."""
    mock_coordinator.hass.config.language = "en"
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor._get_preferred_language() == "en"


def test_sensor_preferred_language_de_variants(mock_coordinator, mock_entry):
    """Test preferred language detection for German variants."""
    for lang in ["de", "de_DE", "de_AT", "de_CH"]:
        mock_coordinator.hass.config.language = lang
        sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
        assert sensor._get_preferred_language() == "de", f"Failed for {lang}"


def test_sensor_preferred_language_none(mock_coordinator, mock_entry):
    """Test preferred language detection when language is None."""
    mock_coordinator.hass.config.language = None
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor._get_preferred_language() == "en"


def test_sensor_preferred_language_exception(mock_coordinator, mock_entry):
    """Test preferred language detection handles exceptions."""
    del mock_coordinator.hass.config.language
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor._get_preferred_language() == "en"


def test_strip_restaurant_prefix(mock_coordinator, mock_entry):
    """Test restaurant prefix stripping."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor._strip_restaurant_prefix("THI Mensa: Spaghetti") == "Spaghetti"
    assert sensor._strip_restaurant_prefix("Ingolstadt Mensa - Pizza") == "Pizza"
    assert sensor._strip_restaurant_prefix("Regular Meal Name") == "Regular Meal Name"
    assert sensor._strip_restaurant_prefix(None) is None


def test_strip_restaurant_prefix_case_insensitive(mock_coordinator, mock_entry):
    """Test restaurant prefix stripping is case insensitive."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")

    assert sensor._strip_restaurant_prefix("thi mensa: Spaghetti") == "Spaghetti"
    assert sensor._strip_restaurant_prefix("INGOLSTADT MENSA - Pizza") == "Pizza"


def test_sensor_unique_id(mock_coordinator, mock_entry):
    """Test sensor unique ID."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    assert sensor._attr_unique_id == "test-entry-today-meal-1"

    sensor2 = MensaMealSensor(mock_coordinator, mock_entry, 2, "tomorrow")
    assert sensor2._attr_unique_id == "test-entry-tomorrow-meal-3"


def test_sensor_device_info(mock_coordinator, mock_entry):
    """Test sensor device info."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "today")
    device_info = sensor._attr_device_info

    assert device_info["identifiers"] == {("thi_mensa", "IngolstadtMensa-today")}
    assert "Ingolstadt Mensa - Today" in device_info["name"]


def test_sensor_device_info_tomorrow(mock_coordinator, mock_entry):
    """Test sensor device info for tomorrow."""
    sensor = MensaMealSensor(mock_coordinator, mock_entry, 0, "tomorrow")
    device_info = sensor._attr_device_info

    assert device_info["identifiers"] == {("thi_mensa", "IngolstadtMensa-tomorrow")}
    assert "Ingolstadt Mensa - Tomorrow" in device_info["name"]
