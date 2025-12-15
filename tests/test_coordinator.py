"""Tests for data coordinator."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.thi_mensa.coordinator import (
    THIMensaDataUpdateCoordinator,
    _filter_meals_by_date,
    _parse_entry_date,
)


def test_parse_entry_date():
    """Test date parsing from timestamp."""
    # Test ISO format with timezone
    timestamp = "2025-01-15T12:00:00+00:00"
    parsed = _parse_entry_date(timestamp)
    assert isinstance(parsed, date)
    assert parsed.year == 2025
    assert parsed.month == 1
    assert parsed.day == 15

    # Test ISO format without timezone
    timestamp = "2025-01-15T12:00:00"
    parsed = _parse_entry_date(timestamp)
    assert isinstance(parsed, date)
    assert parsed.year == 2025

    # Test None
    assert _parse_entry_date(None) is None

    # Test invalid format
    assert _parse_entry_date("invalid") is None


def test_filter_meals_by_date():
    """Test filtering meals by today and tomorrow."""
    today = dt_util.now().date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    food_data = [
        {
            "timestamp": yesterday.isoformat(),
            "meals": [{"id": "old-meal", "name": {"de": "Altes Gericht"}}],
        },
        {
            "timestamp": today.isoformat(),
            "meals": [{"id": "today-meal-1", "name": {"de": "Heutiges Gericht 1"}}],
        },
        {
            "timestamp": tomorrow.isoformat(),
            "meals": [{"id": "tomorrow-meal-1", "name": {"de": "Morgiges Gericht 1"}}],
        },
    ]

    result = _filter_meals_by_date(food_data)

    assert "today" in result
    assert "tomorrow" in result
    assert len(result["today"]["meals"]) == 1
    assert len(result["tomorrow"]["meals"]) == 1
    assert result["today"]["meals"][0]["id"] == "today-meal-1"
    assert result["tomorrow"]["meals"][0]["id"] == "tomorrow-meal-1"
    assert result["today"]["timestamp"] == today.isoformat()
    assert result["tomorrow"]["timestamp"] == tomorrow.isoformat()


def test_filter_meals_by_date_no_matches():
    """Test filtering when no meals match today or tomorrow."""
    yesterday = dt_util.now().date() - timedelta(days=1)
    last_week = yesterday - timedelta(days=7)

    food_data = [
        {
            "timestamp": yesterday.isoformat(),
            "meals": [{"id": "old-meal"}],
        },
        {
            "timestamp": last_week.isoformat(),
            "meals": [{"id": "older-meal"}],
        },
    ]

    result = _filter_meals_by_date(food_data)

    assert "today" in result
    assert "tomorrow" in result
    assert len(result["today"]["meals"]) == 0
    assert len(result["tomorrow"]["meals"]) == 0


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_update_success(
    mock_report, mock_config_entry, sample_meal_data
):
    """Test successful coordinator update."""
    from custom_components.thi_mensa.api import THIMensaApiClient

    coordinator = THIMensaDataUpdateCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        name="test",
        update_interval=timedelta(hours=1),
    )
    coordinator.config_entry = mock_config_entry

    # Mock the runtime data
    mock_config_entry.runtime_data = MagicMock()
    mock_config_entry.runtime_data.client = MagicMock(spec=THIMensaApiClient)
    mock_config_entry.runtime_data.client.async_fetch_meals = AsyncMock(
        return_value=sample_meal_data
    )
    mock_config_entry.runtime_data.location = "IngolstadtMensa"

    result = await coordinator._async_update_data()

    assert "today" in result
    assert "tomorrow" in result


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_update_with_errors(mock_report, mock_config_entry):
    """Test coordinator update with API errors."""
    from custom_components.thi_mensa.api import (
        THIMensaApiClient,
        THIMensaApiResponseError,
    )
    from homeassistant.helpers.update_coordinator import UpdateFailed

    coordinator = THIMensaDataUpdateCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        name="test",
        update_interval=timedelta(hours=1),
    )
    coordinator.config_entry = mock_config_entry

    mock_config_entry.runtime_data = MagicMock()
    mock_config_entry.runtime_data.client = MagicMock(spec=THIMensaApiClient)
    mock_config_entry.runtime_data.client.async_fetch_meals = AsyncMock(
        side_effect=THIMensaApiResponseError("API error")
    )
    mock_config_entry.runtime_data.location = "IngolstadtMensa"

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


def test_parse_entry_date_various_formats():
    """Test date parsing with various timestamp formats."""
    # Test ISO format with Z
    assert _parse_entry_date("2025-01-15T12:00:00Z") is not None

    # Test date only
    assert _parse_entry_date("2025-01-15") is not None

    # Test empty string
    assert _parse_entry_date("") is None

    # Test invalid date
    assert _parse_entry_date("2025-13-45") is None


def test_filter_meals_by_date_multiple_entries_same_day():
    """Test filtering when multiple entries exist for the same day."""
    today = dt_util.now().date()

    food_data = [
        {
            "timestamp": today.isoformat(),
            "meals": [{"id": "meal-1"}],
        },
        {
            "timestamp": today.isoformat(),
            "meals": [{"id": "meal-2"}],
        },
    ]

    result = _filter_meals_by_date(food_data)

    # Should use the last entry for today
    assert len(result["today"]["meals"]) == 1
    assert result["today"]["meals"][0]["id"] == "meal-2"


def test_filter_meals_by_date_empty_food_data():
    """Test filtering with empty food data."""
    result = _filter_meals_by_date([])

    assert "today" in result
    assert "tomorrow" in result
    assert len(result["today"]["meals"]) == 0
    assert len(result["tomorrow"]["meals"]) == 0


def test_filter_meals_by_date_missing_timestamp():
    """Test filtering when entries have missing timestamps."""
    food_data = [
        {
            "timestamp": None,
            "meals": [{"id": "meal-1"}],
        },
        {
            "meals": [{"id": "meal-2"}],  # Missing timestamp key
        },
    ]

    result = _filter_meals_by_date(food_data)

    assert len(result["today"]["meals"]) == 0
    assert len(result["tomorrow"]["meals"]) == 0


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_update_with_communication_error(
    mock_report, mock_config_entry
):
    """Test coordinator update with communication error."""
    from custom_components.thi_mensa.api import (
        THIMensaApiClient,
        THIMensaApiCommunicationError,
    )
    from homeassistant.helpers.update_coordinator import UpdateFailed

    coordinator = THIMensaDataUpdateCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        name="test",
        update_interval=timedelta(hours=1),
    )
    coordinator.config_entry = mock_config_entry

    mock_config_entry.runtime_data = MagicMock()
    mock_config_entry.runtime_data.client = MagicMock(spec=THIMensaApiClient)
    mock_config_entry.runtime_data.client.async_fetch_meals = AsyncMock(
        side_effect=THIMensaApiCommunicationError("Connection failed")
    )
    mock_config_entry.runtime_data.location = "IngolstadtMensa"

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_update_with_api_errors_in_response(
    mock_report, mock_config_entry
):
    """Test coordinator update when API returns errors in response."""
    from custom_components.thi_mensa.api import THIMensaApiClient
    from homeassistant.helpers.update_coordinator import UpdateFailed

    coordinator = THIMensaDataUpdateCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        name="test",
        update_interval=timedelta(hours=1),
    )
    coordinator.config_entry = mock_config_entry

    mock_config_entry.runtime_data = MagicMock()
    mock_config_entry.runtime_data.client = MagicMock(spec=THIMensaApiClient)
    mock_config_entry.runtime_data.client.async_fetch_meals = AsyncMock(
        return_value={"errors": [{"message": "Invalid location"}]}
    )
    mock_config_entry.runtime_data.location = "InvalidLocation"

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
