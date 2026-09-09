"""Config flow: ett sted per oppføring, planter legges til/redigeres i options."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_NAME, CONF_NOTIFY, CONF_NOTIFY_ON, CONF_NOTIFY_TIME, CONF_NOTIFY_URL, CONF_PLANTS, CONF_WINTER_MONTHS, DEFAULT_ICON,
    DEFAULT_INTERVAL, DEFAULT_MOISTURE_MIN, DEFAULTS, DOMAIN, P_AUTO_WATERED, P_ICON, P_ID, P_INTERVAL, P_INTERVAL_WINTER, P_LAST,
    P_LATIN, P_MOISTURE, P_MOISTURE_MIN, P_NAME, P_TIP,
)
from .coordinator import PlanterCoordinator

MORE = "legg_til_flere"
PICK = "plante"


def _sv(d: dict, k: str) -> dict:
    return {"suggested_value": d.get(k)}


def sted_schema(d: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_NAME, default=d.get(CONF_NAME, "")): str,
    })


def varsling_schema(d: dict[str, Any]) -> vol.Schema:
    g = lambda k: d.get(k, DEFAULTS[k])  # noqa: E731
    return vol.Schema({
        vol.Optional(CONF_NOTIFY, description=_sv(d, CONF_NOTIFY)): str,
        vol.Required(CONF_NOTIFY_TIME, default=g(CONF_NOTIFY_TIME)): selector.TimeSelector(),
        vol.Required(CONF_NOTIFY_ON, default=g(CONF_NOTIFY_ON)): selector.BooleanSelector(),
        vol.Optional(CONF_NOTIFY_URL, description=_sv(d, CONF_NOTIFY_URL)): str,
        vol.Required(CONF_WINTER_MONTHS, default=[str(m) for m in g(CONF_WINTER_MONTHS)]): selector.SelectSelector(
            selector.SelectSelectorConfig(multiple=True, mode=selector.SelectSelectorMode.LIST, options=[
                selector.SelectOptionDict(value=str(i), label=n) for i, n in enumerate(
                    ["Januar", "Februar", "Mars", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Desember"], 1)])),
    })


def plante_schema(p: dict[str, Any], more: bool = False) -> vol.Schema:
    s = {
        vol.Required(P_NAME, default=p.get(P_NAME, "")): str,
        vol.Optional(P_LATIN, description=_sv(p, P_LATIN)): str,
        vol.Required(P_ICON, default=p.get(P_ICON, DEFAULT_ICON)): selector.IconSelector(),
        vol.Required(P_INTERVAL, default=p.get(P_INTERVAL, DEFAULT_INTERVAL)): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=60, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="d")),
        vol.Optional(P_INTERVAL_WINTER, description=_sv(p, P_INTERVAL_WINTER)): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=90, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="d")),
        vol.Optional(P_MOISTURE, description=_sv(p, P_MOISTURE)): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")),
        vol.Required(P_MOISTURE_MIN, default=p.get(P_MOISTURE_MIN, DEFAULT_MOISTURE_MIN)): selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=80, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="%")),
        vol.Required(P_AUTO_WATERED, default=p.get(P_AUTO_WATERED, True)): selector.BooleanSelector(),
        vol.Optional(P_TIP, description=_sv(p, P_TIP)): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
    }
    if more:
        s[vol.Required(MORE, default=False)] = selector.BooleanSelector()
    return vol.Schema(s)


def _unique_id(plants: list[dict], name: str) -> str:
    base = slugify(name) or "plante"
    pid, n = base, 2
    while any(p.get(P_ID) == pid for p in plants):
        pid = f"{base}_{n}"
        n += 1
    return pid


class KiPlanterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._plants: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(f"{DOMAIN}_{slugify(user_input[CONF_NAME])}")
            self._abort_if_unique_id_configured()
            self._data = user_input
            return await self.async_step_varsling()
        return self.async_show_form(step_id="user", data_schema=sted_schema({}))

    async def async_step_varsling(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input[CONF_WINTER_MONTHS] = [int(m) for m in user_input.get(CONF_WINTER_MONTHS, [])]
            self._data.update(user_input)
            return await self.async_step_plante()
        return self.async_show_form(step_id="varsling", data_schema=varsling_schema({}))

    async def async_step_plante(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            more = user_input.pop(MORE, False)
            p = PlanterCoordinator.normalize({**user_input, P_ID: _unique_id(self._plants, user_input[P_NAME])})
            self._plants.append(p)
            if more:
                return await self.async_step_plante()
            name = self._data.pop(CONF_NAME)
            return self.async_create_entry(title=name, data={CONF_NAME: name}, options={**self._data, CONF_PLANTS: self._plants})
        return self.async_show_form(step_id="plante", data_schema=plante_schema({}, more=True),
                                    description_placeholders={"antall": str(len(self._plants))})

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return KiPlanterOptionsFlow(entry)


class KiPlanterOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._pick: str | None = None

    @property
    def _plants(self) -> list[dict[str, Any]]:
        return [dict(p) for p in (self._entry.options.get(CONF_PLANTS) or [])]

    def _save(self, **changes: Any):
        return self.async_create_entry(title="", data={**self._entry.options, **changes})

    def _pick_schema(self) -> vol.Schema:
        opts = [selector.SelectOptionDict(value=p[P_ID], label=p[P_NAME]) for p in self._plants]
        return vol.Schema({vol.Required(PICK): selector.SelectSelector(
            selector.SelectSelectorConfig(options=opts, mode=selector.SelectSelectorMode.LIST))})

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        opts = ["legg_til", "varsling"]
        if self._plants:
            opts = ["legg_til", "rediger", "fjern", "varsling"]
        return self.async_show_menu(step_id="init", menu_options=opts)

    async def async_step_legg_til(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            plants = self._plants
            plants.append(PlanterCoordinator.normalize({**user_input, P_ID: _unique_id(plants, user_input[P_NAME])}))
            return self._save(**{CONF_PLANTS: plants})
        return self.async_show_form(step_id="legg_til", data_schema=plante_schema({}))

    async def async_step_rediger(self, user_input: dict[str, Any] | None = None):
        if user_input is not None and self._pick is None:
            self._pick = user_input[PICK]
            return await self.async_step_rediger()
        if user_input is not None:
            plants = self._plants
            for i, p in enumerate(plants):
                if p[P_ID] == self._pick:
                    plants[i] = PlanterCoordinator.normalize({**p, **user_input, P_ID: p[P_ID], P_LAST: p.get(P_LAST)})
            return self._save(**{CONF_PLANTS: plants})
        if self._pick is None:
            return self.async_show_form(step_id="rediger", data_schema=self._pick_schema())
        cur = next((p for p in self._plants if p[P_ID] == self._pick), {})
        return self.async_show_form(step_id="rediger_plante", data_schema=plante_schema(cur),
                                    description_placeholders={"navn": cur.get(P_NAME, "")})

    async def async_step_rediger_plante(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_rediger(user_input)

    async def async_step_fjern(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            plants = [p for p in self._plants if p[P_ID] != user_input[PICK]]
            return self._save(**{CONF_PLANTS: plants})
        return self.async_show_form(step_id="fjern", data_schema=self._pick_schema())

    async def async_step_varsling(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self._save(**{CONF_NOTIFY: user_input.get(CONF_NOTIFY, ""), CONF_NOTIFY_TIME: user_input[CONF_NOTIFY_TIME],
                                 CONF_NOTIFY_ON: user_input[CONF_NOTIFY_ON], CONF_NOTIFY_URL: user_input.get(CONF_NOTIFY_URL, ""),
                                 CONF_WINTER_MONTHS: [int(m) for m in user_input.get(CONF_WINTER_MONTHS, [])]})
        return self.async_show_form(step_id="varsling", data_schema=varsling_schema(self._entry.options))
