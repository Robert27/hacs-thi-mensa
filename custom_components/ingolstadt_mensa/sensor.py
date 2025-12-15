"""Sensor platform for Ingolstadt Mensa meals."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_LOCATION,
    CONF_PRICE_GROUP,
    DOMAIN,
    format_location_name,
    slugify_location_name,
)

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
    tracked: dict[tuple[str, int], MensaMealSensor] = {}

    def _sync_entities_from_data() -> None:
        if not coordinator.data:
            return

        new_entities: list[MensaMealSensor] = []

        # Always create exactly 5 entities for today's meals (fixed slots)
        for slot_index in range(5):
            key = ("today", slot_index)
            if key in tracked:
                continue

            sensor = MensaMealSensor(coordinator, entry, slot_index, "today")
            tracked[key] = sensor
            new_entities.append(sensor)

        # Always create exactly 5 entities for tomorrow's meals (fixed slots)
        for slot_index in range(5):
            key = ("tomorrow", slot_index)
            if key in tracked:
                continue

            sensor = MensaMealSensor(coordinator, entry, slot_index, "tomorrow")
            tracked[key] = sensor
            new_entities.append(sensor)

        if new_entities:
            async_add_entities(new_entities)

    _sync_entities_from_data()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities_from_data))


class MensaMealSensor(CoordinatorEntity, SensorEntity):
    """Represents a single meal as a sensor entity."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: THIMensaDataUpdateCoordinator,
        entry: THIMensaConfigEntry,
        slot_index: int,
        day: str = "today",
    ) -> None:
        """Initialize the sensor with meal metadata."""
        super().__init__(coordinator)
        self._config_entry = entry
        self._slot_index = slot_index
        self._day = day

        location = entry.options.get(
            CONF_LOCATION, entry.data.get(CONF_LOCATION, "IngolstadtMensa")
        )
        self._location_slug = slugify_location_name(location)
        base_device_name = format_location_name(location)
        # Force a static entity_id that only depends on location, day and slot
        self.entity_id = (
            f"sensor.{self._location_slug}_{day}_{slot_index + 1}"
        )

        # Create separate devices for today and tomorrow
        day_label = "Tomorrow" if day == "tomorrow" else "Today"
        device_name = f"{base_device_name} - {day_label}"

        device_identifier = f"{location}-{day}"

        self._fallback_name = f"{base_device_name} {day_label} #{slot_index + 1}"
        self._attr_unique_id = f"{entry.entry_id}-{day}-meal-{slot_index + 1}"
        self._attr_suggested_object_id = (
            f"{self._location_slug}_{day}_{slot_index + 1}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_identifier)},
            name=device_name,
            entry_type=DeviceEntryType.SERVICE,
        )
        self._attr_state_class = SensorStateClass.MEASUREMENT

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
                remaining = normalized[len(prefix) :].lstrip(" :-")
                if remaining:
                    normalized = remaining
                break

        return normalized

    def _get_preferred_language(self) -> str:
        """Get the user's preferred language (de or en)."""
        try:
            language = self.coordinator.hass.config.language
            if language and language.lower().startswith("de"):
                return "de"
        except (AttributeError, TypeError):
            pass
        return "en"

    def _get_meal_name(self, name_data: dict[str, Any]) -> str | None:
        """Get meal name in the user's preferred language with fallback."""
        preferred_lang = self._get_preferred_language()
        fallback_lang = "de" if preferred_lang == "en" else "en"

        # Try preferred language first, then fallback
        name = name_data.get(preferred_lang) or name_data.get(fallback_lang)
        return self._strip_restaurant_prefix(name) if name else None

    @property
    def _selected_price_group(self) -> str:
        return self._config_entry.options.get(
            CONF_PRICE_GROUP, self._config_entry.data[CONF_PRICE_GROUP]
        )

    @property
    def _meal(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None

        day_data = self.coordinator.data.get(self._day, {})
        meals = day_data.get("meals", [])
        if self._slot_index < len(meals):
            return meals[self._slot_index]
        return None

    @property
    def available(self) -> bool:
        """Return whether the meal still exists in the coordinator data."""
        return self._meal is not None

    @property
    def name(self) -> str | None:
        """
        Return the meal name as the friendly name.

        The entity ID stays static through suggested_object_id while the
        friendly name reflects the current meal title.
        """
        meal = self._meal
        if meal:
            meal_name = self._get_meal_name(meal.get("name") or {})
            if meal_name:
                return meal_name
        return self._fallback_name

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
        price = prices.get(self._selected_price_group)
        if price is None:
            return None
        return round(float(price), 2)

    @property
    def suggested_display_precision(self) -> int:
        """Return the suggested display precision (2 decimal places for prices)."""
        return 2

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
        prices = meal.get("prices") or {}

        # Get all price tiers
        price_student = prices.get("student")
        price_employee = prices.get("employee")
        price_guest = prices.get("guest")

        # Get the currently selected price group's price
        selected_price = prices.get(self._selected_price_group)

        attributes = {
            "name_de": name_data.get("de"),
            "name_en": name_data.get("en"),
            "category": meal.get("category"),
            "restaurant": meal.get("restaurant"),
            "allergens": meal.get("allergens"),
            "flags": meal.get("flags"),
            "date": self.coordinator.data.get(self._day, {}).get("timestamp"),
            "price": (
                round(float(selected_price), 2) if selected_price is not None else None
            ),
            "price_student": (
                round(float(price_student), 2) if price_student is not None else None
            ),
            "price_employee": (
                round(float(price_employee), 2) if price_employee is not None else None
            ),
            "price_guest": (
                round(float(price_guest), 2) if price_guest is not None else None
            ),
        }

        return attributes
