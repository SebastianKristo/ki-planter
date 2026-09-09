"""Holder rede på plantene på ett sted og sender varsel."""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change, async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from .const import (
    CONF_NAME, CONF_NOTIFY, CONF_SEASON_MODE, CONF_SUMMER_HOURS, CONF_WINTER_HOURS, CONF_WINTER_MONTHS, DOMAIN,
    P_INTERVAL_SUMMER, SEASON_GROWTH, SEASON_SUMMER, SEASON_WINTER, CONF_NOTIFY_ON, CONF_NOTIFY_TIME, CONF_NOTIFY_URL, CONF_PLANTS, DEFAULT_ICON,
    DEFAULT_INTERVAL, DEFAULT_MOISTURE_MIN, DEFAULTS, MOISTURE_JUMP, P_AUTO_WATERED, P_ICON, P_ID, P_INTERVAL, P_INTERVAL_WINTER,
    P_LAST, P_LATIN, P_MOISTURE, P_MOISTURE_MIN, P_NAME, P_TIP,
)

_LOGGER = logging.getLogger(__name__)


def day_length_hours(latitude: float, when: datetime) -> float:
    """Daglengde i timer (soloppgang→solnedgang, med refraksjon) for en breddegrad og dato."""
    doy = when.timetuple().tm_yday
    decl = math.radians(23.44) * math.sin(math.radians(360.0 / 365.0 * (doy - 81)))
    lat = math.radians(latitude)
    zen = math.radians(90.833)
    cos_h = (math.cos(zen) - math.sin(lat) * math.sin(decl)) / (math.cos(lat) * math.cos(decl))
    if cos_h <= -1:
        return 24.0
    if cos_h >= 1:
        return 0.0
    return 2 * math.degrees(math.acos(cos_h)) / 15.0


class PlantStatus:
    __slots__ = ("interval", "last", "days_since", "days_left", "next", "pct", "due", "text", "season", "moisture", "moisture_min", "reason")

    def __init__(self, plant: dict[str, Any], now: datetime, season: str | bool = SEASON_GROWTH, moisture: float | None = None) -> None:
        if season is True:
            season = SEASON_WINTER
        elif season is False:
            season = SEASON_GROWTH
        self.season = season
        base = plant.get(P_INTERVAL) or DEFAULT_INTERVAL
        if season == SEASON_WINTER:
            iv = plant.get(P_INTERVAL_WINTER) or base
        elif season == SEASON_SUMMER:
            iv = plant.get(P_INTERVAL_SUMMER) or base
        else:
            iv = base
        self.interval = float(iv)
        self.moisture = moisture
        self.moisture_min = float(plant.get(P_MOISTURE_MIN) or DEFAULT_MOISTURE_MIN)
        self.last = dt_util.parse_datetime(plant.get(P_LAST) or "") if plant.get(P_LAST) else None
        if self.last is not None:
            self.last = dt_util.as_local(self.last)
            elapsed = (now - self.last).total_seconds() / 86400
            self.days_since = int(elapsed)
            self.days_left = int(-(-(self.interval - elapsed) // 1))  # ceil
            self.next = self.last + timedelta(days=self.interval)
            self.pct = max(0.0, min(100.0, elapsed / self.interval * 100))
            self.due = self.days_left <= 0
        else:
            self.days_since = self.days_left = None
            self.next = None
            self.pct = 0.0
            self.due = True
        if self.last is None:
            self.text = "Ikke vannet ennå"
        elif self.days_left > 1:
            self.text = f"Om {self.days_left} dager"
        elif self.days_left == 1:
            self.text = "I morgen"
        elif self.days_left == 0:
            self.text = "Vann i dag"
        else:
            n = -self.days_left
            self.text = f"{n} {'dag' if n == 1 else 'dager'} over tiden"
        self.reason = "intervall" if self.due else None
        if self.moisture is not None:
            if self.moisture < self.moisture_min:
                self.due, self.reason = True, "tørr jord"
                self.text = f"Tørr jord ({self.moisture:.0f} %)"
            elif self.due and self.last is not None:
                # jorda er fortsatt fuktig – ikke mas selv om intervallet er passert
                self.due, self.reason = False, None
                self.text = f"Fuktig ({self.moisture:.0f} %)"


class PlanterCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.cfg: dict[str, Any] = {**DEFAULTS, **entry.data, **entry.options}
        self.name: str = self.cfg[CONF_NAME]
        self.prefix = slugify(f"{self.name} planter")
        self.self_update = False
        self.last_notified: datetime | None = None
        self.test_mode: bool = False          # viser alle planter som «trenger vann» i 10 min (for å teste kort/prose)
        self._test_unsub: Callable[[], None] | None = None
        self._listeners: set[Callable[[], None]] = set()
        self._unsubs: list[Callable[[], None]] = []

    # ---------------------------------------------------------------- planter
    @property
    def plants(self) -> list[dict[str, Any]]:
        return [dict(p) for p in (self.cfg.get(CONF_PLANTS) or [])]

    def plant(self, plant_id: str) -> dict[str, Any] | None:
        return next((p for p in self.plants if p.get(P_ID) == plant_id), None)

    def day_length(self, now: datetime | None = None) -> float:
        lat = self.hass.config.latitude if self.hass.config.latitude is not None else 59.9
        return day_length_hours(lat, now or dt_util.now())

    def season(self, now: datetime | None = None) -> str:
        now = now or dt_util.now()
        if self.cfg.get(CONF_SEASON_MODE, "daylength") == "months":
            months = [int(m) for m in (self.cfg.get(CONF_WINTER_MONTHS) or [])]
            return SEASON_WINTER if now.month in months else SEASON_GROWTH
        dl = self.day_length(now)
        if dl < float(self.cfg.get(CONF_WINTER_HOURS, 10)):
            return SEASON_WINTER
        if dl > float(self.cfg.get(CONF_SUMMER_HOURS, 17)):
            return SEASON_SUMMER
        return SEASON_GROWTH

    def is_winter(self, now: datetime | None = None) -> bool:
        return self.season(now) == SEASON_WINTER

    def season_switch_dates(self) -> dict[str, str | None]:
        """Omtrentlige datoer i år der sesongen skifter (bare for daglengde-modus)."""
        if self.cfg.get(CONF_SEASON_MODE, "daylength") == "months":
            return {}
        now = dt_util.now()
        out: dict[str, str | None] = {}
        prev = None
        for d in range(0, 366):
            when = now.replace(month=1, day=1) + timedelta(days=d)
            if when.year != now.year:
                break
            cur = self.season(when)
            if prev is not None and cur != prev:
                out[f"{prev}→{cur}"] = when.strftime("%d.%m")
            prev = cur
        return out

    def moisture(self, plant: dict[str, Any]) -> float | None:
        ent = plant.get(P_MOISTURE)
        if not ent:
            return None
        st = self.hass.states.get(ent)
        if st is None or st.state in ("unknown", "unavailable", ""):
            return None
        try:
            return float(st.state)
        except ValueError:
            return None

    def _status_of(self, p: dict[str, Any], now: datetime) -> PlantStatus:
        return PlantStatus(p, now, self.season(now), self.moisture(p))

    def status(self, plant_id: str) -> PlantStatus | None:
        p = self.plant(plant_id)
        return self._status_of(p, dt_util.now()) if p else None

    def due_count(self) -> int:
        if self.test_mode:
            return len(self.plants)
        now = dt_util.now()
        return sum(1 for p in self.plants if self._status_of(p, now).due)

    def due_names(self) -> list[str]:
        now = dt_util.now()
        return [p.get(P_NAME) or p.get(P_ID) for p in self.plants if self.test_mode or self._status_of(p, now).due]

    async def async_set_test_mode(self, on: bool) -> None:
        """Testvisning: alle planter regnes som «trenger vann» i 10 minutter."""
        if self._test_unsub:
            self._test_unsub()
            self._test_unsub = None
        self.test_mode = on
        if on:
            from homeassistant.helpers.event import async_call_later

            async def _off(_now):
                self._test_unsub = None
                await self.async_set_test_mode(False)

            self._test_unsub = async_call_later(self.hass, 600, _off)
        self._notify()

    @staticmethod
    def normalize(p: dict[str, Any]) -> dict[str, Any]:
        name = (p.get(P_NAME) or "").strip()
        return {
            P_ID: p.get(P_ID) or slugify(name),
            P_NAME: name,
            P_LATIN: (p.get(P_LATIN) or "").strip(),
            P_ICON: p.get(P_ICON) or DEFAULT_ICON,
            P_INTERVAL: int(p.get(P_INTERVAL) or DEFAULT_INTERVAL),
            P_INTERVAL_WINTER: int(p.get(P_INTERVAL_WINTER) or 0),
            P_INTERVAL_SUMMER: int(p.get(P_INTERVAL_SUMMER) or 0),
            P_MOISTURE: p.get(P_MOISTURE) or None,
            P_MOISTURE_MIN: int(p.get(P_MOISTURE_MIN) or DEFAULT_MOISTURE_MIN),
            P_AUTO_WATERED: bool(p.get(P_AUTO_WATERED, True)),
            P_TIP: (p.get(P_TIP) or "").strip(),
            P_LAST: p.get(P_LAST),
        }

    # ---------------------------------------------------------------- oppsett
    async def async_start(self) -> None:
        # Registrer stedets enhet først, så plantene kan peke på den med via_device
        dr.async_get(self.hass).async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=f"{self.name} planter", manufacturer="KI", model="Planter",
        )
        self._unsubs.append(async_track_time_interval(self.hass, self._on_tick, timedelta(minutes=15)))
        self._unsubs.append(async_track_time_change(self.hass, self._on_midnight, hour=0, minute=0, second=5))
        self._unsubs.append(async_track_time_change(self.hass, self._on_notify_time, second=0))
        sensors = [p[P_MOISTURE] for p in self.plants if p.get(P_MOISTURE)]
        if sensors:
            self._unsubs.append(async_track_state_change_event(self.hass, sensors, self._on_moisture))

    async def _on_moisture(self, event) -> None:
        """Fuktigheten hoppet opp → planten ble vannet (hvis auto-registrering er på)."""
        ent = event.data["entity_id"]
        new, old = event.data.get("new_state"), event.data.get("old_state")
        try:
            nv = float(new.state) if new else None
            ov = float(old.state) if old else None
        except (ValueError, AttributeError):
            nv = ov = None
        for p in self.plants:
            if p.get(P_MOISTURE) != ent:
                continue
            if nv is not None and ov is not None and p.get(P_AUTO_WATERED, True) and nv - ov >= MOISTURE_JUMP:
                _LOGGER.info("%s: fuktighet %s → %s, registrerer vanning", p.get(P_NAME), ov, nv)
                await self.async_watered(p[P_ID])
                return
        self._notify()

    @callback
    def async_stop(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        if self._test_unsub:
            self._test_unsub()

    @callback
    def async_add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(cb)
        return lambda: self._listeners.discard(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    async def _on_tick(self, _now: datetime) -> None:
        self._notify()

    async def _on_midnight(self, _now: datetime) -> None:
        self._notify()

    # ---------------------------------------------------------------- lagring
    def _save(self, **changes: Any) -> None:
        self.cfg.update(changes)
        self.self_update = True
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, **changes})
        self._notify()

    async def async_set_setting(self, key: str, value: Any) -> None:
        self._save(**{key: value})

    async def async_update_plant(self, plant_id: str, **fields: Any) -> None:
        plants = self.plants
        for p in plants:
            if p.get(P_ID) == plant_id:
                p.update(fields)
                break
        self._save(**{CONF_PLANTS: plants})

    async def async_watered(self, plant_id: str, when: datetime | None = None) -> None:
        when = when or dt_util.now()
        await self.async_update_plant(plant_id, **{P_LAST: dt_util.as_utc(when).isoformat()})

    async def async_water_all_due(self) -> None:
        now = dt_util.now()
        plants = self.plants
        for p in plants:
            if PlantStatus(p, now).due:
                p[P_LAST] = dt_util.as_utc(now).isoformat()
        self._save(**{CONF_PLANTS: plants})

    # ---------------------------------------------------------------- varsel
    async def _on_notify_time(self, now: datetime) -> None:
        if not self.cfg.get(CONF_NOTIFY_ON) or not self.cfg.get(CONF_NOTIFY):
            return
        now = dt_util.as_local(now)
        hh, mm = (self.cfg.get(CONF_NOTIFY_TIME) or "18:00").split(":")[:2]
        if (now.hour, now.minute) != (int(hh), int(mm)):
            return
        names = self.due_names()
        if not names:
            return
        await self.async_send_notification(names)

    async def async_send_notification(self, names: list[str] | None = None, test: bool = False) -> None:
        names = names if names is not None else self.due_names()
        svc = self.cfg.get(CONF_NOTIFY) or ""
        if "." not in svc:
            _LOGGER.warning("%s: ingen varsel-tjeneste satt opp (Konfigurer → Varsling)", self.name)
            return
        if not names and not test:
            return
        domain, service = svc.split(".", 1)
        if names:
            message = f"{' og '.join(names)} trenger vann." if len(names) < 3 else f"{len(names)} planter trenger vann: {', '.join(names)}."
        else:
            message = "Testvarsel – ingen planter trenger vann akkurat nå."
        if test:
            message = "🧪 " + message
        data: dict[str, Any] = {"title": f"Planter – {self.name}", "message": message}
        url = self.cfg.get(CONF_NOTIFY_URL)
        if url:
            data["data"] = {"url": url}
        try:
            await self.hass.services.async_call(domain, service, data, blocking=False)
            self.last_notified = dt_util.now()
            self._notify()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("%s: varsel feilet (%s): %s", self.name, svc, err)
