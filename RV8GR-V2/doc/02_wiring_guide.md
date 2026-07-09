# RV8-GR — Wiring Guide (Official)

**34 logic chips + ROM + RAM = 36 packages. Source of truth for physical build.**

---

## Memory Map

```
$0000-$7EFF  ROM 32KB (bankable to 128KB)
$7F00-$7FFF  ROM (available)  ## ********* For Future Use in Rom Switch*##
$8000-$FEFF  RAM 32KB (registers at $8000-$8007, data, executable)
$FF00-$FF0F  RAM (available; future vector area)
$FF10-$FF1F  I/O Slot 1 (/SLOT1 on bus)
$FF20-$FF2F  I/O Slot 2 (/SLOT2 on bus)
$FF30-$FFFF  RAM: available
Reset → $0000
```

> 📌 **Boot Requirements (first 3 instructions in ROM):**
>
> ```asm
> $0000: SETDP $80       ; DP → RAM (registers at $8000-$8007)
> $0002: SETPG $00       ; PG → page 0 (safe jumps)
> $0004: LI $00          ; AC = 0, Z = 1
> ```
>
> Why: PG, DP, AC have no hardware reset (74HC574 has no /CLR pin).
> These 3 instructions don't use SRC/STR, so random DP/PG values are harmless.
>
> **DP ranges:** $80-$FF = RAM (read/write) · $00-$7F = ROM (read only, SB ignored)

---

## Timing Note — Official Clock Target: 1 MHz

### Summary

| Clock | ROM | Status |
|:-----:|:---:|:------:|
| **1 MHz** | 70ns or 150ns | ✅ **Official target** — works with any ROM |
| 2 MHz | 70ns | ✅ Achievable on short-wire breadboard |
| 5 MHz | 70ns | ⚠️ PCB only (experimental) |

### The Worst Case: Fetch After Memory-Access Instruction

After LB/SB/ADD/SUB/XOR/SETPG_R (/ADDR_MODE=0 during T2), the address mux switches from {DP,IRL} back to PC at the T2→T0 boundary. ROM then needs access time before U5 can latch valid data.

**Timing chain** (worst case — fetch after LB/SB):
```
T2→T0 edge (ring counter shifts)
  → /ADDR_MODE returns HIGH (U26 propagation: ~15ns)
    → Mux switches to PC (U15/U29 propagation: ~15ns)
      → ROM sees new address (access time: 70-150ns)
        → U7 buffer (12ns)
          → Data valid on IBUS
            → U5 latches at NEXT T0 rising edge
```

**Time available** = one full clock period (T0 phase duration):

| Clock | Phase period | Worst path (150ns ROM) | Margin |
|:-----:|:------------:|:----------------------:|:------:|
| 1 MHz | 1000ns | 15+15+150+12 = 192ns | **+808ns ✅** |
| 2 MHz | 500ns | 192ns | **+308ns ✅** |
| 5 MHz | 200ns | 192ns | **+8ns ⚠️** |

**Why 1 MHz is completely safe**: Even with 150ns ROM + breadboard stray capacitance (~50ns extra), total worst path ≈ 242ns. At 1 MHz each phase is 1000ns — over 700ns margin.

**Why 5 MHz is risky**: 200ns per phase, worst path 192ns on paper. Zero margin for breadboard capacitance. PCB-only.

### Critical Path: ALU (separate concern)

The ALU path (IR → XOR → Adder → AC mux → AC setup) is internal to T2 and does NOT involve ROM timing:

| Stage | Chip | Typ ns |
|-------|------|:------:|
| XOR B-mux | 74HC157 | 15 |
| XOR array | 74HC86 | 12 |
| Adder 8-bit ripple | 74HC283 ×2 | 40 |
| AC input mux | 74HC157 | 15 |
| AC setup time | 74HC574 | 10 |
| **Total** | | **~92ns** |

This fits easily within 1 phase at 1 MHz (1000ns).

### Critical Timing Paths (PCB v1.1 Reference)

| Path | Chips | Typ ns | Critical? |
|------|-------|:------:|:---------:|
| ROM → U7 → U5 (fetch) | ROM + 74HC245 + 74HC574 | 70+12+5 = 87 | **Yes** |
| RAM → U7 → AC (load) | RAM + 74HC245 + mux + 574 | 70+12+15+5 = 102 | **Yes** |
| IR → ALU → AC (execute) | 74HC157+86+283×2+157+574 | 15+12+40+15+5 = 87 | **Yes** |
| Z → Branch → PC (BEQ) | 74HC86 + 00 + 161 | 12+12+15 = 39 | Medium |
| PG → PC load (J) | 74HC574 → 161 D-inputs | 0 (static) | Low |
| DP → Addr mux (SRC) | 74HC574 → 157 | 0+15 = 15 | Low |

> 📌 **PCB layout priority**: Place ROM/RAM/U7/U5 close together (fetch path).
> ALU cluster (U12-U13, U10-U11, U17-U18, U9) as second priority.
> Branch logic (U21, U28, U26) is fast — placement less critical.

### Conclusion

**1 MHz = no timing risk.** Use AT28C256-70ns or even 150ns ROM.
Start breadboard at 1 MHz. Test up to 2 MHz if desired. 5 MHz = PCB/wire-wrap only.

> 📌 **ROM/RAM recommendation: 70ns** (AT28C256-70, 62256-70 or CY7C199-15)
> This gives maximum headroom for future clock increase.
> 150ns parts work fine at 1-2 MHz.

### Master Timing Table (one instruction = 3 phases)

| Phase | Action | Signals Asserted | Data Flow |
|:-----:|--------|------------------|-----------|
| T0 | Fetch opcode | PC_INC=1, U5 CLK↑ | PC→ABUS→ROM→DBUS→U7→IBUS→U5 |
| T1 | Fetch operand | PC_INC=1, U6 CLK↑ | PC→ABUS→ROM→DBUS→U7→IBUS→U6 |
| T2 | Execute | (depends on instruction) | See below |

**T2 actions by instruction type:**

| Type | Key Signals at T2 | What happens |
|------|-------------------|-------------|
| ADDI/SUBI | ACC_CLK↑, /IRL_OE=LOW | U34 drives IRL→IBUS→XOR→Adder→mux→AC |
| ADD/SUB/LB | ACC_CLK↑, /ADDR_MODE=LOW | IRL→ABUS→RAM→DBUS→U7→IBUS→ALU→AC |
| XORI | ACC_CLK↑, /IRL_OE=LOW | U34 drives IRL→IBUS→XOR(with AC)→mux→AC |
| LI | ACC_CLK↑, /IRL_OE=LOW | U34 drives IRL→IBUS→XOR(pass)→mux→AC |
| SB | /AC_BUF=LOW, /ADDR_MODE=LOW | AC→U14→IBUS→U7→DBUS→RAM |
| J/BEQ/BNE | /PC_LD=LOW | {PG,IRL}→PC D-inputs→PC loads |
| SETPG | PG_CLK↑ | IBUS→U23 (PG register) |
| SETDP | DP_Load↑ | IBUS→U32 (DP register) |
| EI | EI_decode↑ | U31 IE=1 |
| DI | no v1.0 state change | Software marker; reset clears IE |
| NOP | (nothing) | PC already incremented |

**Key rule**: Only ONE IBUS driver active at T2:
- SRC=0, STR=0 → U34 (immediate from IRL)
- SRC=1 → U7 (RAM data)
- STR=1 → U14 (AC value for store)

### T0/T1/T2 Timing Diagram

```
CLK     __|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__
         1    2    3    4    5    6    7    8    9

T0      ‾‾‾|___________________________________|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
T1      ‾‾‾‾‾‾‾‾‾‾‾‾|_________________________|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
T2      ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|_____________|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
              ↑fetch op    ↑fetch imm    ↑execute
              U5 CLK       U6 CLK        ACC_CLK/PG_CLK/DP_Load
```

(Ring counter U8: shift register cycles T0→T1→T2→T0)

### Bus Ownership (who drives DBUS/IBUS per phase)

| Phase | ABUS driven by | DBUS driven by | IBUS driven by |
|:-----:|:--------------:|:--------------:|:--------------:|
| T0 | PC (U1-U4 via mux) | ROM (data out) | U7 (DBUS→IBUS) |
| T1 | PC (U1-U4 via mux) | ROM (data out) | U7 (DBUS→IBUS) |
| T2, SRC=0 STR=0 | PC (unchanged) | ROM (stale) | **U34** (IRL→IBUS) |
| T2, SRC=1 | DP:IRL (via mux) | RAM (data out) | **U7** (DBUS→IBUS) |
| T2, STR=1 | DP:IRL (via mux) | **U7** (IBUS→DBUS) | **U14** (AC→IBUS) |

Note: During T2+STR, U7 reverses direction (WR_DIR=1) to write DBUS from IBUS.



### Reset & Standalone Boot (boots from ROM at $0000)

**Circuit**: RC (10kΩ + 10µF) → 74HC14 Schmitt → /RST LOW ~100ms at power-on.

**Wiring**:
```
U1 (PC 0-3):   /CLR ← /RST,   /LD ← /PC_LD (U26-11)
U2 (PC 4-7):   /CLR ← /RST,   /LD ← /PC_LD (U26-11)
U3 (PC 8-11):  /CLR ← /RST,   /LD ← /PC_LD (U26-11)
U4 (PC 12-15): /CLR ← /RST,   /LD ← /PC_LD (U26-11)
U8:  /CLR ← /RST
U31: /CLR1,/CLR2 ← /RST
```

**How it works**:
1. Power on: /RST=LOW for ~100ms (RC circuit)
2. U1-U4: /CLR=LOW → PC[15:0] = $0000 (async, immediate)
3. /RST releases → normal mode. PC = $0000 ✅
4. CPU fetches first instruction from ROM!

**Normal jump operation**: /PC_LD=LOW → loads {PG, IRL} into PC.
U3-U4 D-inputs connect to PG (U23 outputs).

**FINAL DECISION for v1.0:**

```
U1-U4: ALL /CLR ← /RST, ALL /LD ← /PC_LD (standard, no diodes)
PC resets to $0000. ROM is at $0000-$7FFF. Boots directly from ROM.
TRUE standalone boot supported — no Programmer needed at power-on.
```

**Register states after reset:**

| Register | Value | How |
|----------|:-----:|-----|
| PC | $0000 | /CLR resets all counters to 0 |
| PG | ? | 74HC574 has no /CLR — indeterminate |
| DP | ? | 74HC574 has no /CLR — indeterminate |
| AC | ? | 74HC574 has no /CLR — indeterminate |
| Z | ? | 74HC74 /CLR not connected to /RST |
| IE | 0 | /CLR ← /RST |
| IRQ_FF | 0 | /CLR ← /RST |

> 📌 **Standalone boot is native in v1.0.**
> PC resets to $0000 which is in ROM space. No boot stub needed.
> First instruction in ROM executes immediately after reset.

> 📌 **PG, DP, AC are indeterminate at power-on** (74HC574 has no /CLR).
> Boot sequence handles this — see "Boot Requirements" above.
> No hardware fix needed (74HC273 resets to $00, but we need DP=$80).
> - ต้องการ DP=$80 (bit7=1) → ต้อง preset ซึ่งซับซ้อนเกิน
> - Software init (`SETDP $80`) ง่ายกว่า + ไม่เพิ่ม hardware

### Placement Notes (breadboard)

```
U21 (Z flag) and U22 (comparator): place adjacent — minimize /PR wire length.
U10-U11 (adder): place adjacent — carry chain is timing-critical.
U12-U13 (XOR) near U10-U11: minimize ALU path delay.
U5-U6 (IR) near ROM/U7: minimize fetch path delay.
Bypass caps: one per chip, as close to VCC/GND pins as possible.
```

---

## RV8-Bus (40-pin System Bus)

CPU board ↔ Expansion/Programmer ผ่าน 40-pin IDC connector

```
┌──────────────────────────────────────────────────────────┐
│                   RV8-Bus (40 pins)                        │
├──────────────────────────────────────────────────────────┤
│ Pin  Signal    Dir   │ Pin  Signal    Dir                 │
│  1   A0        out   │  2   A1        out                 │
│  3   A2        out   │  4   A3        out                 │
│  5   A4        out   │  6   A5        out                 │
│  7   A6        out   │  8   A7        out                 │
│  9   A8        out   │ 10   A9        out                 │
│ 11   A10       out   │ 12   A11       out                 │
│ 13   A12       out   │ 14   A13       out                 │
│ 15   A14       out   │ 16   A15       out                 │
│ 17   D0        bidir │ 18   D1        bidir               │
│ 19   D2        bidir │ 20   D3        bidir               │
│ 21   D4        bidir │ 22   D5        bidir               │
│ 23   D6        bidir │ 24   D7        bidir               │
│ 25   CLK       out   │ 26   /RST      out                 │
│ 27   /WR       out   │ 28   /RD       out                 │
│ 29   /IRQ      in    │ 30   /SLOT1    out                 │
│ 31   /SLOT2    out   │ 32   T2        out                 │
│ 33   A15       out   │ 34   (reserved)                    │
│ 35   (reserved)      │ 36   (reserved)                    │
│ 37   (reserved)      │ 38   (reserved)                    │
│ 39   VCC (+5V)       │ 40   GND                           │
└──────────────────────────────────────────────────────────┘
```

### Signal Description

| Pin | Signal | Dir | Source | Description |
|:---:|--------|:---:|--------|-------------|
| 1-16 | A[15:0] | out | Addr Mux | 16-bit address bus |
| 17-24 | D[7:0] | bidir | U7/ROM/RAM | 8-bit data bus |
| 25 | CLK | out | Oscillator | System clock (1 MHz breadboard target; 5 MHz PCB-only experiment) |
| 26 | /RST | out | RC+button | Active-low reset |
| 27 | /WR | out | /AC_BUF (U26-8) | Write strobe (LOW during T2+STORE) |
| 28 | /RD | out | /T2 or fetch | Read strobe |
| 29 | /IRQ | in | Peripheral | Active-low IRQ request; U31 latches on release/rising edge |
| 30 | /SLOT1 | out | Address decode | I/O slot 1 select |
| 31 | /SLOT2 | out | Address decode | I/O slot 2 select |
| 32 | T2 | out | U8-5 | Execute phase (for expansion timing) |
| 33 | A15 | out | U30-12 | Duplicate for chip select |
| 39 | VCC | — | Power | +5V |
| 40 | GND | — | Power | Ground |

### Bus Timing

```
        ┌───┐   ┌───┐   ┌───┐   ┌───┐
CLK:  ──┘   └───┘   └───┘   └───┘   └──
        T0       T1       T2       T0
A[15:0]: ←── PC ──→←── PC ──→←─ IRL ─→←── PC ──→
D[7:0]:  ←─ ctrl ─→←─ oper ─→←─ data ─→←─ ctrl ─→
/WR:   ─────────────────────┐       ┌───────────
                             └───────┘ (T2+STORE only)
```

---

## Virtual Internal Net Names

These names are wiring labels for the existing physical nets. They do not add
chips or extra buses. Use them on the schematic and breadboard labels so every
module can be wired and debugged without tracing long source/destination notes.

### External RV8-Bus vs Internal Nets

| Name | Scope | Meaning |
|------|-------|---------|
| RV8_A0..RV8_A15 | 40-pin connector | External address pins. Same physical nets as `ABUS0..ABUS15`. |
| RV8_D0..RV8_D7 | 40-pin connector | External data pins. Same physical nets as `DBUS0..DBUS7`. |
| RV8_CLK, RV8_/RST, RV8_/WR, RV8_/RD, RV8_/IRQ | 40-pin connector | External control pins. |
| PC0..PC15 | CPU internal | Program counter register outputs. |
| IRL0..IRL7 | CPU internal | Operand register outputs from U6. Also feed PC load and address mux. |
| PG0..PG7 | CPU internal | Code page register outputs from U23. Feed PC high load inputs. |
| DP0..DP7 | CPU internal | Data page register outputs from U32. Feed address mux high A inputs. |
| AC0..AC7 | CPU internal | Accumulator outputs from U9. Feed ALU, zero detect, and U14 store buffer. |
| IBUS0..IBUS7 | CPU internal | Internal data bus. Used for instruction fetch, immediates, ALU input, SETPG/SETDP, and store source. |
| DBUS0..DBUS7 | Memory/RV8-Bus | Memory data bus shared by ROM, RAM, U7, and RV8 data pins. |
| ABUS0..ABUS15 | Memory/RV8-Bus | Address mux outputs shared by ROM, RAM, decode, and RV8 address pins. |
| SUM0..SUM7 | CPU internal | 74HC283 adder outputs. |
| XOR_Y0..XOR_Y7 | CPU internal | XOR array outputs. |

Naming rules:
- Bit 0 is always the least significant bit.
- A leading `/` means active-low (`/RST`, `/PC_LD`, `/IRL_OE`).
- A `_N` suffix also means active-low when `/` is awkward in labels (`BUF_OE_N`).
- A `*` after a pin in the bus tables means that chip only drives the bus when
  its output enable is active.

---

## Virtual Internal Buses

### DBUS0..DBUS7 — Memory/RV8 Data Bus

DBUS is the real bidirectional memory data bus. It is also exported as RV8-Bus
pins 17-24 (`RV8_D0..RV8_D7`).

```
DBUS0 ←→ ROM D0, RAM D0, U7-18, RV8_D0 (pin 17)
DBUS1 ←→ ROM D1, RAM D1, U7-17, RV8_D1 (pin 18)
DBUS2 ←→ ROM D2, RAM D2, U7-16, RV8_D2 (pin 19)
DBUS3 ←→ ROM D3, RAM D3, U7-15, RV8_D3 (pin 20)
DBUS4 ←→ ROM D4, RAM D4, U7-14, RV8_D4 (pin 21)
DBUS5 ←→ ROM D5, RAM D5, U7-13, RV8_D5 (pin 22)
DBUS6 ←→ ROM D6, RAM D6, U7-12, RV8_D6 (pin 23)
DBUS7 ←→ ROM D7, RAM D7, U7-11, RV8_D7 (pin 24)
```

### IBUS0..IBUS7 — CPU Internal Data Bus

Drivers (tri-state, only one active in normal operation):
- U7 drives `DBUS -> IBUS` during fetch/load/read paths.
- U34 drives `IRL -> IBUS` for immediate/operand execution paths.
- U14 drives `AC -> IBUS` only during store.

```
IBUS0 ←→ U7-2, U34-18*, U14-18*, U12-1,  U23-2, U32-2, U5-2, U6-2
IBUS1 ←→ U7-3, U34-17*, U14-17*, U12-4,  U23-3, U32-3, U5-3, U6-3
IBUS2 ←→ U7-4, U34-16*, U14-16*, U12-9,  U23-4, U32-4, U5-4, U6-4
IBUS3 ←→ U7-5, U34-15*, U14-15*, U12-12, U23-5, U32-5, U5-5, U6-5
IBUS4 ←→ U7-6, U34-14*, U14-14*, U13-1,  U23-6, U32-6, U5-6, U6-6
IBUS5 ←→ U7-7, U34-13*, U14-13*, U13-4,  U23-7, U32-7, U5-7, U6-7
IBUS6 ←→ U7-8, U34-12*, U14-12*, U13-9,  U23-8, U32-8, U5-8, U6-8
IBUS7 ←→ U7-9, U34-11*, U14-11*, U13-12, U23-9, U32-9, U5-9, U6-9
```

### ABUS0..ABUS15 — Address Mux Output Bus

ABUS is the final address after the PC/IRL/DP muxes. It is also exported as
RV8-Bus pins 1-16 and duplicated on pin 33 for `ABUS15`.

```
ABUS0  ← U15-4     ABUS8  ← U29-4
ABUS1  ← U15-7     ABUS9  ← U29-7
ABUS2  ← U15-9     ABUS10 ← U29-9
ABUS3  ← U15-12    ABUS11 ← U29-12
ABUS4  ← U16-4     ABUS12 ← U30-4
ABUS5  ← U16-7     ABUS13 ← U30-7
ABUS6  ← U16-9     ABUS14 ← U30-9
ABUS7  ← U16-12    ABUS15 ← U30-12
```

### Register Output Nets

```
PC0..PC15   ← U1-U4 Q outputs
IRL0..IRL7 ← U6 Q outputs
PG0..PG7   ← U23 Q outputs
DP0..DP7   ← U32 Q outputs
AC0..AC7   ← U9 Q outputs
SUM0..SUM7 ← U10-U11 sum outputs
XOR_Y0..7  ← U12-U13 XOR outputs
```

---

## Critical Nets Summary

Key control signals — source chip/pin and all destinations. Verify these first during debug.

| Signal | Source | Destinations |
|--------|--------|-------------|
| PC_INC | U25-6 (T0 OR T1) | U1-7, U1-10, U2-7, U3-7, U4-7 (ENP/ENT) |
| /PC_LD | U26-11 | U1-9, U2-9, U3-9, U4-9 (/LD) |
| ACC_CLK | U27-11 (NAND T2,AC_WR) | U9-11 (AC CLK), U21-3 (Z CLK) |
| ADDR_REQ | U25-3 (SRC OR STR) | U26-4 |
| /ADDR_MODE | U26-6 (NAND ADDR_REQ,T2) | U15-1, U16-1, U29-1, U30-1, U26-2, U33-4 |
| BUF_OE_N | U24-12 (NOT /IRL_OE) | U7-19 (/OE) |
| WR_DIR | U28-8 (XOR gate) | U7-1 (DIR), ROM /OE |
| /AC_BUF | U26-8 (NAND T2,STR) | U14-1, U14-19 (/OE), RAM /WE |
| /IRL_OE | U26-3 (NAND T2,/ADDR_MODE) | U34-1, U34-19, U24-13 |
| DP_Load | U33-6 (AND gate 1) | U32-11 (CLK) |
| PG_CLK | U25-11 (/T2 OR /PG_cond) | U23-11 (CLK) |
| /RST | Reset circuit (RC+Schmitt) | U1-1, U2-1, U3-1, U4-1, U8-9, U31-1, U31-13 |
| CLK | Oscillator | U1-2, U2-2, U3-2, U4-2, U8-8, RV8_CLK |

> 📌 If a signal is wrong, check: (1) source chip output, (2) each destination pin, (3) solder/wire continuity.
> These 12 nets account for >80% of debug issues on breadboard builds.

---

## Chip Pin Wiring

### U1-U2 74HC161 — PC Low (bits 0-7)

```
U1: PC bits 0-3
U1-1  (/CLR) ← /RST          U1-2  (CLK)  ← CLK
U1-3  (D0)   ← IRL0          U1-4  (D1)   ← IRL1
U1-5  (D2)   ← IRL2          U1-6  (D3)   ← IRL3
U1-7  (ENP)  ← PC_INC (U25-6)
U1-8  (GND)  → GND
U1-9  (/LD)  ← /PC_LD (U26-11)
U1-10 (ENT)  ← PC_INC (U25-6)
U1-11 (QD)   → PC3 → U15-14
U1-12 (QC)   → PC2 → U15-11
U1-13 (QB)   → PC1 → U15-5
U1-14 (QA)   → PC0 → U15-2
U1-15 (RCO)  → U2-10
U1-16 (VCC)  → VCC

U2: PC bits 4-7
U2-1  (/CLR) ← /RST          U2-2  (CLK)  ← CLK
U2-3  (D0)   ← IRL4          U2-4  (D1)   ← IRL5
U2-5  (D2)   ← IRL6          U2-6  (D3)   ← IRL7
U2-7  (ENP)  ← PC_INC (U25-6)
U2-8  (GND)  → GND
U2-9  (/LD)  ← /PC_LD (U26-11)
U2-10 (ENT)  ← U1-15 (RCO)
U2-11 (QD)   → PC7 → U16-14
U2-12 (QC)   → PC6 → U16-11
U2-13 (QB)   → PC5 → U16-5
U2-14 (QA)   → PC4 → U16-2
U2-15 (RCO)  → U3-10
U2-16 (VCC)  → VCC
```

### U3-U4 74HC161 — PC High (bits 8-15)

```
U3: PC bits 8-11
U3-1  (/CLR) ← /RST          U3-2  (CLK)  ← CLK
U3-3  (D0)   ← PG0           U3-4  (D1)   ← PG1
U3-5  (D2)   ← PG2           U3-6  (D3)   ← PG3
U3-7  (ENP)  ← PC_INC (U25-6)
U3-8  (GND)  → GND
U3-9  (/LD)  ← /PC_LD (U26-11)
U3-10 (ENT)  ← U2-15 (RCO)
U3-11 (QD)   → PC11 → U29-14
U3-12 (QC)   → PC10 → U29-11
U3-13 (QB)   → PC9  → U29-5
U3-14 (QA)   → PC8  → U29-2
U3-15 (RCO)  → U4-10
U3-16 (VCC)  → VCC

U4: PC bits 12-15
U4-1  (/CLR) ← /RST          U4-2  (CLK)  ← CLK
U4-3  (D0)   ← PG4           U4-4  (D1)   ← PG5
U4-5  (D2)   ← PG6           U4-6  (D3)   ← PG7
U4-7  (ENP)  ← PC_INC (U25-6)
U4-8  (GND)  → GND
U4-9  (/LD)  ← /PC_LD (U26-11)
U4-10 (ENT)  ← U3-15 (RCO)
U4-11 (QD)   → PC15 → U30-14
U4-12 (QC)   → PC14 → U30-11
U4-13 (QB)   → PC13 → U30-5
U4-14 (QA)   → PC12 → U30-2
U4-15 (RCO)  → NC
U4-16 (VCC)  → VCC
```

### U5 74HC574 — IR_HIGH (Control Byte)

```
U5-1  (/OE) → GND
U5-2  (D1)  ← IBUS0           U5-3  (D2)  ← IBUS1
U5-4  (D3)  ← IBUS2           U5-5  (D4)  ← IBUS3
U5-6  (D5)  ← IBUS4           U5-7  (D6)  ← IBUS5
U5-8  (D7)  ← IBUS6           U5-9  (D8)  ← IBUS7
U5-10 (GND) → GND
U5-11 (CLK) ← T0 (U8-3)
U5-12 (Q8)  → ALU_SUB (bit7)
U5-13 (Q7)  → XOR_MODE (bit6)
U5-14 (Q6)  → MUX_SEL (bit5)
U5-15 (Q5)  → AC_WR (bit4)
U5-16 (Q4)  → SOURCE_TYPE (bit3)
U5-17 (Q3)  → STORE (bit2)
U5-18 (Q2)  → BRANCH (bit1)
U5-19 (Q1)  → JUMP (bit0)
U5-20 (VCC) → VCC
```

### U6 74HC574 — IR_LOW (Operand)

```
U6-1  (/OE) → GND (IRL outputs always available to PC load and address/U34 inputs)
U6-2  (D1)  ← IBUS0           U6-3  (D2)  ← IBUS1
U6-4  (D3)  ← IBUS2           U6-5  (D4)  ← IBUS3
U6-6  (D5)  ← IBUS4           U6-7  (D6)  ← IBUS5
U6-8  (D7)  ← IBUS6           U6-9  (D8)  ← IBUS7
U6-10 (GND) → GND
U6-11 (CLK) ← T1 (U8-4)
U6-12 (Q8)  → IRL7 → U16-14, U2-6, U34-9
U6-13 (Q7)  → IRL6 → U16-11, U2-5, U34-8
U6-14 (Q6)  → IRL5 → U16-5,  U2-4, U34-7
U6-15 (Q5)  → IRL4 → U16-2,  U2-3, U34-6
U6-16 (Q4)  → IRL3 → U15-14, U1-6, U34-5
U6-17 (Q3)  → IRL2 → U15-11, U1-5, U34-4
U6-18 (Q2)  → IRL1 → U15-5,  U1-4, U34-3
U6-19 (Q1)  → IRL0 → U15-2,  U1-3, U34-2
U6-20 (VCC) → VCC
```

### U34 74HC541 — IRL-to-IBUS Immediate Buffer

```
U34-1  (/OE1) ← /IRL_OE (U26-3)
U34-2  (A1)   ← IRL0           U34-18 (Y1) → IBUS0
U34-3  (A2)   ← IRL1           U34-17 (Y2) → IBUS1
U34-4  (A3)   ← IRL2           U34-16 (Y3) → IBUS2
U34-5  (A4)   ← IRL3           U34-15 (Y4) → IBUS3
U34-6  (A5)   ← IRL4           U34-14 (Y5) → IBUS4
U34-7  (A6)   ← IRL5           U34-13 (Y6) → IBUS5
U34-8  (A7)   ← IRL6           U34-12 (Y7) → IBUS6
U34-9  (A8)   ← IRL7           U34-11 (Y8) → IBUS7
U34-10 (GND)  → GND
U34-19 (/OE2) ← /IRL_OE (U26-3)
U34-20 (VCC)  → VCC
```

### U7 74HC245 — Bus Buffer (DBUS↔IBUS)

```
U7-1  (DIR) ← WR_DIR (U28-8)
U7-2  (A1)  ←→ IBUS0          U7-18 (B1)  ←→ DBUS0
U7-3  (A2)  ←→ IBUS1          U7-17 (B2)  ←→ DBUS1
U7-4  (A3)  ←→ IBUS2          U7-16 (B3)  ←→ DBUS2
U7-5  (A4)  ←→ IBUS3          U7-15 (B4)  ←→ DBUS3
U7-6  (A5)  ←→ IBUS4          U7-14 (B5)  ←→ DBUS4
U7-7  (A6)  ←→ IBUS5          U7-13 (B6)  ←→ DBUS5
U7-8  (A7)  ←→ IBUS6          U7-12 (B7)  ←→ DBUS6
U7-9  (A8)  ←→ IBUS7          U7-11 (B8)  ←→ DBUS7
U7-10 (GND) → GND
U7-19 (/OE) ← BUF_OE_N (U24-12)
U7-20 (VCC) → VCC

Direction (real 74HC245 datasheet):
  DIR=0 (WR_DIR=0): B→A = DBUS→IBUS (READ)
  DIR=1 (WR_DIR=1): A→B = IBUS→DBUS (WRITE/STORE)
```

### U8 74HC164 — Ring Counter (T0/T1/T2)

```
U8-1  (A)    ← NOT(Q0) (U24-2)
U8-2  (B)    ← NOT(Q1) (U24-4)
U8-3  (Q0)   → T0
U8-4  (Q1)   → T1
U8-5  (Q2)   → T2
U8-6  (Q3)   → NC
U8-7  (GND)  → GND
U8-8  (CLK)  ← CLK
U8-9  (/CLR) ← /RST
U8-10..13    → NC
U8-14 (VCC)  → VCC
```

### U9 74HC574 — Accumulator

```
U9-1  (/OE) → GND
U9-2  (D1)  ← U17-4 (Y0)     U9-3  (D2)  ← U17-7 (Y1)
U9-4  (D3)  ← U17-9 (Y2)     U9-5  (D4)  ← U17-12 (Y3)
U9-6  (D5)  ← U18-4 (Y4)     U9-7  (D6)  ← U18-7 (Y5)
U9-8  (D7)  ← U18-9 (Y6)     U9-9  (D8)  ← U18-12 (Y7)
U9-10 (GND) → GND
U9-11 (CLK) ← ACC_CLK (U27-11)
U9-12 (Q8)  → AC7 → U11-12, U20-13, U14-9, U22-18
U9-13 (Q7)  → AC6 → U11-14, U20-10, U14-8, U22-16
U9-14 (Q6)  → AC5 → U11-3, U20-6, U14-7, U22-14
U9-15 (Q5)  → AC4 → U11-5, U20-3, U14-6, U22-12
U9-16 (Q4)  → AC3 → U10-12, U19-13, U14-5, U22-8
U9-17 (Q3)  → AC2 → U10-14, U19-10, U14-4, U22-6
U9-18 (Q2)  → AC1 → U10-3, U19-6, U14-3, U22-4
U9-19 (Q1)  → AC0 → U10-5, U19-3, U14-2, U22-2
U9-20 (VCC) → VCC
```

### U10-U11 74HC283 — ALU Adder

```
U10: bits 0-3
U10-5 (A0) ← AC0    U10-6 (B0) ← XOR_Y0 (U12-3)
U10-3 (A1) ← AC1    U10-2 (B1) ← XOR_Y1 (U12-6)
U10-14(A2) ← AC2    U10-15(B2) ← XOR_Y2 (U12-8)
U10-12(A3) ← AC3    U10-11(B3) ← XOR_Y3 (U12-11)
U10-7 (Cin) ← ALU_SUB (U5-12)
U10-4 (S0) → SUM0 → U17-2     U10-1 (S1) → SUM1 → U17-5
U10-13(S2) → SUM2 → U17-11    U10-10(S3) → SUM3 → U17-14
U10-9 (Cout) → U11-7
U10-8 (GND) → GND   U10-16(VCC) → VCC

U11: bits 4-7
U11-5 (A0) ← AC4    U11-6 (B0) ← XOR_Y4 (U13-3)
U11-3 (A1) ← AC5    U11-2 (B1) ← XOR_Y5 (U13-6)
U11-14(A2) ← AC6    U11-15(B2) ← XOR_Y6 (U13-8)
U11-12(A3) ← AC7    U11-11(B3) ← XOR_Y7 (U13-11)
U11-7 (Cin) ← U10-9 (Cout)
U11-4 (S0) → SUM4 → U18-2     U11-1 (S1) → SUM5 → U18-5
U11-13(S2) → SUM6 → U18-11    U11-10(S3) → SUM7 → U18-14
U11-9 (Cout) → NC
U11-8 (GND) → GND   U11-16(VCC) → VCC
```

### U12-U13 74HC86 — XOR Array

```
U12: bits 0-3 (A=IBUS, B=mux output)
U12-1 (A1) ← IBUS0  U12-2 (B1) ← U19-4    U12-3 (Y1) → XOR_Y0 → U10-6, U17-3
U12-4 (A2) ← IBUS1  U12-5 (B2) ← U19-7    U12-6 (Y2) → XOR_Y1 → U10-2, U17-6
U12-9 (A3) ← IBUS2  U12-10(B3) ← U19-9    U12-8 (Y3) → XOR_Y2 → U10-15, U17-10
U12-12(A4) ← IBUS3  U12-13(B4) ← U19-12   U12-11(Y4) → XOR_Y3 → U10-11, U17-13
U12-7 (GND) → GND   U12-14(VCC) → VCC

U13: bits 4-7
U13-1 (A1) ← IBUS4  U13-2 (B1) ← U20-4    U13-3 (Y1) → XOR_Y4 → U11-6, U18-3
U13-4 (A2) ← IBUS5  U13-5 (B2) ← U20-7    U13-6 (Y2) → XOR_Y5 → U11-2, U18-6
U13-9 (A3) ← IBUS6  U13-10(B3) ← U20-9    U13-8 (Y3) → XOR_Y6 → U11-15, U18-10
U13-12(A4) ← IBUS7  U13-13(B4) ← U20-12   U13-11(Y4) → XOR_Y7 → U11-11, U18-13
U13-7 (GND) → GND   U13-14(VCC) → VCC
```

### U14 74HC541 — AC Output Buffer

```
U14-1 (/OE1) ← /AC_BUF (U26-8)
U14-2  (A1) ← AC0    U14-18 (Y1) → IBUS0
U14-3  (A2) ← AC1    U14-17 (Y2) → IBUS1
U14-4  (A3) ← AC2    U14-16 (Y3) → IBUS2
U14-5  (A4) ← AC3    U14-15 (Y4) → IBUS3
U14-6  (A5) ← AC4    U14-14 (Y5) → IBUS4
U14-7  (A6) ← AC5    U14-13 (Y6) → IBUS5
U14-8  (A7) ← AC6    U14-12 (Y7) → IBUS6
U14-9  (A8) ← AC7    U14-11 (Y8) → IBUS7
U14-10 (GND) → GND
U14-19 (/OE2) ← /AC_BUF (U26-8)
U14-20 (VCC) → VCC
```

### U15-U16 74HC157 — Address Mux A[7:0] (PC vs IRL)

```
SEL=0: IRL, SEL=1: PC

U15-1 (SEL) ← /ADDR_MODE (U26-6)    U15-15(/E) → GND
U15-2 (1A) ← IRL0  U15-3 (1B) ← PC0    U15-4 (1Y) → ABUS0
U15-5 (2A) ← IRL1  U15-6 (2B) ← PC1    U15-7 (2Y) → ABUS1
U15-11(3A) ← IRL2  U15-10(3B) ← PC2    U15-9 (3Y) → ABUS2
U15-14(4A) ← IRL3  U15-13(4B) ← PC3    U15-12(4Y) → ABUS3
U15-8 (GND) → GND  U15-16(VCC) → VCC

U16-1 (SEL) ← /ADDR_MODE             U16-15(/E) → GND
U16-2 (1A) ← IRL4  U16-3 (1B) ← PC4    U16-4 (1Y) → ABUS4
U16-5 (2A) ← IRL5  U16-6 (2B) ← PC5    U16-7 (2Y) → ABUS5
U16-11(3A) ← IRL6  U16-10(3B) ← PC6    U16-9 (3Y) → ABUS6
U16-14(4A) ← IRL7  U16-13(4B) ← PC7    U16-12(4Y) → ABUS7
U16-8 (GND) → GND  U16-16(VCC) → VCC
```

### U17-U18 74HC157 — AC Input Mux (Adder vs XOR)

```
SEL=0: Adder SUM, SEL=1: XOR output

U17-1 (SEL) ← MUX_SEL (U5-14)      U17-15(/E) → GND
U17-2 (1A) ← SUM0   U17-3 (1B) ← XOR_Y0   U17-4 (1Y) → U9-2
U17-5 (2A) ← SUM1   U17-6 (2B) ← XOR_Y1   U17-7 (2Y) → U9-3
U17-11(3A) ← SUM2   U17-10(3B) ← XOR_Y2   U17-9 (3Y) → U9-4
U17-14(4A) ← SUM3   U17-13(4B) ← XOR_Y3   U17-12(4Y) → U9-5
U17-8 (GND) → GND   U17-16(VCC) → VCC

U18-1 (SEL) ← MUX_SEL (U5-14)      U18-15(/E) → GND
U18-2 (1A) ← SUM4   U18-3 (1B) ← XOR_Y4   U18-4 (1Y) → U9-6
U18-5 (2A) ← SUM5   U18-6 (2B) ← XOR_Y5   U18-7 (2Y) → U9-7
U18-11(3A) ← SUM6   U18-10(3B) ← XOR_Y6   U18-9 (3Y) → U9-8
U18-14(4A) ← SUM7   U18-13(4B) ← XOR_Y7   U18-12(4Y) → U9-9
U18-8 (GND) → GND   U18-16(VCC) → VCC
```

### U19-U20 74HC157 — XOR B-Input Mux (SUB vs AC)

```
SEL=0: ALU_SUB (for ADD/SUB), SEL=1: AC bits (for XOR instr)

U19-1 (SEL) ← XOR_MODE (U5-13)     U19-15(/E) → GND
U19-2 (1A) ← SUB   U19-3 (1B) ← AC0   U19-4 (1Y) → U12-2
U19-5 (2A) ← SUB   U19-6 (2B) ← AC1   U19-7 (2Y) → U12-5
U19-11(3A) ← SUB   U19-10(3B) ← AC2   U19-9 (3Y) → U12-10
U19-14(4A) ← SUB   U19-13(4B) ← AC3   U19-12(4Y) → U12-13
U19-8 (GND) → GND  U19-16(VCC) → VCC

U20-1 (SEL) ← XOR_MODE (U5-13)     U20-15(/E) → GND
U20-2 (1A) ← SUB   U20-3 (1B) ← AC4   U20-4 (1Y) → U13-2
U20-5 (2A) ← SUB   U20-6 (2B) ← AC5   U20-7 (2Y) → U13-5
U20-11(3A) ← SUB   U20-10(3B) ← AC6   U20-9 (3Y) → U13-10
U20-14(4A) ← SUB   U20-13(4B) ← AC7   U20-12(4Y) → U13-13
U20-8 (GND) → GND  U20-16(VCC) → VCC
```

### U21 74HC74 — Z Flag

```
U21-1 (/CLR1) → VCC
U21-2 (D1)    → GND
U21-3 (CLK1)  ← ACC_CLK (U27-11)
U21-4 (/PR1)  ← U22-19 (/P=Q)
U21-5 (Q1)    → Z_flag → U28-1
U21-6 (/Q1)   → NC
U21-7 (GND)   → GND
U21-8 (/Q2)   → NC
U21-9 (Q2)    → NC
U21-10(/PR2)  → VCC
U21-11(CLK2)  → GND
U21-12(D2)    → GND
U21-13(/CLR2) → VCC
U21-14(VCC)   → VCC
```

> 📌 **Z flag uses async preset** — U22 /P=Q drives U21 /PR.
> Place U21 and U22 physically adjacent on breadboard (minimize wire delay).
> Works reliably at 1 MHz. For PCB v2.0: consider synchronous Z update.

### U22 74HC688 — Zero Detect

```
U22-1 (/OE) → GND
U22-2 (P0) ← AC0   U22-3 (Q0) → GND
U22-4 (P1) ← AC1   U22-5 (Q1) → GND
U22-6 (P2) ← AC2   U22-7 (Q2) → GND
U22-8 (P3) ← AC3   U22-9 (Q3) → GND
U22-10(GND) → GND
U22-11(Q4) → GND   U22-12(P4) ← AC4
U22-13(Q5) → GND   U22-14(P5) ← AC5
U22-15(Q6) → GND   U22-16(P6) ← AC6
U22-17(Q7) → GND   U22-18(P7) ← AC7
U22-19(/P=Q) → U21-4
U22-20(VCC) → VCC
```

### U23 74HC574 — Page Register

> 📌 **74HC574 = positive-edge triggered.** U23/U32 latch data on CLK **rising edge** (LOW→HIGH).
> Do NOT treat CLK as active-low enable. PG_CLK and DP_Load must provide a clean LOW→HIGH transition.

**PG_CLK timing (SETPG instruction):**
```
         T0       T1       T2       T0 (next)
CLK   __|‾‾|__|‾‾|__|‾‾|__|‾‾|__
T2    ____________|‾‾‾‾‾‾|________
PG_cond __________| HIGH |________   (MUX_SEL=1 AND /AC_WR=1)
/T2   ‾‾‾‾‾‾‾‾‾‾‾‾|_____|‾‾‾‾‾‾‾
/PG_cond ‾‾‾‾‾‾‾‾‾‾|_____|‾‾‾‾‾‾‾
PG_CLK ‾‾‾‾‾‾‾‾‾‾‾‾|_____|‾‾‾‾‾‾‾   = /T2 OR /PG_cond
                           ↑
                     RISING EDGE = U23 latches IBUS!
```
PG_CLK = HIGH normally. Goes LOW only during T2 of SETPG. Returns HIGH at T2→T0 transition = latch point.

PG_CLK truth table:

| T2 | PG_cond (MUX & /AC_WR) | /T2 | /PG_cond | PG_CLK (/T2 OR /PG_cond) | Edge? |
|:--:|:----------------------:|:---:|:--------:|:------------------------:|:-----:|
| 0 | X | 1 | X | 1 | — |
| 1 | 0 | 0 | 1 | 1 | — |
| 1 | 1 (SETPG!) | 0 | 0 | **0** | — |
| 0 (T2 ends) | 1→0 | 1 | 0→1 | **1** | **↑ LATCH!** |

```
U23-1 (/OE) → GND
U23-2 (D1) ← IBUS0   U23-3 (D2) ← IBUS1
U23-4 (D3) ← IBUS2   U23-5 (D4) ← IBUS3
U23-6 (D5) ← IBUS4   U23-7 (D6) ← IBUS5
U23-8 (D7) ← IBUS6   U23-9 (D8) ← IBUS7
U23-10(GND) → GND
U23-11(CLK) ← PG_CLK (U25-11)
U23-12(Q8) → PG7 → U4-6     U23-13(Q7) → PG6 → U4-5
U23-14(Q6) → PG5 → U4-4     U23-15(Q5) → PG4 → U4-3
U23-16(Q4) → PG3 → U3-6     U23-17(Q3) → PG2 → U3-5
U23-18(Q2) → PG1 → U3-4     U23-19(Q1) → PG0 → U3-3
U23-20(VCC) → VCC
```

### U24 74HC04 — Inverters

```
U24-1 (1A) ← T0 (U8-3)         U24-2 (1Y) → NOT(Q0) → U8-1
U24-3 (2A) ← T1 (U8-4)         U24-4 (2Y) → NOT(Q1) → U8-2
U24-5 (3A) ← ABUS15            U24-6 (3Y) → /A15 → RAM /CE
U24-7 (GND) → GND
U24-9 (4A) ← JUMP (U5-19)      U24-8 (4Y) → /JUMP → U27-4
U24-11(5A) ← AC_WR (U5-15)     U24-10(5Y) → /AC_WR → U27-10
U24-13(6A) ← /IRL_OE (U26-3)   U24-12(6Y) → BUF_OE_N → U7-19
U24-14(VCC) → VCC
```

### U25 74HC32 — OR Gates

```
U25-1 (1A) ← SRC (U5-16)   U25-2 (1B) ← STR (U5-17)   U25-3 (1Y) → ADDR_REQ
U25-4 (2A) ← T0 (U8-3)     U25-5 (2B) ← T1 (U8-4)     U25-6 (2Y) → PC_INC
U25-7 (GND) → GND
U25 gate 3 spare: tie U25-9 and U25-10 to GND; U25-8 → NC
U25-12(4A) ← /T2 (U28-6)   U25-13(4B) ← /PG_cond(U27-8) U25-11(4Y) → PG_CLK → U23-11
U25-14(VCC) → VCC
```

### U26 74HC00 — NAND #1

```
Gate A: /IRL_OE = NAND(T2, /ADDR_MODE)
U26-1 ← T2 (U8-5)   U26-2 ← /ADDR_MODE (U26-6)   U26-3 → /IRL_OE → U34-1/19, U24-13

Gate B: /ADDR_MODE = NAND(ADDR_REQ, T2)
U26-4 ← ADDR_REQ (U25-3)   U26-5 ← T2 (U8-5)   U26-6 → /ADDR_MODE → U15/16/29/30-1, U26-2, U33-4

Gate C: /AC_BUF = NAND(T2, STORE)
U26-9 ← T2 (U8-5)   U26-10 ← STR (U5-17)   U26-8 → /AC_BUF → U14-1/19, RAM /WE, U28-9

Gate D: /PC_LD = NAND(T2, PC_LOAD_COND)
U26-12 ← T2 (U8-5)   U26-13 ← PC_LOAD_COND (U27-6)   U26-11 → /PC_LD → U1-9..U4-9

U26-7 (GND) → GND   U26-14(VCC) → VCC
```

### U27 74HC00 — NAND #2

```
Gate A: /BR_TAKEN = NAND(BRANCH, Z_match)
U27-1 ← BR (U5-18)   U27-2 ← Z_match (U28-3)   U27-3 → /BR_TAKEN → U27-5

Gate B: PC_LOAD_COND = NAND(/JUMP, /BR_TAKEN) = JUMP OR BR_TAKEN
U27-4 ← /JUMP (U24-8)   U27-5 ← /BR_TAKEN (U27-3)   U27-6 → PC_LOAD_COND → U26-13

Gate C: /PG_cond = NAND(MUX_SEL, /AC_WR)
U27-9 ← MUX (U5-14)   U27-10 ← /AC_WR (U24-10)   U27-8 → /PG_cond → U25-12

Gate D: ACC_CLK = NAND(T2, AC_WR)
U27-12 ← T2 (U8-5)   U27-13 ← AC_WR (U5-15)   U27-11 → ACC_CLK → U9-11, U21-3

U27-7 (GND) → GND   U27-14(VCC) → VCC
```

### U28 74HC86 — XOR (Misc)

```
Gate A: Z_match = Z_flag XOR ALU_SUB
U28-1 ← Z_flag (U21-5)   U28-2 ← SUB (U5-12)   U28-3 → Z_match → U27-2

Gate B: /T2 = T2 XOR 1 = NOT(T2)
U28-4 ← T2 (U8-5)   U28-5 → VCC   U28-6 → /T2 → U25-11

Gate C: WR_DIR = /AC_BUF XOR 1 = NOT(/AC_BUF)
U28-9 ← /AC_BUF (U26-8)   U28-10 → VCC   U28-8 → WR_DIR → U7-1, ROM /OE

Gate D: /XOR_MODE = XOR_MODE XOR 1 = NOT(XOR_MODE)
U28-12 ← XOR_MODE (U5-13)   U28-13 ← VCC   U28-11 → /XOR_MODE → U33-12

U28-7 (GND) → GND   U28-14(VCC) → VCC
```

### U29-U30 74HC157 — Address Mux A[15:8] (PC high vs Data Page)

```
SEL=0: Data Page Register (U32 Q outputs), SEL=1: PC high

U29-1 (SEL) ← /ADDR_MODE        U29-15(/E) → GND
U29-2 (1A) ← DP0    U29-3 (1B) ← PC8    U29-4 (1Y) → ABUS8
U29-5 (2A) ← DP1    U29-6 (2B) ← PC9    U29-7 (2Y) → ABUS9
U29-11(3A) ← DP2    U29-10(3B) ← PC10   U29-9 (3Y) → ABUS10
U29-14(4A) ← DP3    U29-13(4B) ← PC11   U29-12(4Y) → ABUS11
U29-8 (GND) → GND   U29-16(VCC) → VCC

U30-1 (SEL) ← /ADDR_MODE        U30-15(/E) → GND
U30-2 (1A) ← DP4    U30-3 (1B) ← PC12   U30-4 (1Y) → ABUS12
U30-5 (2A) ← DP5    U30-6 (2B) ← PC13   U30-7 (2Y) → ABUS13
U30-11(3A) ← DP6    U30-10(3B) ← PC14   U30-9 (3Y) → ABUS14
U30-14(4A) ← DP7    U30-13(4B) ← PC15   U30-12(4Y) → ABUS15 → ROM /CE, U24-5, RV8_A15
U30-8 (GND) → GND   U30-16(VCC) → VCC
```

### U31 74HC74 — IRQ Latch + IE Flag (v1.0 Polling)

```
FF-A: IE flag (Interrupt Enable)
U31-1 (/CLR1) ← /RST (clear on reset → IE=0 at boot)
U31-2 (D1)    → VCC (D=1 always)
U31-3 (CLK1)  ← EI_decode (U33-8, rising edge sets IE=1)
U31-4 (/PR1)  → VCC
U31-5 (Q1)    → IE flag → LED
U31-6 (/Q1)   → NC

FF-B: IRQ latch
U31-7 (GND)   → GND
U31-8 (/Q2)   → NC
U31-9 (Q2)    → IRQ_FF → LED/test point; optional external /SLOT device may expose it to software
U31-10(/PR2)  → VCC
U31-11(CLK2)  ← /IRQ (external, active-low from peripheral)
U31-12(D2)    → VCC (D=1 always)
U31-13(/CLR2) ← /RST (clear on reset)
U31-14(VCC)   → VCC
```

> 📌 **IRQ latches on /IRQ rising edge** (device releases line).
> v1.0 uses level-triggered protocol: device holds /IRQ LOW until software acknowledges.
> For edge-detect: add inverter on /IRQ input (future option).

### v1.0 IRQ Operation: Software Polling

```
1. External device pulls /IRQ LOW, then releases it HIGH → IRQ_FF = 1 on the rising edge
2. Main loop reads IRQ_FF only if an external /SLOT status device exposes it
3. If IRQ_FF=1 AND IE=1: branch to handler subroutine
4. Handler processes event (IRQ_FF remains set until /RST in v1.0)
5. Software ignores further events unless it intentionally calls `EI` again

No hardware vector. No PC forcing. No bus override.
No IRQ_ack gate needed. No extra chips beyond U31+U33.
v1.0: IRQ_FF cleared only by /RST. Hardware vector/ack is not part of v1.0.
```

### Future Upgrade: Hardware Vector $FF00 (not frozen)

```
Do not build this from the v1.0 wiring guide.

Required functions:
- PC input mux: normal {PG,IRL} vs vector constant $FF00
- /PC_LD assertion during IRQ acknowledge
- Safe IRQ_ack generation: T2 AND IE AND IRQ_FF AND NOT(PC_LOAD_COND)
- Active-low clear generation for U31 if auto-clear is kept
- Timing review for conflicts with branch/jump and reset
```

> 📌 **$FF00 is in RAM** — a future hardware vector may jump here.
> Must load ISR code before enabling hardware interrupts:
> `SETDP $FF` → write ISR via SB → `SETDP $80` → enable.
> v1.0 (polling) does not jump to $FF00 automatically.

### EI Decode (v1.0)

```
EI opcode = $08 = 00001000 (SRC=1, XOR=0, AC_WR=0)

EI_decode: U33 gate 2 (74HC21, 4-input AND)
  U33-9  ← T2 (U8-5)
  U33-10 ← SRC (U5-16)
  U33-12 ← /XOR_MODE (U28-11)
  U33-13 ← /AC_WR (U24-10)
  U33-8  → EI_decode → U31-3 (CLK1, rising edge sets IE=1)

IE_D:
  U31-2 (D1) ← VCC

Decode safety check (only $08 clocks IE):
  $08: SRC=1, XOR=0, AC_WR=0 → T2 & 1 & 1 & 1 = 1 ✅
  $18: SRC=1, XOR=0, AC_WR=1 → /AC_WR=0 → blocked ✅
  $38: SRC=1, XOR=0, AC_WR=1 → /AC_WR=0 → blocked ✅
  $48: SRC=1, XOR=1, AC_WR=0 → /XOR=0 → blocked ✅
  $78: SRC=1, XOR=1, AC_WR=1 → both blocked ✅

DI ($48) has no v1.0 hardware effect. IE clears only via `/RST`.
```

---

### U32 74HC574 — Data Page Register

```
U32-1 (/OE) → GND
U32-2 (D1) ← IBUS0   U32-3 (D2) ← IBUS1
U32-4 (D3) ← IBUS2   U32-5 (D4) ← IBUS3
U32-6 (D5) ← IBUS4   U32-7 (D6) ← IBUS5
U32-8 (D7) ← IBUS6   U32-9 (D8) ← IBUS7
U32-10(GND) → GND
U32-11(CLK) ← DP_Load (decode: T2 AND SETDP)
U32-12(Q8) → DP7 → U30-14 (ABUS15 A-input: when DP7=1, ABUS15=1 → selects RAM)
U32-13(Q7) → DP6 → U30-11 (ABUS14 A-input)
U32-14(Q6) → DP5 → U30-5 (ABUS13 A-input)
U32-15(Q5) → DP4 → U30-2 (ABUS12 A-input)
U32-16(Q4) → DP3 → U29-14 (ABUS11 A-input)
U32-17(Q3) → DP2 → U29-11 (ABUS10 A-input)
U32-18(Q2) → DP1 → U29-5 (ABUS9 A-input)
U32-19(Q1) → DP0 → U29-2 (ABUS8 A-input)
U32-20(VCC) → VCC
```

### U33 74HC21 — SETDP Decode (dual 4-input AND)

```
U33-1  (1A) ← T2 (U8-5)
U33-2  (1B) ← XOR_MODE (U5-13)
U33-3  (NC)
U33-4  (1C) ← /ADDR_MODE (U26-6)
U33-5  (1D) ← /AC_WR (U24-10)
U33-6  (1Y) → DP_Load → U32-11
U33-7  (GND) → GND
U33-8  (2Y) → EI_decode → U31-3
U33-9  (2A) ← T2 (U8-5)
U33-10 (2B) ← SRC (U5-16)
U33-11 (NC)
U33-12 (2C) ← /XOR_MODE (U28-11)
U33-13 (2D) ← /AC_WR (U24-10)
U33-14 (VCC) → VCC
```

Decode verification:
| Opcode | T2 | XOR | /ADDR | /AC_WR | DP_Load |
|:------:|:--:|:---:|:-----:|:------:|:-------:|
| SETDP $40 | 1 | 1 | 1 | 1 | **1** ✓ |
| DI $48 | 1 | 1 | 0 | 1 | 0 ✓ |
| XORI $70 | 1 | 1 | 1 | 0 | 0 ✓ |
| SETPG $20 | 1 | 0 | 1 | 1 | 0 ✓ |
| $C0 (SUB+XOR) | 1 | 1 | 1 | 1 | **1** (= SETDP alias, harmless) |

Note: $C0 triggers DP_Load but is equivalent to SETDP (SUB bit has no effect when AC_WR=0).

---

## ROM & RAM

```
ROM (AT28C256 / SST39SF010A)
  A[0:7]  ← ABUS0..ABUS7
  A[8:14] ← ABUS8..ABUS14
  D[0:7]  → DBUS0..DBUS7
  /CE     ← ABUS15
  /OE     ← WR_DIR (U28-8; disables ROM output during CPU store)
  /WE     ← /WR (RV8-Bus pin 27, from Programmer board only)

Note: Bus pin 27 (/WR) is driven by /AC_BUF during CPU STORE operations.
ROM sees /WE pulse when SETDP<$80 + SB, but AT28C256 has built-in software data
protection (SDP) — single pulses without unlock sequence are ignored.
The current Programmer firmware performs normal byte write cycles while /RST=LOW
and the CPU is stopped. Use an AT28C256 with SDP disabled, or add/enable an SDP
unlock sequence in Programmer firmware before relying on protected chips.
SETDP <$80 + LB = read from ROM (lookup tables, safe).

RAM (62256)
  A[0:7]  ← ABUS0..ABUS7
  A[8:14] ← ABUS8..ABUS14
  D[0:7]  ←→ DBUS0..DBUS7
  /CE     ← /A15 (U24-6)
  /OE     → GND (output always enabled when /CE active)
  /WE     ← /AC_BUF (U26-8)
```

> 📌 **RAM output permanently enabled** — relies on mutually-exclusive chip selects.
> ABUS15=0 → ROM /CE=LOW (ROM drives DBUS). ABUS15=1 → RAM /CE=LOW (RAM drives DBUS).
> No bus fight possible as long as A15 decode is correct.
> During STORE: RAM /WE=LOW disables output drivers automatically (62256 datasheet).

---

## Control Signal Summary

| Signal | Source | Destinations | Active |
|--------|--------|-------------|:------:|
| CLK | Oscillator | U1-2, U2-2, U3-2, U4-2, U8-8 | ↑edge |
| /RST | RC+button | U1-1, U2-1, U3-1, U4-1, U8-9, U31-1, U31-13 | LOW |
| T0 | U8-3 | U5-11, U25-4, U24-1 | HIGH |
| T1 | U8-4 | U6-11, U25-5, U24-3 | HIGH |
| T2 | U8-5 | U26-1, U26-9, U26-12, U27-12, U28-4, U33-1, U33-9 | HIGH |
| ALU_SUB | U5-12 | U10-7, U19-2/5/11/14, U20-2/5/11/14, U28-2 | HIGH |
| XOR_MODE | U5-13 | U19-1, U20-1, U33-2, U28-12 | HIGH |
| MUX_SEL | U5-14 | U17-1, U18-1, U27-9 | HIGH |
| AC_WR | U5-15 | U24-11, U27-13 | HIGH |
| SRC | U5-16 | U25-1, U33-10 | HIGH |
| STR | U5-17 | U25-2, U26-10 | HIGH |
| BR | U5-18 | U27-1 | HIGH |
| JMP | U5-19 | U24-9 | HIGH |
| ADDR_REQ | U25-3 | U26-4 | HIGH when SRC or STR |
| /ADDR_MODE | U26-6 | U15-1, U16-1, U29-1, U30-1, U26-2, U33-4 | LOW selects data address |
| PC_INC | U25-6 | U1-7/10, U2-7, U3-7, U4-7 | HIGH |
| /PC_LD | U26-11 | U1-9, U2-9, U3-9, U4-9 | LOW |
| /AC_BUF | U26-8 | U14-1/19, RAM /WE, U28-9 | LOW |
| ACC_CLK | U27-11 | U9-11, U21-3 | ↑edge |
| BUF_OE_N | U24-12 | U7-19 | LOW enables U7 |
| WR_DIR | U28-8 | U7-1, ROM /OE | HIGH=write and ROM output disabled |
| A15 | U30-12 | ROM /CE, U24-5 | — |
| PG_CLK | U25-11 | U23-11 | ↑edge |
| DP_Load | U33-6 | U32-11 | ↑edge |
| EI_decode | U33-8 | U31-3 | ↑edge |

---

## Power

| Package | VCC | GND | Bypass |
|---------|:---:|:---:|:------:|
| 74HC161 (U1-U4) | 16 | 8 | 100nF |
| 74HC574 (U5,U6,U9,U23,U32) | 20 | 10 | 100nF |
| 74HC21 (U33) | 14 | 7 | 100nF |
| 74HC245 (U7) | 20 | 10 | 100nF |
| 74HC164 (U8) | 14 | 7 | 100nF |
| 74HC283 (U10-U11) | 16 | 8 | 100nF |
| 74HC86 (U12,U13,U28) | 14 | 7 | 100nF |
| 74HC541 (U14,U34) | 20 | 10 | 100nF |
| 74HC157 (U15-U20,U29-U30) | 16 | 8 | 100nF |
| 74HC74 (U21,U31) | 14 | 7 | 100nF |
| 74HC688 (U22) | 20 | 10 | 100nF |
| 74HC04 (U24) | 14 | 7 | 100nF |
| 74HC32 (U25) | 14 | 7 | 100nF |
| 74HC00 (U26-U27) | 14 | 7 | 100nF |

---

## Forbidden Bus States

The following states must NEVER occur — they cause electrical bus contention:

| Bus | Conflict | Prevention |
|-----|----------|-----------|
| IBUS | U34 + U14 driving simultaneously | /IRL_OE and /AC_BUF mutually exclusive (NAND gates) |
| IBUS | U7 + U14 driving simultaneously | Not a conflict in store: U14 drives IBUS, U7 is DIR=write and drives DBUS |
| IBUS | U34 + U7 driving simultaneously | /IRL_OE=0 only when /ADDR_MODE=1 (immediate); U7 enabled during fetch/load when U34 is disabled |
| DBUS | ROM + U7(write) simultaneously | ROM /OE=WR_DIR disables ROM output during CPU store |
| DBUS | RAM + U7(write) simultaneously | RAM /WE=0 disables RAM output automatically |
| chip select | ROM + RAM both /CE=0 | Impossible: ROM /CE=A15, RAM /CE=/A15 (complementary) |

If any of these occur during debug → check /ADDR_MODE, BUF_OE_N, WR_DIR, or ABUS15 decode.

---

## Revision History

| Version | Date | Changes |
|:-------:|:----:|---------|
| v1.0 | 2026-06-15 | Initial freeze. 34 logic + ROM + RAM. 18 instructions. 1 MHz target. Software polling IRQ. |
| v1.1 | (reserved) | Optional software IRQ_FF clear via I/O, if wanted |
| v2.0 | (future) | Hardware vector/save-PC/RTI after full logic design |

---

## Appendix A: IRQ Hardware Vector (v2.0 — FUTURE)

> **NOT part of v1.0 build.** Requires +2-3 chips beyond the 36-package design.

### Hardware Save-PC (v2.0 concept)

During IRQ-ack, a v2.0 CPU would:
1. Write PC[7:0] to RAM[$800E]
2. Write PC[15:8] to RAM[$800F]
3. Force PC = $FF00

```
Cycle 1 — Save PC low:
  Force /ADDR_MODE=0, address=$0E, DP=$80
  Force AC buffer to drive PC[7:0] onto IBUS (override U14 input)
  RAM /WE pulse → RAM[$800E] = PC[7:0]

Cycle 2 — Save PC high:
  Force address=$0F, DP=$80
  Drive PC[15:8] onto IBUS
  RAM /WE pulse → RAM[$800F] = PC[15:8]
```

**Required chips**: 74HC157 ×2 (PC mux) + additional state logic.
Not included in v1.0 BOM.

---

## Appendix B: Canonical Opcode → Control Bits Table

| Hex | Mnemonic | SUB | XOR | MUX | AC_WR | SRC | STR | BR | JMP |
|:---:|----------|:---:|:---:|:---:|:-----:|:---:|:---:|:--:|:---:|
| $00 | NOP      | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| $01 | J        | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| $02 | BEQ      | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| $04 | SB       | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| $08 | EI       | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| $10 | ADDI     | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| $18 | ADD      | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| $20 | SETPG    | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| $28 | SETPG_R  | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 |
| $30 | LI       | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| $38 | LB       | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 |
| $40 | SETDP    | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| $48 | DI       | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| $70 | XORI     | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| $78 | XOR      | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| $82 | BNE      | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| $90 | SUBI     | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| $98 | SUB      | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |

**Alias**: $C0 = SETDP (SUB bit ignored by U33 decode)

**Reserved**: Any opcode with SRC+STR both set (bit3+bit2 = 11) is store-dominant and electrically safe, but not part of the ISA.
Pattern: `(opcode & $0C) == $0C` → 64 reserved mixed opcodes.
