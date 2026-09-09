"""«Sist vannet» per plante – redigerbar."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import PlanteEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SistVannet(c, p) for p in c.plants)


class SistVannet(PlanteEntity, DateTimeEntity):
    _attr_icon = "mdi:watering-can-outline"

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "sist_vannet", "sist_vannet")

    @property
    def native_value(self) -> datetime | None:
        s = self.status
        return dt_util.as_utc(s.last) if s and s.last else None

    async def async_set_value(self, value: datetime) -> None:
        await self.coordinator.async_watered(self.plant_id, value)
