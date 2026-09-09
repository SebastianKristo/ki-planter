"""Sensorer: dager siden / neste vanning per plante, antall som trenger vann per sted."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SEASON_MODE, CONF_SUMMER_HOURS, CONF_WINTER_HOURS, CONF_WINTER_MONTHS, DOMAIN, P_MOISTURE, P_NAME
from .entity import PlanteEntity, StedEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    ents = [TrengerVannAntall(c)]
    for p in c.plants:
        ents += [DagerSiden(c, p), NesteVanning(c, p)]
    async_add_entities(ents)


class TrengerVannAntall(StedEntity, SensorEntity):
    _attr_icon = "mdi:flower-outline"
    _attr_native_unit_of_measurement = "stk"

    def __init__(self, c) -> None:
        super().__init__(c, "trenger_vann", "trenger_vann_antall")

    @property
    def native_value(self) -> int:
        return self.coordinator.due_count()

    @property
    def extra_state_attributes(self) -> dict:
        c = self.coordinator
        return {
            "integrasjon": DOMAIN,
            "type": "sted",
            "sted": c.name,
            "prefix": c.prefix,
            "planter": [p.get(P_NAME) for p in c.plants],
            "trenger_vann": c.due_names(),
            "trenger_vann_tekst": " og ".join(c.due_names()),
            "testvisning": c.test_mode,
            "sist_varslet": c.last_notified.isoformat() if c.last_notified else None,
            "sesong": c.season(),
            "sesongmodus": c.cfg.get(CONF_SEASON_MODE, "daylength"),
            "daglengde_timer": round(c.day_length(), 1),
            "vinter_under_timer": c.cfg.get(CONF_WINTER_HOURS),
            "hoysommer_over_timer": c.cfg.get(CONF_SUMMER_HOURS),
            "sesongskifter": c.season_switch_dates(),
            "vintermaaneder": c.cfg.get(CONF_WINTER_MONTHS),
        }


class DagerSiden(PlanteEntity, SensorEntity):
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "d"

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "dager_siden", "dager_siden_vannet")

    @property
    def native_value(self) -> int | None:
        s = self.status
        return s.days_since if s else None


class NesteVanning(PlanteEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:watering-can"

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "neste", "neste_vanning")

    @property
    def native_value(self) -> datetime | None:
        s = self.status
        return s.next if s else None
