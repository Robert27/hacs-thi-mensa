"""Sensor platform for THI Mensa meals."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION, CONF_PRICE_GROUP, DOMAIN

if TYPE_CHECKING:
    from .data import THIMensaConfigEntry
    from .coordinator import THIMensaDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: THIMensaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up meal sensors based on the coordinator data."""

    coordinator: THIMensaDataUpdateCoordinator = entry.runtime_data.coordinator
    tracked: dict[str, MensaMealSensor] = {}

    def _sync_entities_from_data() -> None:
        meals = coordinator.data.get("meals", []) if coordinator.data else []
        new_entities: list[MensaMealSensor] = []
        for meal in meals:
            meal_identifier = meal.get("id") or meal.get("mealId")
            if not meal_identifier or meal_identifier in tracked:
                continue
            sensor = MensaMealSensor(coordinator, entry, meal_identifier)
            tracked[meal_identifier] = sensor
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
        meal_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = entry
        self._meal_id = meal_id
        self._attr_unique_id = f"{entry.entry_id}-{meal_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="THI Mensa",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _selected_price_group(self) -> str:
        return self._config_entry.options.get(
            CONF_PRICE_GROUP, self._config_entry.data[CONF_PRICE_GROUP]
        )

    @property
    def _meal(self) -> dict[str, Any] | None:
        meals = self.coordinator.data.get("meals", []) if self.coordinator.data else []
        for meal in meals:
            if meal.get("id") == self._meal_id or meal.get("mealId") == self._meal_id:
                return meal
        return None

    @property
    def available(self) -> bool:
        return self._meal is not None

    @property
    def name(self) -> str | None:
        meal = self._meal
        if not meal:
            return "THI Mensa meal"
        name_data = meal.get("name") or {}
        return name_data.get("en") or name_data.get("de") or "THI Mensa meal"

    @property
    def native_value(self) -> float | None:
        meal = self._meal
        if not meal:
            return None
        prices = meal.get("prices") or {}
        return prices.get(self._selected_price_group)

    @property
    def native_unit_of_measurement(self) -> str:
        return "EUR"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
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
