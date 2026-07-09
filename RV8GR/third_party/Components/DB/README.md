# Components DB

Component database for the shared Components library.

The current migration-safe structure is grouped by component family:

```text
DB/
  74xx/
    74HC00/
      chip.json
  memory/
    62256/
      chip.json
  virtual/
    InputSource/
      component.json
    Probe/
      component.json
  passive/
    LED/
      component.json
    Resistor/
      component.json
  discrete/
    NPN/
      component.json
```

Each component owns one manifest. IC manifests may reference existing legacy
files while the repo migrates gradually:

- pinout evidence docs
- Verilog model
- Python behavior provider
- DB-owned Verilog export metadata
- tests
- datasheet/source evidence

The manifest shape is defined by `chip.schema.json`. The schema now includes
`group`, `kind`, `role`, and `passive` pin direction so the DB can represent:

- `74xx`: 74xx/74HC logic ICs
- `memory`: SRAM, EEPROM, and flash ICs
- `virtual`: simulation-only inputs, clocks, rails, pulls, and probes
- `passive`: LED, resistor, capacitor
- `discrete`: NPN and PNP transistors

Missing properties are allowed, but they must be visible through manifest
status and loader reports. A grouped IC folder is valid when `chip.json` is
readable and identifies the part. A grouped non-IC folder is valid when
`component.json` is readable and identifies the part.

Implementation files remain active in their legacy locations during migration:

- `Verilog/74xx/`
- `Verilog/Memory/`
- `python/chiplib/`

The DB is the component identity layer. Simulators, exporters, CLI tools, and
future UI/API code should ask the DB what properties a component has instead of
scattering component facts across unrelated files.

The first seed set intentionally covers simple gates, a sequential counter, a
bidirectional bus transceiver, SRAM, and EEPROM:

- `74HC00`
- `74HC04`
- `74HC161`
- `74HC245`
- `62256`
- `AT28C256`

The next useful set adds flip-flop, register, decoder, and flash coverage:

- `74HC74`
- `74HC574`
- `74HC138`
- `SST39SF010A`

The DB now has one manifest for every active legacy Verilog model and pinout
entry: 62 DB IC parts for 62 legacy model parts. It also has grouped seed
manifests for virtual, passive, and discrete schematic components.

All 62 active IC parts with `verilog_export=tested` now own their structural
Verilog export metadata in DB manifests. `Design.to_verilog()` reads those
`verilog.export` blocks through `chiplib.db`; there is no separate runtime
mapping table to keep in sync.

Grouped seed manifests currently cover:

- `InputSource`
- `ClockSource`
- `Probe`
- `BusProbe`
- `VCC`
- `GND`
- `Pullup`
- `Pulldown`
- `LED`
- `Resistor`
- `Capacitor`
- `NPN`
- `PNP`

Audit the DB against the active legacy catalog:

```sh
cd ../python
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
```

Use the learner-facing catalog view for student UI/API work:

```sh
python3 -m chiplib.cli db --student
python3 -m chiplib.cli db --student --group virtual
```

See `STUDENT_CATALOG.md` for the CLI, Python, and frontend API contract.
