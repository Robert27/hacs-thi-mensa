"""DataUpdateCoordinator for Ingolstadt Mensa."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    THIMensaApiClient,
    THIMensaApiCommunicationError,
    THIMensaApiError,
    THIMensaApiResponseError,
)


def _parse_entry_date(entry_timestamp: str | None) -> date | None:
    """Convert a timestamp from the API into a date object."""
    if not entry_timestamp:
        return None

    parsed_datetime = dt_util.parse_datetime(entry_timestamp)
    if parsed_datetime:
        return dt_util.as_local(parsed_datetime).date()

    try:
        return datetime.fromisoformat(entry_timestamp).date()
    except ValueError:
        return None


def _filter_meals_by_date(food_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Return meals for today and tomorrow."""
    today = dt_util.now().date()
    tomorrow = today + timedelta(days=1)

    today_meals: list[dict[str, Any]] = []
    tomorrow_meals: list[dict[str, Any]] = []
    today_timestamp = today.isoformat()
    tomorrow_timestamp = tomorrow.isoformat()

    for entry in food_data:
        entry_date = _parse_entry_date(entry.get("timestamp"))
        if not entry_date:
            continue

        if entry_date == today:
            today_meals = entry.get("meals", [])
            today_timestamp = entry_date.isoformat()
        elif entry_date == tomorrow:
            tomorrow_meals = entry.get("meals", [])
            tomorrow_timestamp = entry_date.isoformat()

    return {
        "today": {
            "timestamp": today_timestamp,
            "meals": today_meals,
        },
        "tomorrow": {
            "timestamp": tomorrow_timestamp,
            "meals": tomorrow_meals,
        },
    }


class THIMensaDataUpdateCoordinator(DataUpdateCoordinator):
    """Manage fetching meals from the API."""

    config_entry: Any

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        client: THIMensaApiClient = self.config_entry.runtime_data.client
        location = self.config_entry.runtime_data.location
        try:
            result = await client.async_fetch_meals([location])
            if result.get("errors"):
                error_message = str(result["errors"])
                raise UpdateFailed(error_message)
            return _filter_meals_by_date(result.get("foodData", []))
        except (THIMensaApiResponseError, THIMensaApiCommunicationError) as exception:
            raise UpdateFailed(exception) from exception
        except THIMensaApiError as exception:
            raise UpdateFailed(exception) from exception
