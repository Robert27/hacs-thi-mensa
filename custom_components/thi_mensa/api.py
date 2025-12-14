"""API client for THI Mensa GraphQL endpoint."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from .const import API_URL


class THIMensaApiError(Exception):
    """Base exception for API errors."""


class THIMensaApiCommunicationError(THIMensaApiError):
    """Raised when the API cannot be reached."""


class THIMensaApiResponseError(THIMensaApiError):
    """Raised when the API returns an error payload."""


class THIMensaApiClient:
    """Handle requests to the Neuland GraphQL API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize client."""
        self._session = session

    async def async_fetch_meals(self, locations: list[str]) -> dict[str, Any]:
        """Fetch meals for the given locations."""
        query = """
        query Meals($locations: [LocationInput!]!) {
          food(locations: $locations) {
            foodData {
              timestamp
              meals {
                id
                mealId
                category
                restaurant
                name { de en }
                prices { student employee guest }
                allergens
                flags
                variants {
                  id
                  mealId
                  restaurant
                  name { de en }
                  prices { student employee guest }
                  allergens
                  flags
                  additional
                  originalLanguage
                  static
                  parent {
                    id
                    category
                    name { de en }
                  }
                }
                originalLanguage
                static
              }
            }
            errors { location message }
          }
        }
        """
        payload = {"query": query, "variables": {"locations": locations}}
        try:
            async with async_timeout.timeout(15):
                response = await self._session.post(API_URL, json=payload)
                response.raise_for_status()
                data = await response.json()
        except TimeoutError as exception:
            msg = f"Timeout while calling Neuland API: {exception}"
            raise THIMensaApiCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Communication error while calling Neuland API: {exception}"
            raise THIMensaApiCommunicationError(msg) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Unexpected error while calling Neuland API: {exception}"
            raise THIMensaApiError(msg) from exception

        if "errors" in data:
            error_message = str(data["errors"])
            raise THIMensaApiResponseError(error_message)

        if not data.get("data") or not data["data"].get("food"):
            error_message = "Malformed response from Neuland API"
            raise THIMensaApiResponseError(error_message)

        return data["data"]["food"]
