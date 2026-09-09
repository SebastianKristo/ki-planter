"""Bryter: varsling på/av per sted."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NOTIFY_ON, DOMAIN, P_AUTO_WATERED, P_MOISTURE
from .entity import PlanteEntity, StedEntity
from .notify_targets import pretty_service


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([Varsling(c), TestVisning(c)] + [VarselEnhet(c, svc) for svc in c.notify_services]
                       + [AutoRegistrer(c, p) for p in c.plants if p.get(P_MOISTURE)])


class VarselEnhet(StedEntity, SwitchEntity):
    """Én bryter per valgt enhet: av = enheten får ikke varsel."""
    _attr_icon = "mdi:cellphone-message"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, c, service: str) -> None:
        key = "varsel_" + service.split(".", 1)[1]
        super().__init__(c, key, "varsel_enhet")
        self._service = service
        self._attr_translation_placeholders = {"enhet": pretty_service(service)}

    @property
    def is_on(self) -> bool:
        return not self.coordinator.is_muted(self._service)

    @property
    def extra_state_attributes(self) -> dict:
        return {"tjeneste": self._service}

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_muted(self._service, False)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_muted(self._service, True)


class TestVisning(StedEntity, SwitchEntity):
    """På = alle planter vises som «trenger vann» i 10 minutter (for å teste kort og prose-tekst)."""
    _attr_icon = "mdi:test-tube"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "testvisning", "testvisning")

    @property
    def is_on(self) -> bool:
        return self.coordinator.test_mode

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_test_mode(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_test_mode(False)


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
