"""«Trenger vann» per plante – hovedentiteten kortet leser."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, P_ICON, P_ID, P_INTERVAL, P_LATIN, P_NAME, P_TIP
from .entity import PlanteEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(TrengerVann(c, p) for p in c.plants)


class TrengerVann(PlanteEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, c, plant) -> None:
        super().__init__(c, plant, "trenger_vann", "trenger_vann")

    @property
    def icon(self) -> str:
        return self.plant.get(P_ICON) or "mdi:sprout"

    @property
    def is_on(self) -> bool:
        s = self.status
        return bool(s and s.due)

    @property
    def extra_state_attributes(self) -> dict:
        p, s, c = self.plant, self.status, self.coordinator
        return {
            "integrasjon": DOMAIN,
            "type": "plante",
            "sted": c.name,
            "sted_prefix": c.prefix,
            "plante_id": p.get(P_ID),
            "navn": p.get(P_NAME),
            "latin": p.get(P_LATIN) or None,
            "ikon": p.get(P_ICON),
            "tips": p.get(P_TIP) or None,
            "intervall_dager": p.get(P_INTERVAL),
            "sist_vannet": s.last.isoformat() if s and s.last else None,
            "dager_siden": s.days_since if s else None,
            "dager_igjen": s.days_left if s else None,
            "neste_vanning": s.next.isoformat() if s and s.next else None,
            "prosent": round(s.pct, 1) if s else 0,
            "status": s.text if s else None,
        }
