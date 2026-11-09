# Brunner Heating for Home Assistant

Local Home Assistant integration for **BRUNNER** heating systems (BWP heat pump,
EOS wood stove, BHZ central unit, Solar‑PV) that have a Touchdisplay 2.0/3.0 —
**without** the paid BRUNNER Energiemanager / Smart Home (BSH) Modbus board.

> Status: **early scaffold.** The access method is proven and every sensor screen
> is mapped (see [`docs/sensor-map.md`](docs/sensor-map.md)); the OCR polling
> logic is the next milestone. Not yet functional as an installed integration.

## How it works

The BRUNNER touchdisplay runs an unauthenticated **VNC (RFB 3.8)** server on the
local network (observed on a BWP 13 green: `x11vnc`, 640×480, security type
"None"). BRUNNER's own cloud (`mybrunner.de`) and app are just Apache Guacamole
screen‑sharing on top of this same VNC — there is no data API behind them, and
no Modbus unless you buy the Energiemanager board.

Since VNC exposes only pixels, this integration:

1. connects to the display over VNC (pure‑Python client, no extra wheels — see
   [`custom_components/brunner/vnc.py`](custom_components/brunner/vnc.py)),
2. navigates to each screen by sending taps,
3. captures the framebuffer and OCRs fixed regions into values,
4. publishes them as Home Assistant sensors.

Each poll briefly takes over the local display (as a cloud session does), so the
default poll interval is deliberately slow (5 min).

## Requirements & open design questions

- The display must be reachable over the network with VNC enabled (default on
  the systems tested).
- **OCR engine is not yet chosen.** Values are a normal font at fixed positions,
  so options include Tesseract (needs a system binary — awkward inside HA), a
  bundled lightweight digit classifier, or template matching. Tracked for the
  poller build.

## Security note

The touchdisplay's VNC is **open and password‑free** — anyone on your LAN or
guest Wi‑Fi can view *and operate* your heating. Consider firewalling the port
to trusted hosts. Note BRUNNER's own remote access may rely on it, so test
before locking it down.

## Installation (HACS, once released)

1. HACS → Integrations → ⋮ → Custom repositories → add this repo as type
   *Integration*.
2. Install **Brunner Heating**, restart Home Assistant.
3. Settings → Devices & Services → Add Integration → **Brunner Heating**, enter
   the touchdisplay IP.

## Repository layout

```
custom_components/brunner/   # the integration
  vnc.py                     # dependency-free RFB client (capture + tap)
  coordinator.py             # poll loop (OCR regions: TODO)
  sensor.py                  # entity definitions (mirror docs/sensor-map.md)
  config_flow.py             # UI setup (host/port/interval)
docs/sensor-map.md           # every mapped screen + values + HA entity names
docs/screens/                # reference screenshots
scripts/                     # standalone VNC capture/probe tools used to map
```

## Disclaimer

Unofficial, not affiliated with Ulrich Brunner GmbH. Read‑only by design; use at
your own risk. "BRUNNER", "myBRUNNER", "BWP", "EOS", "BHZ" are trademarks of
their owner.
