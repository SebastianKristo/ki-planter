"""Bryter: varsling på/av per sted."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NOTIFY_ON, DOMAIN
from .entity import StedEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([Varsling(hass.data[DOMAIN][entry.entry_id])])


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
