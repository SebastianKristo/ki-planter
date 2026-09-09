"""Vanningsintervall per plante."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_INTERVAL, DOMAIN, P_INTERVAL
from .entity import PlanteEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(Intervall(c, p) for p in c.plants)


class Intervall(PlanteEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:calendar-refresh"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "d"

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "intervall", "intervall")

    @property
    def native_value(self) -> float:
        return float(self.plant.get(P_INTERVAL) or DEFAULT_INTERVAL)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_update_plant(self.plant_id, **{P_INTERVAL: int(value)})
