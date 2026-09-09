"""Vanningsintervall per plante."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_INTERVAL, DEFAULT_MOISTURE_MIN, DOMAIN, P_INTERVAL, P_INTERVAL_WINTER, P_MOISTURE, P_MOISTURE_MIN
from .entity import PlanteEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    ents = []
    for p in c.plants:
        ents += [PlantNumber(c, p, "intervall", P_INTERVAL, "mdi:weather-sunny", 1, 60, 1, "d", DEFAULT_INTERVAL),
                 PlantNumber(c, p, "intervall_vinter", P_INTERVAL_WINTER, "mdi:snowflake", 0, 90, 1, "d", 0)]
        if p.get(P_MOISTURE):
            ents.append(PlantNumber(c, p, "fuktighet_min", P_MOISTURE_MIN, "mdi:water-percent", 5, 80, 1, "%", DEFAULT_MOISTURE_MIN))
    async_add_entities(ents)


class PlantNumber(PlanteEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.SLIDER

    def __init__(self, c, plant, key, field, icon, min_, max_, step, unit, default) -> None:
        super().__init__(c, plant, key, key)
        self._field, self._default = field, default
        self._attr_icon = icon
        self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = min_, max_, step
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float:
        v = self.plant.get(self._field)
        return float(v if v is not None else self._default)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_update_plant(self.plant_id, **{self._field: int(value)})
