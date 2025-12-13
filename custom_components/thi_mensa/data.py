"""Custom types for THI Mensa."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import THIMensaApiClient
    from .coordinator import THIMensaDataUpdateCoordinator


type THIMensaConfigEntry = ConfigEntry[THIMensaData]


@dataclass
class THIMensaData:
    """Runtime data for the integration."""

    client: THIMensaApiClient
    coordinator: THIMensaDataUpdateCoordinator
    integration: Integration
    location: str
    price_group: str
