"""THI Mensa integration."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import THIMensaApiClient
from .const import CONF_LOCATION, CONF_PRICE_GROUP, DOMAIN, LOGGER
from .coordinator import THIMensaDataUpdateCoordinator
from .data import THIMensaData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import THIMensaConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: THIMensaConfigEntry,
) -> bool:
    """Set up THI Mensa integration."""

    coordinator = THIMensaDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=2),
    )

    entry.runtime_data = THIMensaData(
        client=THIMensaApiClient(
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        location=entry.options.get(CONF_LOCATION, entry.data[CONF_LOCATION]),
        price_group=entry.options.get(CONF_PRICE_GROUP, entry.data[CONF_PRICE_GROUP]),
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: THIMensaConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: THIMensaConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
