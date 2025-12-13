"""DataUpdateCoordinator for THI Mensa."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    THIMensaApiClient,
    THIMensaApiCommunicationError,
    THIMensaApiError,
    THIMensaApiResponseError,
)


def _filter_today_meals(food_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Return meals only for today's date."""
    today_iso = dt_util.now().date().isoformat()
    for entry in food_data:
        if entry.get("timestamp") == today_iso:
            return {"timestamp": today_iso, "meals": entry.get("meals", [])}
    return {"timestamp": today_iso, "meals": []}


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
