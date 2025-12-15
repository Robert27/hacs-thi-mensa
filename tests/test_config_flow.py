"""Tests for config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ingolstadt_mensa import config_flow
from custom_components.ingolstadt_mensa.api import (
    THIMensaApiClient,
    THIMensaApiCommunicationError,
    THIMensaApiResponseError,
)
from custom_components.ingolstadt_mensa.const import (
    CONF_LOCATION,
    CONF_PRICE_GROUP,
    DEFAULT_LOCATIONS,
)


@pytest.fixture
def hass_mock():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def flow():
    """Create a config flow instance."""
    flow_instance = config_flow.THIMensaConfigFlow()
    flow_instance.hass = MagicMock(spec=HomeAssistant)
    flow_instance.hass.data = {}
    return flow_instance


@pytest.mark.asyncio
async def test_config_flow_user_step_no_input(flow):
    """Test config flow user step with no input."""
    flow.hass.data = {}
    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "data_schema" in result


@pytest.mark.asyncio
async def test_config_flow_user_step_success(flow, sample_api_response):
    """Test successful config flow."""
    flow.hass.data = {}
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()

    with (
        patch(
            "custom_components.ingolstadt_mensa.config_flow.async_get_clientsession"
        ) as mock_get_session,
        patch(
            "custom_components.ingolstadt_mensa.config_flow.THIMensaApiClient"
        ) as mock_client_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_client = MagicMock(spec=THIMensaApiClient)
        mock_client.async_fetch_meals = AsyncMock(
            return_value=sample_api_response["data"]["food"]
        )
        mock_client_class.return_value = mock_client

        user_input = {
            CONF_LOCATION: DEFAULT_LOCATIONS[0],
            CONF_PRICE_GROUP: "student",
        }
        result = await flow.async_step_user(user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == user_input


@pytest.mark.asyncio
async def test_config_flow_user_step_connection_error(flow):
    """Test config flow with connection error."""
    flow.hass.data = {}

    with (
        patch(
            "custom_components.ingolstadt_mensa.config_flow.async_get_clientsession"
        ) as mock_get_session,
        patch(
            "custom_components.ingolstadt_mensa.config_flow.THIMensaApiClient"
        ) as mock_client_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_client = MagicMock(spec=THIMensaApiClient)
        mock_client.async_fetch_meals = AsyncMock(
            side_effect=THIMensaApiCommunicationError("Connection failed")
        )
        mock_client_class.return_value = mock_client

        user_input = {
            CONF_LOCATION: DEFAULT_LOCATIONS[0],
            CONF_PRICE_GROUP: "student",
        }
        result = await flow.async_step_user(user_input)

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "connection"


@pytest.mark.asyncio
async def test_config_flow_user_step_invalid_location(flow):
    """Test config flow with invalid location."""
    flow.hass.data = {}

    with (
        patch(
            "custom_components.ingolstadt_mensa.config_flow.async_get_clientsession"
        ) as mock_get_session,
        patch(
            "custom_components.ingolstadt_mensa.config_flow.THIMensaApiClient"
        ) as mock_client_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_client = MagicMock(spec=THIMensaApiClient)
        mock_client.async_fetch_meals = AsyncMock(
            side_effect=THIMensaApiResponseError("Invalid location")
        )
        mock_client_class.return_value = mock_client

        user_input = {
            CONF_LOCATION: "InvalidLocation",
            CONF_PRICE_GROUP: "student",
        }
        result = await flow.async_step_user(user_input)

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_location"
