# RV8-GR Gate-Level Simulator — Design Document

## Purpose

Pin-accurate simulation of all 35 chips. Verify wiring from 03_wiring_guide.md.
Probe any pin like attaching an LED. Step one clock at a time.

---

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────┐
│  Chip Class │────▶│  Wire    │────▶│ Simulator│
│  (per type) │     │  Net     │     │  Engine  │
└─────────────┘     └──────────┘     └──────────┘
```

---

## Chip Base Class

```python
class Chip:
    """Base class for all 74HC chips."""
    def __init__(self, name: str, pin_count: int):
        self.name = name                    # e.g. "U5"
        self.pins = [None] * (pin_count+1)  # pins[1..N], index 0 unused
        self.pin_names = {}                 # {pin_num: "name"}

    def set_pin(self, pin: int, value: int):
        """Set input pin value (0 or 1 for single bit, 0-255 for bus)."""

    def get_pin(self, pin: int) -> int:
        """Read output pin value."""

    def update(self):
        """Recalculate outputs from inputs (combinational)."""

    def clock_edge(self):
        """Handle rising edge (for sequential chips)."""
```

---

## Chip Types

### Sequential (edge-triggered)

| Class | Chip | Instances | Key Behavior |
|-------|------|-----------|-------------|
| HC574 | 74HC574 | U5,U6,U9,U23,U32 | 8-bit D latch, rising edge CLK, /OE |
| HC161 | 74HC161 | U1,U2,U3,U4 | 4-bit counter, sync load, enable |
| HC164 | 74HC164 | U8 | 8-bit shift register, serial in |
| HC74 | 74HC74 | U21,U31 | Dual D flip-flop, /PR, /CLR |

### Combinational (instant propagation)

| Class | Chip | Instances | Key Behavior |
|-------|------|-----------|-------------|
| HC245 | 74HC245 | U7 | 8-bit bidirectional buffer, DIR, /OE |
| HC541 | 74HC541 | U14 | 8-bit buffer, /OE1, /OE2 |
| HC283 | 74HC283 | U10,U11 | 4-bit full adder, Cin, Cout |
| HC86 | 74HC86 | U12,U13,U28 | Quad 2-input XOR |
| HC157 | 74HC157 | U15-U20,U29,U30 | Quad 2-to-1 mux, SEL, /E |
| HC688 | 74HC688 | U22 | 8-bit comparator, /OE, /P=Q |
| HC04 | 74HC04 | U24 | Hex inverter |
| HC32 | 74HC32 | U25 | Quad 2-input OR |
| HC00 | 74HC00 | U26,U27 | Quad 2-input NAND |
| HC21 | 74HC21 | U33 | Dual 4-input AND |

### Memory

| Class | Chip | Instances | Key Behavior |
|-------|------|-----------|-------------|
| ROM | AT28C256 | ROM | 32KB read, /CE, /OE |
| RAM | 62256 | RAM | 32KB read/write, /CE, /OE, /WE |

---

## Bus Architecture (matches 03_wiring_guide)

### Internal Buses

```
DBUS[7:0]  — External data bus (ROM, RAM, U7 A-side)
IBUS[7:0]  — Internal data bus (U7 B-side, U6*, U14*, U12/U13, U5, U23, U32)
ABUS[15:0] — Address bus (U15/U16/U29/U30 outputs → ROM, RAM)
```

### Tristate Bus Resolution

IBUS has 3 possible drivers (only one active at a time):

```python
class TristateBus:
    """Bus with multiple tristate drivers."""
    def __init__(self, name: str, width: int):
        self.name = name
        self.width = width
        self.drivers = {}   # {name: (value, enabled)}

    def drive(self, name: str, value: int, enabled: bool):
        """A chip asserts/releases the bus."""
        self.drivers[name] = (value, enabled)

    def read(self) -> int:
        """Resolve bus value. Error if multiple drivers."""
        active = [(n,v) for n,(v,e) in self.drivers.items() if e]
        if len(active) == 0:
            return 0xFF  # floating (pulled high)
        if len(active) == 1:
            return active[0][1]
        # BUS CONFLICT!
        raise BusConflictError(f"{self.name}: multiple drivers {[n for n,v in active]}")
```

### Bus Instances

```python
# From 03_wiring_guide.md:
dbus = TristateBus('DBUS', 8)   # D0-D7: ROM out, RAM bidir, U7 A-side
ibus = TristateBus('IBUS', 8)   # IB0-IB7: U7 B, U6 Q*, U14 Y*
abus = Bus('ABUS', 16)          # A0-A15: driven by mux only (no tristate)
```

### IBUS Drivers (from 03_wiring_guide)

```python
# U7 (74HC245 B-side): drives IBUS when BUF_OE_SAFE=0
ibus.drive('U7', dbus_value, enabled=(buf_oe_safe == 0))

# U6 (74HC574 Q outputs): drives IBUS when /IRL_OE=0
ibus.drive('U6', irl_value, enabled=(irl_oe_n == 0))

# U14 (74HC541 Y outputs): drives IBUS when /AC_BUF=0
ibus.drive('U14', ac_value, enabled=(ac_buf_n == 0))
```

### DBUS Drivers

```python
# ROM: drives DBUS when ROM /CE=0 AND /OE=0
dbus.drive('ROM', rom_data, enabled=(rom_ce_n == 0))

# RAM: drives DBUS when RAM /CE=0 AND /OE=0 AND /WE=1 (read mode)
dbus.drive('RAM', ram_data, enabled=(ram_ce_n == 0 and ram_we_n == 1))

# U7 (74HC245 A-side): drives DBUS when DIR=1 AND /OE=0 (write mode)
dbus.drive('U7', ibus_value, enabled=(wr_dir == 1 and buf_oe_safe == 0))
```

### ABUS (no tristate — always driven by mux)

```python
# U15-U16: A[7:0] from mux (PC low or IRL)
# U29-U30: A[15:8] from mux (PC high or Data Page)
abus.value = (addr_hi << 8) | addr_lo
```

---

## Wire Net

```python
class Net:
    """A named wire connecting chip pins."""
    def __init__(self, name: str):
        self.name = name
        self.value = 0          # current logic level
        self.driver = None      # (chip, pin) that drives this net
        self.listeners = []     # [(chip, pin), ...] that read this net
```

---

## Simulator Engine

```python
class Simulator:
    def __init__(self):
        self.chips = {}         # {"U5": Chip, "U6": Chip, ...}
        self.nets = {}          # {"T0": Net, "IBUS0": Net, ...}
        self.clock = 0

    def wire(self, net_name: str, driver: tuple, listeners: list):
        """Connect driver (chip,pin) to listeners [(chip,pin), ...]"""

    def step(self):
        """One clock cycle: propagate combinational, then clock edge."""

    def probe(self, chip_name: str, pin: int) -> int:
        """Read a pin value (like LED)."""

    def probe_bus(self, net_prefix: str, width: int) -> int:
        """Read multi-bit bus (e.g. 'IBUS', 8)."""

    def inject(self, chip_name: str, pin: int, value: int):
        """Force a pin value (like DIP switch)."""
```

---

## Simulation Loop

```python
def step(self):
    # 1. Drive clock HIGH
    self.nets['CLK'].value = 1

    # 2. Sequential chips latch on rising edge
    for chip in self.sequential_chips:
        chip.clock_edge()

    # 3. Propagate combinational (iterate until stable)
    for _ in range(10):  # max iterations
        changed = False
        for chip in self.combinational_chips:
            old = chip.outputs()
            chip.update()
            if chip.outputs() != old:
                changed = True
        if not changed:
            break

    # 4. Update all nets from chip outputs
    self.propagate_nets()
    self.clock += 1
```

---

## Wiring (from 03_wiring_guide.md)

Wiring defined as connection list:

```python
def wire_cpu(sim):
    # CLK → U1-2, U2-2, U3-2, U4-2, U8-8
    sim.wire('CLK', source=('OSC', 1), sinks=[
        ('U1', 2), ('U2', 2), ('U3', 2), ('U4', 2), ('U8', 8)
    ])

    # T0 (U8-3) → U5-11, U25-4, U24-1
    sim.wire('T0', source=('U8', 3), sinks=[
        ('U5', 11), ('U25', 4), ('U24', 1)
    ])

    # IB0: U7-18, U6-19*, U14-18*, U12-1, U23-2, U5-2, U32-2
    sim.wire('IB0', source=None, sinks=[  # tristate - multiple potential drivers
        ('U7', 18), ('U6', 19), ('U14', 18),
        ('U12', 1), ('U23', 2), ('U5', 2), ('U32', 2)
    ])
    # ... (all connections from 03_wiring_guide.md)
```

---

## Probe Interface

```python
# Probe like LED
sim.probe('U9', 19)          # AC bit 0
sim.probe_bus('AC', 8)       # Full AC value

# Probe bus
sim.probe_bus('ABUS', 16)    # Address bus
sim.probe_bus('DBUS', 8)     # Data bus
sim.probe_bus('IBUS', 8)     # Internal bus

# Inject like DIP switch
sim.inject('ROM', 'data', 0x30)  # Force ROM output
```

---

## Test Strategy

```python
# Step 1: Power on, check reset state
sim.reset()
assert sim.probe_bus('PC', 16) == 0x8000
assert sim.probe('U8', 3) == 1  # T0

# Step 2: Single step, check ROM fetch
sim.step()
assert sim.probe_bus('ABUS', 16) == 0x8000
assert sim.probe_bus('DBUS', 8) == rom_data[0]

# Step 3: Verify each instruction type
```

---

## File Structure

```
sim/
├── soft_debug.py           # Current high-level sim (keep)
├── chip_sim.py             # NEW: Gate-level chip simulator
├── chips/
│   ├── __init__.py
│   ├── base.py             # Chip base class + Net
│   ├── sequential.py       # HC574, HC161, HC164, HC74
│   ├── combinational.py    # HC245, HC541, HC283, HC86, HC157, HC688, HC04, HC32, HC00, HC21
│   └── memory.py           # ROM, RAM
└── wiring.py               # Wire connections from 03_wiring_guide.md
```

---

## Implementation Order

1. `base.py` — Chip, Net, Simulator classes
2. `sequential.py` — HC574 first (most used)
3. `combinational.py` — HC04, HC00, HC32, HC86 first (simple gates)
4. `memory.py` — ROM, RAM
5. `wiring.py` — Connect everything per 03_wiring_guide
6. `chip_sim.py` — Main entry point + tests

---

## Acceptance Criteria

- [ ] All 35 chip objects created with correct pin count
- [ ] All pins wired according to 03_wiring_guide.md
- [ ] `LI $42` executes correctly (3 clocks)
- [ ] `ADDI $05` gives correct AC
- [ ] `SB` writes RAM correctly
- [ ] `SETDP + LB` reads correct page
- [ ] Probe any pin returns correct value
- [ ] Step-by-step matches soft_debug.py output
