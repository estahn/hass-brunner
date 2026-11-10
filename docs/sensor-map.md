# Brunner BWP 13 green — sensor map (via touchdisplay VNC)

Access: `192.168.178.124:5900`, x11vnc, no password, framebuffer **640×480**.
Captured 2026‑11‑09 ~17:26. Heat pump was in standby, wood fireplace (EOS) running, outdoor 3 °C.

Navigation is by on‑screen taps over VNC:
- Bottom tabs switch subsystem: **EOS** (wood stove) · **Heizung** (central unit / BHZ) · **BWP** (heat pump).
- Top bar switches screen within a subsystem: Home · Sensors · Menu · Archive · **Status (0123)** · Settings · Info. The icon set changes per tab.
- `◄ ►` bottom arrows had no effect here (single page each).

Each value below is a fixed text box on a fixed screen → good OCR targets. Value column is right‑aligned; left panel values sit around x≈120–345, right panel around x≈380–610. Row pitch ≈ 28 px starting y≈122.

---

## BWP tab → Home  (`brunner-bwp.png`)
| Value | Reading | Unit | Notes |
|---|---|---|---|
| Outdoor temp | 3 | °C | top‑left thermometer |
| Mode (left btn) | Standby/Pause | — | operating request |
| Mode (right btn) | Off | — | on/off state |
| Fan | 0 | % | |
| Compressor | 0 | rev/s | |
| Flow (supply) | 24 | °C | arrow out, top‑right |
| Return | 20 | °C | arrow in, bottom‑right |

## BWP tab → Sensors  (`bwp-sensors.png`)
| Value | Reading | Unit |
|---|---|---|
| COP | 0.0 | — |
| Flow (volumetric) | 0.0 | l/min |
| Flow (supply temp) | 22 | °C |
| Return | 19 | °C |
| Air intake | 0 | °C |
| Heating power | 0.0 | kW |
| High pressure | 6 | bar |
| Low pressure | 3 | bar |
| Status | 1 STAND BY | enum |
| COP graph | — | — | last 2 h, right panel |

## BWP tab → Status (0123)  (`bwp-status.png`)
| Field | Reading | Notes |
|---|---|---|
| Brunner HP | HP OT | model/variant code |
| IP | (shown `x.y.0.0`) | masked placeholder on screen |
| Motor‑type | PB52FA1MT 400 | compressor model |
| Defrost | Off | enum |
| Env.-zone | 6 Low comp.ratio | operating envelope zone |
| Status HP | 1 STAND BY | numeric+text enum |
| Error | (none) | fault code field |
| HP Mode | Heating | Heating / Cooling / ... |
| HP loading | Aus (off) | load request |

---

## Heizung tab → Home = system overview (BHZ 3.0)  (`system-overview.png`)
Richest single screen — the whole hydraulic picture.
| Value | Reading | Unit |
|---|---|---|
| Solar‑PV power | 0.0 | kW |
| Fireplace power | 4.5 | kW |
| BWP 13 state | Off | enum |
| Outdoor temp | 3 | °C |
| Buffer top | 55 | °C |
| Buffer middle | 35 | °C |
| Buffer bottom | 34 | °C |
| Buffer pressure | 1.5 | bar |
| Buffer volume | 1000 | l (static label) |
| Heating circuit (HK "Family") | 2.1 | kW |
| Hot water state | Ready | enum |

## Heizung tab → Solar‑PV screen  (`solar-pv.png`)
| Field | Reading | Notes |
|---|---|---|
| Activation | Supply | mode |
| El.heater power | 0.0 kW | immersion heater |
| PV use | El.heater/HP | surplus routing |
| Program | Day | schedule |
| El.heater power graph | — | per clock time |
*(left down‑arrow scrolls to more rows — not yet captured)*

## Heizung tab → Heating → Heat.circuit 1  (`heating-circuit-1a.png`, `heating-circuit-1b.png`)
Page 1 (settings):
| Field | Reading |
|---|---|
| HK | On |
| Program | Family |
| Heating power | 1.8 kW |
| Warmer/Colder (offset) | +1 °C |
| Setback | Cooldown prot. |
| Absence | 0 days |
| Summer from | 17 °C |
| Permanent | 0 hrs |

Page 2 (live sensors — the useful ones):
| Value | Reading | Unit |
|---|---|---|
| Circuit type | Radiators | — |
| HC1 pump | On | enum |
| HK1 flow setpoint | 43 | °C |
| HK1 flow actual | 35.1 | °C |
| HK1 return actual | 34.2 | °C |
| HK1 flow rate actual | 25.6 | l/min |

## Heizung tab → Water (hot water / DHW)  (`hotwater-a.png`, `hotwater-b.png`)
| Field | Reading |
|---|---|
| Water pump | Off |
| Heating power | 0.0 kW |
| HW set temp | 50 °C |
| Water program | early riser |
| DHW source | BWP 13 @ 50 °C set |
| HW loading S4 | Ja, S3 |
| Additional heat | 0 °C |
| DHW priority (WW‑Vorrang) | OFF |
*(No separate "actual DHW temp" box on these pages; overview shows DHW state = Ready.)*

## BWP/EOS tab → Archive (0123 neighbour)  (`archive.png` in scratchpad)
Graphical only: pick a series (COP, Flow, Return, Air intake, Heating power, Low pressure)
and see a rolling **~2 h** chart. No tables, no export → not an OCR/backfill target.

---

## EOS tab → Home (wood stove)  (`brunner-eos.png`)
| Value | Reading | Unit |
|---|---|---|
| Combustion chamber | 246 | °C |
| Power | 4.9 | kW |
| Boiler | 65 | °C |
| Buffer top | 55 | °C |
| Buffer middle | 35 | °C |
| Buffer bottom | 34 | °C |
| Weather (outdoor) | 3 | °C |
| Yield today | 31.0 | kWh |
| Eco function | Yes | enum |
| State | Stage 1 Light‑up | enum |

---

## Candidate Home Assistant entities
Core heat‑pump set (poll BWP Home + Sensors + Status):
`sensor.bwp_outdoor_temp`, `sensor.bwp_flow_temp`, `sensor.bwp_return_temp`,
`sensor.bwp_flow_rate` (l/min), `sensor.bwp_air_intake_temp`, `sensor.bwp_fan` (%),
`sensor.bwp_compressor_speed` (rev/s), `sensor.bwp_heating_power` (kW), `sensor.bwp_cop`,
`sensor.bwp_pressure_high` / `_low` (bar), `sensor.bwp_status`, `sensor.bwp_mode`,
`binary_sensor.bwp_defrost`, `sensor.bwp_error`.

System set (poll Heizung overview): buffer top/mid/bottom °C, buffer bar,
solar‑pv kW, fireplace kW, heating‑circuit kW, hot‑water state.

Heating circuit (poll HC1 page 2): `sensor.hk1_flow_set`, `sensor.hk1_flow_actual`,
`sensor.hk1_return_actual`, `sensor.hk1_flow_rate`, `binary_sensor.hk1_pump`,
`sensor.hk1_heating_power`.

Hot water (poll Water): `sensor.dhw_set_temp`, `binary_sensor.dhw_pump`,
`sensor.dhw_heating_power`, `binary_sensor.dhw_priority`.

## Mapping status
All sensor‑bearing screens now captured: BWP Home/Sensors/Status, system overview,
Solar‑PV, Heating circuit 1 (2 pages), Hot water (2 pages), EOS stove.
Archive is rolling 2 h graphs only — no history backfill.

## Poller build — done
- Exact pixel boxes + polarity per value live in `custom_components/brunner/regions.py`.
- Navigation macros (tap sequences, one tap per VNC connection) in `reader.py`.
- OCR via bundled digit templates (`ocr.py` + `glyphs.npz`), verified live.
- Default poll cadence 5 min (`const.py`) to minimise local‑display takeover.

## Text enums — done (seeded states only)
- `bwp_status`, `bwp_mode`, `bwp_defrost` read via whole-region template match
  (`enums.py` + `enum_templates.npz`, seeded by `scripts/train_enums.py`).
- Only seeded states are recognised (currently: status=standby, mode=heating,
  defrost=off); other states read as None until captured and added. The leading
  state code in "1 STAND BY" is part of the matched region.
- `bwp_running` (binary) is derived from flow rate / heating power — more
  reliable than the tiny fan/compressor pills.

## Still open
- Fan % and compressor rev/s: rendered in a ~6px pill font, too small to OCR
  reliably (a "0" misreads as "1"); use `bwp_running` instead. Revisit if a
  larger readout exists.
- More enum states: capture status/mode/defrost in running/cooling/defrost
  states and add them to `scripts/train_enums.py` (Env.-zone is highly dynamic).
- EOS stove screen has a variable layout; not yet in the region table.
