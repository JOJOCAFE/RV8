# Memory Component Library

Standalone behavioral Verilog models for the memory parts used or explicitly
allowed by the RV8 project docs. Each model embeds its DIP pinout notes as
comments near the top of the `.v` file.

Included devices:

- `at28c256.v` (`mem_at28c256`) - 32K x 8 parallel EEPROM
- `sst39sf010a.v` (`mem_sst39sf010a`) - 128K x 8 flash EEPROM
- `62256.v` (`mem_62256`) - generic 32K x 8 SRAM
- `as6c62256.v` (`mem_as6c62256`) - Alliance Memory-compatible 32K x 8 SRAM wrapper
- `cy7c199.v` (`mem_cy7c199`) - Cypress/Infineon-compatible 32K x 8 SRAM wrapper

Each device keeps the Verilog behavior and manufacturer-backed DIP pinout
documentation together in the matching `.v` file.

The Python memory models in `../python/` use the real 28-pin DIP pin numbers.
The Verilog memory models keep HDL-friendly vector ports, but their read,
write, output-enable, and high-Z behavior must match the Python models for
overlapping parts.

Manufacturer datasheet sources used for pinouts:

- Microchip AT28C256: https://ww1.microchip.com/downloads/en/DeviceDoc/doc0006.pdf
- Microchip SST39SF010A: https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/SST39SF010A-SST39SF020A-SST39SF040-Data-Sheet-DS20005022.pdf
- Alliance Memory AS6C62256: https://www.alliancememory.com/wp-content/uploads/pdf/AS6C62256.pdf
- Infineon/Cypress CY7C199: https://www.infineon.com/dgdl/Infineon-CY7C199_32K_x_8_Static_RAM-DataSheet-v07_00-EN.pdf

Run the smoke test with:

```sh
iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Verilog/Memory/*.v Components/Verilog/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```
