"""Knapper: «vannet nå» per plante, «alle vannet» og «send varsel» per sted."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import PlanteEntity, StedEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    ents = [AlleVannet(c), SendVarsel(c)] + [VannetNa(c, p) for p in c.plants]
    async_add_entities(ents)


class VannetNa(PlanteEntity, ButtonEntity):
    _attr_icon = "mdi:watering-can"

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "vannet_na", "vannet_naa")

    async def async_press(self) -> None:
        await self.coordinator.async_watered(self.plant_id)


class AlleVannet(StedEntity, ButtonEntity):
    _attr_icon = "mdi:watering-can"

    def __init__(self, c) -> None:
        super().__init__(c, "alle_vannet", "alle_vannet")

    async def async_press(self) -> None:
        await self.coordinator.async_water_all_due()


class SendVarsel(StedEntity, ButtonEntity):
    _attr_icon = "mdi:bell-ring"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "send_varsel", "send_varsel")

    async def async_press(self) -> None:
        await self.coordinator.async_send_notification(test=True)
