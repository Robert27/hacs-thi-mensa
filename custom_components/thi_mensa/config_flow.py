"""Config flow for THI Mensa."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    THIMensaApiClient,
    THIMensaApiCommunicationError,
    THIMensaApiResponseError,
)
from .const import (
    CONF_LOCATION,
    CONF_PRICE_GROUP,
    DEFAULT_LOCATIONS,
    DOMAIN,
    LOGGER,
    PRICE_GROUPS,
)


class THIMensaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for THI Mensa."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_location(user_input[CONF_LOCATION])
            except THIMensaApiCommunicationError as err:
                LOGGER.warning(
                    "Validation for location '%s' failed due to communication error: %s",
                    user_input[CONF_LOCATION],
                    err,
                )
                errors["base"] = "connection"
            except THIMensaApiResponseError as err:
                LOGGER.info(
                    "Validation for location '%s' failed with response error: %s",
                    user_input[CONF_LOCATION],
                    err,
                )
                errors["base"] = "invalid_location"
            else:
                await self.async_set_unique_id(user_input[CONF_LOCATION])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_LOCATION], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOCATION,
                        default=(user_input or {}).get(
                            CONF_LOCATION, DEFAULT_LOCATIONS[0]
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=DEFAULT_LOCATIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Required(
                        CONF_PRICE_GROUP,
                        default=(user_input or {}).get(
                            CONF_PRICE_GROUP, PRICE_GROUPS[0]
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=PRICE_GROUPS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def _validate_location(self, location: str) -> None:
        """Check that the chosen location responds with data."""
        session = async_get_clientsession(self.hass)
        client = THIMensaApiClient(session=session)
        result = await client.async_fetch_meals([location])
        if result.get("errors"):
            raise THIMensaApiResponseError(str(result["errors"]))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return THIMensaOptionsFlowHandler(config_entry)


class THIMensaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for THI Mensa."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options handler with the config entry."""
        self.config_entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            try:
                await self._validate_location(user_input[CONF_LOCATION])
            except THIMensaApiCommunicationError as err:
                LOGGER.warning(
                    "Options validation for location '%s' failed due to communication error: %s",
                    user_input[CONF_LOCATION],
                    err,
                )
                errors["base"] = "connection"
            except THIMensaApiResponseError as err:
                LOGGER.info(
                    "Options validation for location '%s' failed with response error: %s",
                    user_input[CONF_LOCATION],
                    err,
                )
                errors["base"] = "invalid_location"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOCATION,
                        default=current.get(CONF_LOCATION, DEFAULT_LOCATIONS[0]),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=DEFAULT_LOCATIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Required(
                        CONF_PRICE_GROUP,
                        default=current.get(CONF_PRICE_GROUP, PRICE_GROUPS[0]),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=PRICE_GROUPS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def _validate_location(self, location: str) -> None:
        session = async_get_clientsession(self.hass)
        client = THIMensaApiClient(session=session)
        result = await client.async_fetch_meals([location])
        if result.get("errors"):
            raise THIMensaApiResponseError(str(result["errors"]))
