"""Konstanter for KI Planter."""

DOMAIN = "ki_planter"

CONF_NAME = "name"                 # sted, f.eks. «Sebastians soverom»
CONF_PLANTS = "plants"             # liste av planter (options)
CONF_NOTIFY = "notify_service"     # f.eks. notify.mobile_app_sebastians_iphone
CONF_NOTIFY_TIME = "notify_time"   # "18:00"
CONF_NOTIFY_ON = "notify_enabled"
CONF_NOTIFY_URL = "notify_url"     # åpnes fra varselet, f.eks. /lovelace/soverom#planter
CONF_WINTER_MONTHS = "winter_months"   # måneder som regnes som vinter (1–12)

# Felter per plante
P_ID = "id"
P_NAME = "name"
P_LATIN = "latin"
P_ICON = "icon"
P_INTERVAL = "interval"            # dager (sommer / standard)
P_INTERVAL_WINTER = "interval_winter"   # dager om vinteren (0/tom = samme som sommer)
P_MOISTURE = "moisture_sensor"     # sensor.* med jordfuktighet i %
P_MOISTURE_MIN = "moisture_min"    # under dette = trenger vann (%)
P_AUTO_WATERED = "auto_watered"    # registrer vanning automatisk når fuktigheten hopper opp
P_TIP = "tip"
P_LAST = "last_watered"            # ISO-tidspunkt

DEFAULT_INTERVAL = 7
DEFAULT_MOISTURE_MIN = 30
DEFAULT_WINTER_MONTHS = [11, 12, 1, 2, 3]
MOISTURE_JUMP = 15                 # prosentpoeng opp innen kort tid = vannet
DEFAULT_ICON = "mdi:sprout"

DEFAULTS = {
    CONF_PLANTS: [],
    CONF_NOTIFY: "",
    CONF_NOTIFY_TIME: "18:00",
    CONF_NOTIFY_ON: True,
    CONF_NOTIFY_URL: "",
    CONF_WINTER_MONTHS: DEFAULT_WINTER_MONTHS,
}
