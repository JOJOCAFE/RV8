# RTL Coder Memory

## Codebase

| File | Purpose |
|------|---------|
| `rtl/rv8gr_cpu.v` | Main CPU module (behavioral) |
| `tb/tb_rv8gr_full.v` | Full ISA test (127 cycles) |
| `tb/tb_rv8gr_irq.v` | IRQ test |
| `tb/tb_rv8gr_setdp.v` | SETDP test (160 cycles) |
| `tb/tb_rv8gr_opcode_sweep.v` | 512-case sweep |
| `sim/chip_sim.py` | Gate-level simulation (34 logic chips + ROM/RAM) |
| `sim/soft_debug.py` | High-level trace sim |

## Shared Components Repo

| Path | Purpose |
|------|---------|
| `/home/jo/kiro/Components/74HC/*.v` | Reusable 74HC behavioral chip models |
| `/home/jo/kiro/Components/Memory/*.v` | Reusable EEPROM/SRAM behavioral models |
| `/home/jo/kiro/Components/74HC/tests/tb_74hc_smoke.v` | Shared 74HC smoke test |
| `/home/jo/kiro/Components/Memory/tests/tb_memory_smoke.v` | Shared memory smoke test |
| `/home/jo/kiro/Components/python/chiplib` | Pin-level Python chip simulator that Verilog behavior must match |

## Conventions

- Single-file CPU with FSM (T0/T1/T2)
- `$readmemh` for ROM loading in testbenches
- iverilog + GTKWave
- Behavioral model (not gate-level in Verilog)

## Key Patterns

```verilog
localparam T0=0, T1=1, T2=2;
wire pc_load = jump | (branch & z_match);
wire [7:0] mem_read = pc[15] ? ram[pc[14:0]] : rom[pc[14:0]];
```

## Work Done

- rv8gr_cpu.v: complete, all tests pass
- 5 testbenches written and passing

## Pending

- RV8-R CPU model (when architect specs it)
- Example program .memh files for new tests

## Component Library Responsibility

- Own reusable Verilog component models and smoke tests in `/home/jo/kiro/Components`.
- Use `ttl_74hcxx` module names for 74HC logic and `mem_<part>` for memory models.
- Hand off any physical pinout/datasheet work to Ohm and any verification to Fern.
- Test from `/home/jo/kiro` with the 74HC and Memory smoke commands in `component-library/SKILL.md`.
- Sequential behavior now has edge-aware Python coverage. Preserve compatibility for 74HC73/112 falling-edge clocks, 74HC74 per-section clocks, 74HC595 SRCLK/RCLK separation, and 74HC593 RCK/CCK separation.
- 74HC112 Verilog was corrected to datasheet-style asynchronous preset/clear and negative-edge clock.
- RV8GR now also has generated chip-level Verilog from the KiCad/netlist source: `RV8GR/rtl/rv8gr_chip_level.v` with chip-level testbenches.
