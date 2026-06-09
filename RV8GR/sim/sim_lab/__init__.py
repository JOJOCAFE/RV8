"""
RV8-GR Sim Lab — Step-by-step wiring and testing.

Like physical breadboard: wire a few chips, test with DIP switch + LED,
then treat tested group as a "black box" for the next step.

Lab Steps:
  lab01_ring_counter.py   — U8 + U24 (2 inv): T0/T1/T2 generation
  lab02_pc_counter.py     — U1-U4: 16-bit PC with count/load
  lab03_address_mux.py    — U15-U16: PC vs IRL address selection
  lab04_rom_fetch.py      — ROM + U7: read bytes from ROM
  lab05_ir_latch.py       — U5 + U6: latch control + operand
  lab06_alu.py            — U10-U13, U19-U20: ADD/SUB/XOR
  lab07_ac_mux.py         — U17-U18 + U9: result → AC
  lab08_control_logic.py  — U24-U28: derived signals
  lab09_full_fetch.py     — All above: fetch LI $42 from ROM
  lab10_full_execute.py   — Execute LI $42, verify AC=$42
"""
