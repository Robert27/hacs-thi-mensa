"""DataUpdateCoordinator for THI Mensa."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER
from .api import (
    THIMensaApiClient,
    THIMensaApiCommunicationError,
    THIMensaApiError,
    THIMensaApiResponseError,
)


def _filter_today_meals(food_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Return meals only for today's date."""
    today_iso = date.today().isoformat()
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
                raise THIMensaApiResponseError(str(result["errors"]))
            return _filter_today_meals(result.get("foodData", []))
        except THIMensaApiResponseError as exception:
            raise UpdateFailed(exception) from exception
        except THIMensaApiCommunicationError as exception:
            raise UpdateFailed(exception) from exception
        except THIMensaApiError as exception:
            raise UpdateFailed(exception) from exception
