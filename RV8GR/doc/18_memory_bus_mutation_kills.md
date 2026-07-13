# RV8GR Memory and Bus Mutation Kills

`tools/run_memory_bus_mutation.sh` is a testbench-only negative suite for the
unchanged structural RV8GR netlist.  It first proves the intended state, then
runs each deliberate fault and requires a nonzero exit with a named kill
marker.

| Fault | Baseline proof | Mutation proof |
| --- | --- | --- |
| ROM `/WE` | ROM instance `/WE` is hard-wired high and its selected byte remains unchanged. | A forced low-to-high `/WE` pulse during a ROM write window changes the EEPROM model byte. |
| U7 store direction | U7 `DIR=1` transfers the selected IBUS byte to RAM DBUS. | Reversing `DIR` while a different DBUS source is present writes a byte other than the selected IBUS byte. |
| U34/U7 output-enable order | U34 owns IBUS while U7 remains disabled. | Enabling U7 before U34 releases an opposite bit resolves IBUS to `X`. |

Run it with the same Components source selection used by the other structural
benches:

```bash
COMPONENTS_ROOT=/home/jo/kiro/Components \
  tools/run_memory_bus_mutation.sh
```

The suite uses hierarchical testbench forces only; it never changes production
RTL.  It proves digital model behavior and modelled ownership resolution.  It
does not sign off physical EEPROM/SRAM timing, 74HC turn-around deadband,
contention current, or a PCB clock limit.  Those require a wired board and
measurements.
