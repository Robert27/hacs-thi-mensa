"""Sensor platform for Ingolstadt Mensa meals."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION, CONF_PRICE_GROUP, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import THIMensaDataUpdateCoordinator
    from .data import THIMensaConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: THIMensaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up meal sensors based on the coordinator data."""
    coordinator: THIMensaDataUpdateCoordinator = entry.runtime_data.coordinator
    tracked: dict[int, MensaMealSensor] = {}

    def _sync_entities_from_data() -> None:
        meals = coordinator.data.get("meals", []) if coordinator.data else []
        required_slots = max(5, len(meals))
        new_entities: list[MensaMealSensor] = []

        for slot_index in range(required_slots):
            if slot_index in tracked:
                continue

            sensor = MensaMealSensor(coordinator, entry, slot_index)
            tracked[slot_index] = sensor
            new_entities.append(sensor)

        if new_entities:
            async_add_entities(new_entities)

    _sync_entities_from_data()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities_from_data))


class MensaMealSensor(CoordinatorEntity, SensorEntity):
    """Represents a single meal as a sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: THIMensaDataUpdateCoordinator,
        entry: THIMensaConfigEntry,
        slot_index: int,
    ) -> None:
        """Initialize the sensor with meal metadata."""
        super().__init__(coordinator)
        self._config_entry = entry
        self._slot_index = slot_index
        self._attr_unique_id = f"{entry.entry_id}-meal-{slot_index + 1}"

        # Get location from config entry (check options first, then data)
        location = entry.options.get(
            CONF_LOCATION, entry.data.get(CONF_LOCATION, "Ingolstadt Mensa")
        )
        device_name = self._format_location_name(location)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            entry_type=DeviceEntryType.SERVICE,
        )

    @staticmethod
    def _format_location_name(location: str) -> str:
        if not location:
            return "Ingolstadt Mensa"

        formatted = re.sub(r"(?<!^)(?<! )([A-Z])", r" \1", location)
        return formatted.strip()

    @staticmethod
    def _get_category_icon(category: str | None) -> str:
        """Return Home Assistant icon based on meal category."""
        if not category:
            return "mdi:food"

        category_lower = category.lower()

        # Map categories to icons
        icon_map = {
            "main": "mdi:silverware-fork-knife",
            "salad": "mdi:bowl-mix",
            "desert": "mdi:cake",
            "dessert": "mdi:cake",  # Handle correct spelling too
            "soup": "mdi:bowl",
        }

        return icon_map.get(category_lower, "mdi:food")

    @staticmethod
    def _strip_restaurant_prefix(name: str | None) -> str | None:
        """Remove the leading restaurant label from a meal name."""
        if not name:
            return name

        normalized = name.strip()
        # Try various prefix formats (case-insensitive)
        prefixes = ("thi mensa", "ingolstadt mensa")
        normalized_lower = normalized.lower()
        for prefix in prefixes:
            if normalized_lower.startswith(prefix):
                # Remove prefix and any following separators (space, colon, dash, etc.)
                remaining = normalized[len(prefix) :].lstrip(" :-")
                # Only use stripped version if it's not empty
                if remaining:
                    normalized = remaining
                break

        return normalized

    @property
    def _selected_price_group(self) -> str:
        return self._config_entry.options.get(
            CONF_PRICE_GROUP, self._config_entry.data[CONF_PRICE_GROUP]
        )

    @property
    def _meal(self) -> dict[str, Any] | None:
        meals = self.coordinator.data.get("meals", []) if self.coordinator.data else []
        if self._slot_index < len(meals):
            return meals[self._slot_index]
        return None

    @property
    def available(self) -> bool:
        """Return whether the meal still exists in the coordinator data."""
        return self._meal is not None

    @property
    def name(self) -> str | None:
        """Return a localized meal name if present."""
        meal = self._meal
        if not meal:
            return f"Meal {self._slot_index + 1}"
        name_data = meal.get("name") or {}
        name = name_data.get("en") or name_data.get("de")
        stripped_name = self._strip_restaurant_prefix(name)
        return stripped_name or f"Meal {self._slot_index + 1}"

    @property
    def icon(self) -> str:
        """Return icon based on meal category."""
        meal = self._meal
        if not meal:
            return "mdi:food"
        category = meal.get("category")
        return self._get_category_icon(category)

    @property
    def native_value(self) -> float | None:
        """Return the selected price group value."""
        meal = self._meal
        if not meal:
            return None
        prices = meal.get("prices") or {}
        return prices.get(self._selected_price_group)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement for the price."""
        return "EUR"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Provide detailed metadata about the meal."""
        meal = self._meal
        if not meal:
            return {}
        name_data = meal.get("name") or {}
        return {
            "name_de": name_data.get("de"),
            "name_en": name_data.get("en"),
            "category": meal.get("category"),
            "restaurant": meal.get("restaurant"),
            "prices": meal.get("prices"),
            "allergens": meal.get("allergens"),
            "flags": meal.get("flags"),
            "meal_id": meal.get("mealId"),
            "date": self.coordinator.data.get("timestamp"),
            "location": self._config_entry.options.get(
                CONF_LOCATION, self._config_entry.data.get(CONF_LOCATION)
            ),
            "price_group": self._selected_price_group,
        }
