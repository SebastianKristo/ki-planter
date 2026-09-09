"""Finner notify-tjenester (mobiler, grupper, …) og gir dem lesbare navn."""
from __future__ import annotations

import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

SKIP = {"send_message", "persistent_notification", "notify"}


def pretty_service(service: str) -> str:
    name = service.split(".", 1)[-1]
    if name.startswith("mobile_app_"):
        name = name[len("mobile_app_"):]
    name = re.sub(r"[_\-]+", " ", name).strip()
    name = re.sub(r"\b(iphone|ipad)\b", lambda m: {"iphone": "iPhone", "ipad": "iPad"}[m.group(1)], name, flags=re.I)
    return name[:1].upper() + name[1:] if name else service


def notify_targets(hass: HomeAssistant) -> list[tuple[str, str]]:
    """[(service_id, label)] for alle notify-tjenester. Mobiler først, med enhetsmodell fra mobile_app."""
    services = hass.services.async_services().get("notify", {})
    devices = {}
    for dev in dr.async_get(hass).devices.values():
        if any(ident[0] == "mobile_app" for ident in dev.identifiers):
            key = re.sub(r"[^a-z0-9]+", "_", (dev.name_by_user or dev.name or "").lower()).strip("_")
            devices[key] = f"{dev.name_by_user or dev.name} ({dev.model})" if dev.model else (dev.name_by_user or dev.name)
    out = []
    for name in services:
        if name in SKIP:
            continue
        sid = f"notify.{name}"
        if name.startswith("mobile_app_"):
            key = name[len("mobile_app_"):]
            label = "📱 " + (devices.get(key) or pretty_service(sid))
            out.append((0, sid, label))
        else:
            out.append((1, sid, "🔔 " + pretty_service(sid)))
    out.sort(key=lambda t: (t[0], t[2].lower()))
    return [(sid, label) for _, sid, label in out]
