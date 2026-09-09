"""Entitetsbaser: én enhet per plante, én enhet for stedet."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, P_ICON, P_ID, P_LATIN, P_NAME
from .coordinator import PlanterCoordinator


class StedEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, c: PlanterCoordinator, key: str, translation_key: str) -> None:
        self.coordinator = c
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{c.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, c.entry.entry_id)},
            name=f"{c.name} planter",
            manufacturer="KI",
            model="Planter",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class PlanteEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, c: PlanterCoordinator, plant: dict, key: str, translation_key: str) -> None:
        self.coordinator = c
        self.plant_id: str = plant[P_ID]
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{c.entry.entry_id}_{self.plant_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{c.entry.entry_id}_{self.plant_id}")},
            name=plant[P_NAME],
            manufacturer="KI",
            model=plant.get(P_LATIN) or "Plante",
            via_device=(DOMAIN, c.entry.entry_id),
        )

    @property
    def plant(self) -> dict:
        return self.coordinator.plant(self.plant_id) or {P_ID: self.plant_id, P_NAME: self.plant_id, P_ICON: "mdi:sprout"}

    @property
    def status(self):
        return self.coordinator.status(self.plant_id)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
