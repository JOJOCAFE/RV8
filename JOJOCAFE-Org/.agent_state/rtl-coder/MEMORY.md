# RTL Coder Memory

## Codebase

| File | Purpose |
|------|---------|
| `rtl/rv8gr_cpu.v` | Main CPU module (behavioral) |
| `tb/tb_rv8gr_full.v` | Full ISA test (127 cycles) |
| `tb/tb_rv8gr_irq.v` | IRQ test |
| `tb/tb_rv8gr_setdp.v` | SETDP test (160 cycles) |
| `tb/tb_rv8gr_opcode_sweep.v` | 512-case sweep |
| `sim/chip_sim.py` | Gate-level simulation (35 chips) |
| `sim/soft_debug.py` | High-level trace sim |

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
