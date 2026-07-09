# 74xx to 74HC Scan Map

Scan scope: `/home/jo/kiro` text-like documents, KiCad files, and PDFs with extractable text.

The `Components/Verilog/74xx` library maps `74LSxx`, `74HCTxx`, and bare `74xx` project references to `74HCxx` files when a same-function HC part is used or directly compatible for the project model.

## Added or already covered

| Project/reference part | 74HC library file | Source evidence |
|---|---|---|
| 74LS08, 74HC08 | `74hc08.v` with embedded pinout comments | RV8-Old KiCad/PDF, RV8 future upgrade docs |
| 74HC02 | `74hc02.v` with embedded pinout comments | RV8-Old wiring verification |
| 74HC14 | `74hc14.v` with embedded pinout comments | RV8GR-V2 reset wiring |
| 74HC30 | `74hc30.v` with embedded pinout comments | RV8-Old wiring verification |
| 74HC138 | `74hc138.v` with embedded pinout comments | RV8GR-V2/old RV8 decoder docs |
| 74HC139 | `74hc139.v` with embedded pinout comments | RV8GR/RV8 reference summary and docs |
| 74HC151 | `74hc151.v` with embedded pinout comments | RV8S wiring guide |
| 74HC153 | `74hc153.v` with embedded pinout comments | Reference summary and Computer requirements |
| 74LS157, 74HC157 | `74hc157.v` with embedded pinout comments | RV8GR-V2 and old RV8 KiCad/PDF |
| 74LS161, 74HC161 | `74hc161.v` with embedded pinout comments | RV8GR-V2 and old RV8 KiCad/PDF |
| 74HC164 | `74hc164.v` with embedded pinout comments | RV8GR-V2 ring counter |
| 74HC165 | `74hc165.v` with embedded pinout comments | RV8S and Computer docs |
| 74HC166 | `74hc166.v` with embedded pinout comments | Computer requirements |
| 74HC193 | `74hc193.v` with embedded pinout comments | RV8GR-V2 module notes |
| 74HC240 | `74hc240.v` with embedded pinout comments | Reference summary |
| 74HC244 | `74hc244.v` with embedded pinout comments | RV8R wiring guide |
| 74HCT245, 74LS245, 74HC245 | `74hc245.v` with embedded pinout comments | Trainer, RV8GR-V2, old RV8 KiCad/PDF |
| 74HC251 | `74hc251.v` with embedded pinout comments | RV8-Old wiring verification |
| 74HC257 | `74hc257.v` with embedded pinout comments | Computer requirements |
| 74HC273 | `74hc273.v` with embedded pinout comments | RV8GR-V2 wiring guide |
| 74LS283, 74HC283 | `74hc283.v` with embedded pinout comments | RV8GR-V2 and old RV8 KiCad/PDF |
| 74HC374 | `74hc374.v` with embedded pinout comments | RV8GR-V2 module notes |
| 74HC4078 | `74hc4078.v` with embedded pinout comments | RV8-Old wiring verification; STMicroelectronics local datasheet |
| 74HC541 | `74hc541.v` with embedded pinout comments | RV8GR-V2 and RV8G docs |
| 74LS574, 74HC574 | `74hc574.v` with embedded pinout comments | RV8GR-V2 and old RV8 KiCad/PDF |
| 74HC593 | `74hc593.v` with embedded pinout comments | RV8-Old design docs; STMicroelectronics local datasheet |
| 74HC595 | `74hc595.v` with embedded pinout comments | Programmer KiCad/PDF |
| 74HC688 | `74hc688.v` with embedded pinout comments | RV8GR-V2 and RV8G docs |
| 74HC922/MM74C922 | `74hc922.v` with embedded pinout comments | Trainer docs; Fairchild local datasheet |

Generic 7400-series references from reference books were not converted into files unless the same chip function also appeared in the RV8/RV8GR/Trainer project documents.
