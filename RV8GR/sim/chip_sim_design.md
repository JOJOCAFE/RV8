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
