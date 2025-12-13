"""Constants for THI Mensa integration."""

from logging import Logger, getLogger

DOMAIN = "thi_mensa"
LOGGER: Logger = getLogger(__package__)

API_URL = "https://api.neuland.app/graphql"
DEFAULT_LOCATIONS = [
    "IngolstadtMensa",
    "NeuburgMensa",
    "Reimanns",
    "Canisius",
]
PRICE_GROUPS = ["student", "employee", "guest"]

CONF_PRICE_GROUP = "price_group"
CONF_LOCATION = "location"
