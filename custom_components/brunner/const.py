"""Constants for the Brunner Heating integration."""

from __future__ import annotations

DOMAIN = "brunner"

# Config entry keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 5900
DEFAULT_SCAN_INTERVAL = 300  # seconds; pace gently — polling takes over the local display

# Touchdisplay framebuffer (RFB) geometry observed on BWP 13 green
FB_WIDTH = 640
FB_HEIGHT = 480
