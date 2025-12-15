"""Tests for API client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.thi_mensa.api import (
    THIMensaApiCommunicationError,
    THIMensaApiResponseError,
)


@pytest.mark.asyncio
async def test_async_fetch_meals_success(api_client, sample_api_response):
    """Test successful API fetch."""
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=sample_api_response)
    mock_response.raise_for_status = MagicMock()
    api_client._session.post = AsyncMock(return_value=mock_response)

    result = await api_client.async_fetch_meals(["IngolstadtMensa"])

    assert result == sample_api_response["data"]["food"]
    api_client._session.post.assert_called_once()


@pytest.mark.asyncio
async def test_async_fetch_meals_multiple_locations(api_client, sample_api_response):
    """Test API fetch with multiple locations."""
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=sample_api_response)
    mock_response.raise_for_status = MagicMock()
    api_client._session.post = AsyncMock(return_value=mock_response)

    result = await api_client.async_fetch_meals(["IngolstadtMensa", "NeuburgMensa"])

    assert result == sample_api_response["data"]["food"]
    api_client._session.post.assert_called_once()


@pytest.mark.asyncio
async def test_async_fetch_meals_timeout(api_client):
    """Test API timeout handling."""
    api_client._session.post = AsyncMock(side_effect=TimeoutError("Timeout"))

    with pytest.raises(THIMensaApiCommunicationError, match="Timeout"):
        await api_client.async_fetch_meals(["IngolstadtMensa"])


@pytest.mark.asyncio
async def test_async_fetch_meals_connection_error(api_client):
    """Test API connection error handling."""
    api_client._session.post = AsyncMock(
        side_effect=aiohttp.ClientError("Connection failed")
    )

    with pytest.raises(THIMensaApiCommunicationError, match="Communication error"):
        await api_client.async_fetch_meals(["IngolstadtMensa"])


@pytest.mark.asyncio
async def test_async_fetch_meals_socket_error(api_client):
    """Test API socket error handling."""
    import socket

    api_client._session.post = AsyncMock(
        side_effect=socket.gaierror("DNS resolution failed")
    )

    with pytest.raises(THIMensaApiCommunicationError, match="Communication error"):
        await api_client.async_fetch_meals(["IngolstadtMensa"])


@pytest.mark.asyncio
async def test_async_fetch_meals_api_errors(api_client):
    """Test API error response handling."""
    error_response = {"errors": [{"message": "Invalid location"}]}
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=error_response)
    mock_response.raise_for_status = MagicMock()
    api_client._session.post = AsyncMock(return_value=mock_response)

    with pytest.raises(THIMensaApiResponseError):
        await api_client.async_fetch_meals(["InvalidLocation"])


@pytest.mark.asyncio
async def test_async_fetch_meals_malformed_response(api_client):
    """Test malformed API response handling."""
    malformed_response = {"data": {}}  # Missing 'food' key
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=malformed_response)
    mock_response.raise_for_status = MagicMock()
    api_client._session.post = AsyncMock(return_value=mock_response)

    with pytest.raises(THIMensaApiResponseError, match="Malformed response"):
        await api_client.async_fetch_meals(["IngolstadtMensa"])


@pytest.mark.asyncio
async def test_async_fetch_meals_missing_data_key(api_client):
    """Test API response with missing data key."""
    malformed_response = {}  # Missing 'data' key entirely
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=malformed_response)
    mock_response.raise_for_status = MagicMock()
    api_client._session.post = AsyncMock(return_value=mock_response)

    with pytest.raises(THIMensaApiResponseError, match="Malformed response"):
        await api_client.async_fetch_meals(["IngolstadtMensa"])


@pytest.mark.asyncio
async def test_async_fetch_meals_http_error(api_client):
    """Test HTTP error handling."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Internal Server Error",
        )
    )
    api_client._session.post = AsyncMock(return_value=mock_response)

    with pytest.raises(THIMensaApiCommunicationError):
        await api_client.async_fetch_meals(["IngolstadtMensa"])


@pytest.mark.asyncio
async def test_async_fetch_meals_json_decode_error(api_client):
    """Test JSON decode error handling."""
    from custom_components.thi_mensa.api import THIMensaApiError

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
    )
    mock_response.raise_for_status = MagicMock()
    api_client._session.post = AsyncMock(return_value=mock_response)

    with pytest.raises(THIMensaApiError):
        await api_client.async_fetch_meals(["IngolstadtMensa"])
