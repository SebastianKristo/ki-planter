"""Konstanter for KI Planter."""

DOMAIN = "ki_planter"

CONF_NAME = "name"                 # sted, f.eks. «Sebastians soverom»
CONF_PLANTS = "plants"             # liste av planter (options)
CONF_NOTIFY = "notify_service"     # f.eks. notify.mobile_app_sebastians_iphone
CONF_NOTIFY_TIME = "notify_time"   # "18:00"
CONF_NOTIFY_ON = "notify_enabled"
CONF_NOTIFY_URL = "notify_url"     # åpnes fra varselet, f.eks. /lovelace/soverom#planter

# Felter per plante
P_ID = "id"
P_NAME = "name"
P_LATIN = "latin"
P_ICON = "icon"
P_INTERVAL = "interval"            # dager
P_TIP = "tip"
P_LAST = "last_watered"            # ISO-tidspunkt

DEFAULT_INTERVAL = 7
DEFAULT_ICON = "mdi:sprout"

DEFAULTS = {
    CONF_PLANTS: [],
    CONF_NOTIFY: "",
    CONF_NOTIFY_TIME: "18:00",
    CONF_NOTIFY_ON: True,
    CONF_NOTIFY_URL: "",
}
