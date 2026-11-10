# Brunner Heating for Home Assistant

Local Home Assistant integration for **BRUNNER** heating systems (BWP heat pump,
EOS wood stove, BHZ central unit, Solar‑PV) that have a Touchdisplay 2.0/3.0 —
**without** the paid BRUNNER Energiemanager / Smart Home (BSH) Modbus board.

> Status: **working, pre-release.** Verified end-to-end inside a real Home
> Assistant core (via `pytest-homeassistant-custom-component`) against a live
> BWP 13 green: the config entry sets up and all 24 entities populate with real
> values — 20 numeric (heat-pump flow/return/COP/power/pressures, buffer temps,
> heating-circuit flow/return/rate, solar & fireplace power, hot-water setpoint),
> 3 text enums (status/mode/defrost) and a derived "running" binary. Navigation
> is landmark-checked (a dropped tap is caught and retried). Still to do before a
> tagged release: more enum states, the variable-layout EOS stove screen, and
> occasional last-decimal misreads on the smallest fonts.

## Testing

- Offline OCR regression (no hardware, CI): `pytest tests/test_ocr_offline.py`
  reads known values from `docs/screens/` to guard the digit templates.
- Live end-to-end (needs the display): sets up the integration in a real HA
  core and asserts entities populate:
  `BRUNNER_TEST_HOST=<display-ip> pytest tests/test_live_setup.py -o asyncio_mode=auto`
  (install `pytest-homeassistant-custom-component`).

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

## OCR approach

Values are a fixed GUI font at fixed positions, so OCR is a bundled **digit
template matcher** ([`ocr.py`](custom_components/brunner/ocr.py)) needing only
Pillow and numpy (declared in the manifest; both sit within Home Assistant's own
version constraints) — so no Tesseract binary at runtime. A region is cropped,
thresholded (polarity per region,
since buffer temps are white-on-colour), segmented into glyphs, and each glyph
height-normalised and matched against bundled templates
([`glyphs.npz`](custom_components/brunner/glyphs.npz)); the first whitespace-
delimited number token is kept, so units never need OCR. Templates are built by
[`scripts/train_glyphs.py`](scripts/train_glyphs.py), which uses Tesseract *only
at training time* to label glyphs harvested from captures.

Validate or re-measure against your own display with
[`scripts/poll_once.py`](scripts/poll_once.py) (`python scripts/poll_once.py
<host> --dump`).

## Requirements

- The display must be reachable over the network with VNC enabled (default on
  the systems tested).
- Runtime: Pillow + numpy (declared in the manifest; Home Assistant installs
  them within its own version constraints). Tesseract is a
  dev-only dependency for retraining templates.

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
