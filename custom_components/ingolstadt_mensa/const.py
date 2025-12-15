"""Constants for the Ingolstadt Mensa integration."""

import re
from logging import Logger, getLogger

DOMAIN = "ingolstadt_mensa"
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


def format_location_name(location: str) -> str:
    """
    Format location name for display.

    Example: 'IngolstadtMensa' -> 'Ingolstadt Mensa'
    """
    if not location:
        return "Ingolstadt Mensa"

    formatted = re.sub(r"(?<!^)(?<! )([A-Z])", r" \1", location)
    return formatted.strip()


def format_price_group_name(price_group: str) -> str:
    """
    Format price group name for display.

    Example: 'student' -> 'Student'
    """
    if not price_group:
        return price_group
    return price_group.capitalize()


def slugify_location_name(location: str) -> str:
    """
    Convert location name to a slug for use in entity IDs.

    Example: 'IngolstadtMensa' -> 'ingolstadt_mensa'
             'Canisius' -> 'canisius'
    """
    if not location:
        return "ingolstadt_mensa"

    # Convert camelCase to snake_case
    slug = re.sub(r"(?<!^)(?<! )([A-Z])", r"_\1", location)
    # Convert to lowercase and replace spaces with underscores
    slug = slug.lower().replace(" ", "_")
    return slug
