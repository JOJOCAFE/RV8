"""
RV8-GR Sim Lab — Step-by-step wiring and testing.

Like physical breadboard: wire a few chips, test with DIP switch + LED,
then treat tested group as a "black box" for the next step.

Matches doc/labs/ and doc/06_debug_plan.md (14 steps).

Lab Files:
  lab01_power_clock.py    — Hardware only (no simulation)
  lab02_ring_counter.py   — U8 + U24: T0/T1/T2 generation
  lab03_pc_counter.py     — U1-U4: 16-bit PC with count/load/overflow
  lab04_address_mux.py    — U15-U16, U29-U30: PC vs IRL selection
  lab05_rom_fetch.py      — ROM + U7: read bytes from ROM
  lab06_ir_latch.py       — U5 + U6: latch control + operand
  lab07_alu.py            — U10-U13: ADD/SUB with carry
  lab08_ac_mux.py         — U17-U18 + U9: AC input mux + latch
  lab09_z_flag.py         — U21-U22 + control logic: Z detect + signals
  lab10_branch_jump.py    — Branch/Jump: PC_LD, PC_INC conditions
  lab11_page_register.py  — U23 + full fetch: SETPG + cross-page
  lab12_ram_datapage.py   — RAM + U32: SETDP, SB/LB with pages
  lab13_full_system.py    — All chips: execute LI $42 end-to-end
  lab14_irq_bus.py        — U31: IRQ latch, EI/DI, polling
"""
