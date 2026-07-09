# 74HC Verilog Chip Library

Standalone behavioral Verilog models for the RV8/RV8GR/Trainer 74HC logic
package set found under `/home/jo/kiro`.
The coding style follows the simple module naming, optional `DELAY_RISE` /
`DELAY_FALL` parameter pattern, and compact behavioral style used by
`/tmp/ice-chips-verilog/source-7400`.

Included chips:

- `74hc00.v` (`ttl_74hc00`) - quad 2-input NAND gate
- `74hc02.v` (`ttl_74hc02`) - quad 2-input NOR gate
- `74hc04.v` (`ttl_74hc04`) - hex inverter
- `74hc08.v` (`ttl_74hc08`) - quad 2-input AND gate
- `74hc14.v` (`ttl_74hc14`) - hex Schmitt-trigger inverter
- `74hc21.v` (`ttl_74hc21`) - dual 4-input AND gate
- `74hc30.v` (`ttl_74hc30`) - single 8-input NAND gate
- `74hc32.v` (`ttl_74hc32`) - quad 2-input OR gate
- `74hc74.v` (`ttl_74hc74`) - dual D flip-flop with asynchronous preset and clear
- `74hc86.v` (`ttl_74hc86`) - quad 2-input XOR gate
- `74hc138.v` (`ttl_74hc138`) - 3-line to 8-line decoder/demultiplexer
- `74hc139.v` (`ttl_74hc139`) - dual 2-line to 4-line decoder/demultiplexer
- `74hc151.v` (`ttl_74hc151`) - 8-line to 1-line data selector/multiplexer
- `74hc153.v` (`ttl_74hc153`) - dual 4-line to 1-line data selector/multiplexer
- `74hc157.v` (`ttl_74hc157`) - quad 2-input multiplexer with active-low enable
- `74hc161.v` (`ttl_74hc161`) - 4-bit binary counter with parallel load and asynchronous clear
- `74hc164.v` (`ttl_74hc164`) - 8-bit serial-in parallel-out shift register
- `74hc165.v` (`ttl_74hc165`) - 8-bit parallel-load shift register
- `74hc166.v` (`ttl_74hc166`) - 8-bit parallel-load shift register with clear
- `74hc193.v` (`ttl_74hc193`) - 4-bit synchronous up/down binary counter
- `74hc240.v` (`ttl_74hc240`) - octal inverting buffer/line driver with 3-state outputs
- `74hc244.v` (`ttl_74hc244`) - octal buffer/line driver with 3-state outputs
- `74hc245.v` (`ttl_74hc245`) - octal bus transceiver with 3-state outputs
- `74hc251.v` (`ttl_74hc251`) - 8-line to 1-line data selector with 3-state outputs
- `74hc257.v` (`ttl_74hc257`) - quad 2-input multiplexer with 3-state outputs
- `74hc273.v` (`ttl_74hc273`) - octal D-type flip-flop with asynchronous clear
- `74hc283.v` (`ttl_74hc283`) - 4-bit binary full adder with carry
- `74hc374.v` (`ttl_74hc374`) - octal D-type flip-flop with 3-state outputs
- `74hc4078.v` (`ttl_74hc4078`) - 8-input NOR/OR gate
- `74hc541.v` (`ttl_74hc541`) - octal buffer/line driver with 3-state outputs
- `74hc574.v` (`ttl_74hc574`) - octal D-type flip-flop with 3-state outputs
- `74hc593.v` (`ttl_74hc593`) - 8-bit binary counter with input register and 3-state I/O
- `74hc595.v` (`ttl_74hc595`) - 8-bit serial-in shift register with output register
- `74hc688.v` (`ttl_74hc688`) - 8-bit identity comparator with active-low enable and output
- `74hc922.v` (`ttl_74hc922`) - 16-key encoder behavioral model

Project-used chips and future-use imports keep model and pinout documentation
together in the matching `74hcxx.v` file, for example `74hc00.v`. The embedded
pinout comments cite the manufacturer datasheet PDF used for verification.
Parts without clean HC-family manufacturer DIP evidence are omitted instead of
kept as placeholders.

See `SCAN_74XX_MAP.md` for the whole-folder scan result, LS/HCT-to-HC mapping,
and PDF evidence summary.

Additional future-use models imported from JOJOCAFE ice-chips-verilog/source-7400 are listed in `SOURCE_7400_COVERAGE.md`. These files use HC names such as `74hc10.v` and module names such as `ttl_74hc10`.

Memory devices such as AT28C256 EEPROM and 62256 SRAM are intentionally not
modeled in this `Verilog/74xx/` logic-chip library.

Run the smoke test with:

```sh
iverilog -g2012 -Wall -o /tmp/tb_74xx_smoke.vvp Components/Verilog/74xx/*.v Components/Verilog/74xx/tests/tb_74xx_smoke.v
vvp /tmp/tb_74xx_smoke.vvp
```

Yosys can parse and elaborate these files, but it warns on the intentionally
bidirectional/tri-state devices (`74HC245`, `74HC541`, `74HC574`). Use the
Icarus smoke test above as the primary behavior check for this library.
