"""Bryter: varsling på/av per sted."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NOTIFY_ON, DOMAIN, P_AUTO_WATERED, P_MOISTURE
from .entity import PlanteEntity, StedEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([Varsling(c)] + [AutoRegistrer(c, p) for p in c.plants if p.get(P_MOISTURE)])


class AutoRegistrer(PlanteEntity, SwitchEntity):
    _attr_icon = "mdi:auto-fix"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "auto_registrer", "auto_registrer")

    @property
    def is_on(self) -> bool:
        return bool(self.plant.get(P_AUTO_WATERED, True))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_update_plant(self.plant_id, **{P_AUTO_WATERED: True})

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_update_plant(self.plant_id, **{P_AUTO_WATERED: False})


class Varsling(StedEntity, SwitchEntity):
    _attr_icon = "mdi:bell"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, c) -> None:
        super().__init__(c, "varsling", "varsling")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.cfg.get(CONF_NOTIFY_ON, True))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_setting(CONF_NOTIFY_ON, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_setting(CONF_NOTIFY_ON, False)
