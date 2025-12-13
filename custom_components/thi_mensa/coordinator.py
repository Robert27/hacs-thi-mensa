"""DataUpdateCoordinator for THI Mensa."""

from __future__ import annotations

from datetime import date, datetime
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
        return datetime.fromisoformat(entry_timestamp.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _filter_today_meals(food_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Return meals for today or the next available date."""

    today = dt_util.now().date()
    next_entry: dict[str, Any] | None = None

    for entry in food_data:
        entry_date = _parse_entry_date(entry.get("timestamp"))
        if not entry_date:
            continue

        if entry_date == today:
            return {"timestamp": entry_date.isoformat(), "meals": entry.get("meals", [])}

        if entry_date > today and (
            next_entry is None
            or _parse_entry_date(next_entry.get("timestamp")) is None
            or entry_date < _parse_entry_date(next_entry.get("timestamp"))
        ):
            next_entry = entry

    if next_entry:
        next_date = _parse_entry_date(next_entry.get("timestamp")) or today
        return {"timestamp": next_date.isoformat(), "meals": next_entry.get("meals", [])}

    return {"timestamp": today.isoformat(), "meals": []}


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
            return _filter_today_meals(result.get("foodData", []))
        except (THIMensaApiResponseError, THIMensaApiCommunicationError) as exception:
            raise UpdateFailed(exception) from exception
        except THIMensaApiError as exception:
            raise UpdateFailed(exception) from exception
