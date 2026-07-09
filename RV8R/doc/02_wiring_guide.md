{
// ═══════════════════════════════════════════════════════════════
// RV8-R CPU — WiringGuide (Bus-Centric, draft)
// FullHW revision: 49 logic chips + 4 ROM/RAM packages = 53 packages
// = RV8 minus hardware registers, registers live in RAM $FFF8-$FFFF
//
// RV8-style 35-slot programmer ISA surface
// Native/macro/prototype status is defined in doc/00_design.md
// Full ISA pin trace status: REAL HARDWARE PATHS DEFINED; RTL/KiCad proof pending
// Microcode address includes IRQ_ACTIVE + flags + step[3:0] + opcode
// Reset PC = $0000: Program ROM boots first, high RAM holds registers/data
// Fewer chips: no 8× register 574s, no 2× decode 138s
//
// TWO BUSES:
//   RV8-Bus (external 40-pin): A[15:0] + D[7:0] → ROM, RAM
//   IBUS (internal 8-bit): ALU, IR, result latch, bus buffer
// ═══════════════════════════════════════════════════════════════

Project: RV8-R,

RV8_Bus:{
    "A[15:0]": "PC (fetch) or address latches (register/memory access)",
    "D[7:0]":  "ROM/RAM ↔ U12 (245) ↔ IBUS",
    "/RD":     "from microcode",
    "/WR":     "from microcode",
    "/IRQ":    "external active-low interrupt request into U22 IRQ_PENDING latch",
    pinout:    "Same 40-pin as all RV8 variants"
},

IBUS:{
    width: 8,
    drivers: [
        "U2 (IR operand, /OE controlled)",
        "U12 (245 bus buffer, read mode)",
        "U15 (ALU result latch, /OE controlled)"
    ],
    consumers: [
        "U1 (IR opcode, CLK=IR_CLK)",
        "U2 (IR operand, CLK=OPR_CLK)",
        "U3 (ALU B latch, CLK=ALUB_CLK)",
        "U10 (addr latch low, CLK=ADDR_LO_CLK)",
        "U11 (addr latch high, CLK=ADDR_HI_CLK)",
        "U12 (245 bus buffer, write mode)",
        "U6-U7 (XOR → adder B inputs)"
    ],
    rule: "One driver at a time (microcode controls /OE and BUF_OE)"
},

Legacy_19Chip_Sketch_Do_Not_Build:{
    note:"Kept only to show the old low-chip idea. It does not meet the full ISA. Build from FullHW_Part below.",
    // ═══════════════════════════════════════════
    // IR — 74HC574 ×2 (U1-U2)
    // ═══════════════════════════════════════════

    U1:{type:74HC574, bus:IBUS, function:"IR opcode",
        1:GND, 11:IR_CLK, "2-9":IBUS, "12-19":"→Flash addr A[7:0]",
        10:GND, 20:VCC},
    // /OE=GND (always outputs to Flash address)

    U2:{type:74HC574, bus:IBUS, function:"IR operand (also drives IBUS for immediate)",
        1:OPR_OE, 11:OPR_CLK, "2-9":IBUS, "12-19":"IBUS + addr_mux(U18)",
        10:GND, 20:VCC},
    // /OE controlled by microcode (drives IBUS when loading ALU B with immediate)

    // ═══════════════════════════════════════════
    // ALU — 74HC574 + 74HC283 ×2 + 74HC86 ×2 + 74HC574 (U3-U7, U15)
    // ═══════════════════════════════════════════

    U3:{type:74HC574, bus:IBUS, function:"ALU B latch",
        1:VCC, 11:ALUB_CLK, "2-9":IBUS, "12-19":"→U6-U7 XOR A inputs",
        10:GND, 20:VCC},
    // /OE=VCC (never drives IBUS). Outputs → XOR chips.

    U4:{type:74HC283, bus:internal, function:"ALU adder low nibble",
        5:"IBUS0", 3:"IBUS1", 14:"IBUS2", 12:"IBUS3",
        6:"U6.Y0", 2:"U6.Y1", 15:"U6.Y2", 11:"U6.Y3",
        7:ALU_SUB, 9:"→U5.C0",
        4:"S0→U15.D0", 1:"S1→U15.D1", 13:"S2→U15.D2", 10:"S3→U15.D3",
        8:GND, 16:VCC},
    // A inputs from IBUS (register value from RAM during execute)
    // B inputs from XOR output (operand or register, inverted for SUB)

    U5:{type:74HC283, bus:internal, function:"ALU adder high nibble",
        5:"IBUS4", 3:"IBUS5", 14:"IBUS6", 12:"IBUS7",
        6:"U7.Y0", 2:"U7.Y1", 15:"U7.Y2", 11:"U7.Y3",
        7:"U4.C4", 9:"CARRY_OUT→U14.D2",
        4:"S4→U15.D4", 1:"S5→U15.D5", 13:"S6→U15.D6", 10:"S7→U15.D7",
        8:GND, 16:VCC},

    U6:{type:74HC86, bus:internal, function:"XOR low (SUB invert bits 0-3)",
        1:"U3.Q0", 2:ALU_SUB, 3:"→U4.B1",
        4:"U3.Q1", 5:ALU_SUB, 6:"→U4.B2",
        9:"U3.Q2", 10:ALU_SUB, 8:"→U4.B3",
        12:"U3.Q3", 13:ALU_SUB, 11:"→U4.B4",
        7:GND, 14:VCC},

    U7:{type:74HC86, bus:internal, function:"XOR high (SUB invert bits 4-7)",
        1:"U3.Q4", 2:ALU_SUB, 3:"→U5.B1",
        4:"U3.Q5", 5:ALU_SUB, 6:"→U5.B2",
        9:"U3.Q6", 10:ALU_SUB, 8:"→U5.B3",
        12:"U3.Q7", 13:ALU_SUB, 11:"→U5.B4",
        7:GND, 14:VCC},

    U15:{type:74HC574, bus:IBUS, function:"ALU result latch (drives IBUS for write-back)",
        1:ALUR_OE, 11:ALUR_CLK, "2-9":"adder S[7:0]", "12-19":IBUS,
        10:GND, 20:VCC},
    // /OE=ALUR_OE (drives IBUS when writing result to RAM)
    // CLK=ALUR_CLK (latches adder output)

    // ═══════════════════════════════════════════
    // PC — 74HC574 ×2 (U8-U9) — has /OE
    // ═══════════════════════════════════════════

    U8:{type:74HC574, bus:RV8_Bus_addr, function:"PC low (A[7:0] during fetch)",
        1:PC_ADDR_n, 11:PC_LO_CLK, "2-9":"ALU_R (from U15)", "12-19":"A[7:0]",
        10:GND, 20:VCC},
    // /OE=PC_ADDR_n (LOW during fetch, HIGH during data access)

    U9:{type:74HC574, bus:RV8_Bus_addr, function:"PC high (A[15:8] during fetch)",
        1:PC_ADDR_n, 11:PC_HI_CLK, "2-9":"ALU_R (from U15)", "12-19":"A[15:8]",
        10:GND, 20:VCC},

    // ═══════════════════════════════════════════
    // ADDRESS LATCHES — 74HC574 ×2 (U10-U11)
    // ═══════════════════════════════════════════

    U10:{type:74HC574, bus:RV8_Bus_addr, function:"Addr latch low (A[7:0] during data access)",
        1:PC_ADDR, 11:ADDR_LO_CLK,
        "2-4":"from U18 mux (normal addr bits or opcode[2:0])",
        "5-9":"from U18/force network (normal addr bits or VCC for $FFF8-$FFFF)",
        "12-19":"A[7:0]",
        10:GND, 20:VCC},
    // /OE=PC_ADDR (LOW during data access, HIGH during fetch)
    // D inputs from U18/force network: normal address or $F8+opcode[2:0] for register access

    U11:{type:74HC574, bus:RV8_Bus_addr, function:"Addr latch high (A[15:8] during data access)",
        1:PC_ADDR, 11:ADDR_HI_CLK, "2-9":"IBUS or $FF force in REG_ADDR_MODE", "12-19":"A[15:8]",
        10:GND, 20:VCC},

    // ═══════════════════════════════════════════
    // REGISTER ADDRESS MUX / FORCE NETWORK — 74HC157 (U18)
    // Selects normal memory address vs forced $FFF8+reg address
    // ═══════════════════════════════════════════

    U18:{type:74HC157, bus:internal, function:"Addr latch input mux/force (normal addr vs $FFF8+reg)",
        1:REG_ADDR_MODE,
        2:"IBUS0", 3:"U1.Q0 (opcode bit 0)", 4:"→U10.D0",
        5:"IBUS1", 6:"U1.Q1 (opcode bit 1)", 7:"→U10.D1",
        11:"IBUS2", 10:"U1.Q2 (opcode bit 2)", 9:"→U10.D2",
        14:"IBUS3", 13:VCC, 12:"→U10.D3",
        8:GND, 15:GND, 16:VCC},
    // S=REG_ADDR_MODE: 0=normal address, 1=register address $FFF8+opcode[2:0]
    // B inputs: opcode[2:0] for bits 0-2, VCC for bit 3. Remaining low-byte bits and high byte
    // must be forced high in REG_ADDR_MODE. This is the frozen concept; pin-level proof pending.

    // ═══════════════════════════════════════════
    // BUS BUFFER — 74HC245 (U12)
    // ═══════════════════════════════════════════

    U12:{type:74HC245, bus:both, function:"Bridge: IBUS ↔ RV8-Bus D[7:0]",
        1:BUF_DIR, 19:BUF_OE_n, "2-9":IBUS, "11-18":"D[7:0]",
        10:GND, 20:VCC},

    // ═══════════════════════════════════════════
    // CONTROL — Flash ×2 + step counter + flags + IRQ
    // ═══════════════════════════════════════════

    U13:{type:SST39SF010A, bus:control, function:"Microcode Flash #1 (low byte)",
        "addr":"IRQ_ACTIVE + flag_C + flag_Z + step[2:0] + opcode[7:0] = 14 bits",
        "data":"D[7:0] = BUF_OE, BUF_DIR, PC_ADDR, ADDR_CLK, PC_INC, IR_CLK, OPR_CLK, STEP_RST"},

    U17:{type:SST39SF010A, bus:control, function:"Microcode Flash #2 (high byte)",
        "addr":"same as U13",
        "data":"D[7:0] = REG_ADDR_MODE, ALUB_CLK, ALUR_CLK, ALUR_OE, ALU_SUB, FLAGS_CLK, PC_LOAD, ADDR_HI_CLK"},

    U14:{type:74HC74, bus:control, function:"Flags (Z, C)",
        "FF1":"D=alu_zero, CLK=FLAGS_CLK, Q=flag_z → Flash addr",
        "FF2":"D=carry_out, CLK=FLAGS_CLK, Q=flag_c → Flash addr",
        1:"/RST", 7:GND, 13:"/RST", 14:VCC},

    U22:{type:74HC74, bus:control, function:"Interrupt state (IE, IRQ_PENDING)",
        "FF1":"IE: set by SYS 2/EI, clear by SYS 3/DI or IRQ_ACK or /RST, Q=IE",
        "FF2":"IRQ_PENDING: clocked by falling /IRQ, clear by IRQ_ACK or /RST",
        "IRQ_ACTIVE":"IE AND IRQ_PENDING → Flash addr A13",
        "entry":"save PC to RAM[$FFF6/$FFF7], clear IE+IRQ_PENDING, PC=$7F00",
        1:"/RST", 7:GND, 13:"/RST", 14:VCC},

    U16:{type:74HC161, bus:control, function:"Step counter",
        2:CLK, 1:STEP_RST_n, "Q[2:0]":"→Flash addr A[10:8]",
        7:VCC, 10:VCC, 8:GND, 16:VCC},

    // ═══════════════════════════════════════════
    // MEMORY
    // ═══════════════════════════════════════════

    ROM:{type:AT28C256, bus:RV8_Bus, function:"Program ROM",
        "range":"$0000-$7FFF, first fetch after reset",
        "/CE":"A15 active-low select for lower 32KB", "/OE":"/RD", "/WE":VCC},
    RAM:{type:62256, bus:RV8_Bus, function:"RAM (registers $FFF8-$FFFF + data)",
        "range":"$8000-$FFFF, high RAM",
        "/CE":"NOT(A15) active-low select for upper 32KB", "/OE":"/RD", "/WE":"/WR"},

    // ═══════════════════════════════════════════
    // SUPPORT
    // ═══════════════════════════════════════════
    OSC:{type:"Crystal 5MHz", output:CLK},
    R1:{type:"10K", 1:VCC, 2:"/RST"},
    SW:{type:"Pushbutton", 1:"/RST", 2:GND},
    C1:{type:"100nF", 1:"/RST", 2:GND},

    RV8_Bus_connector:{type:"40-pin IDC", pinout:"Same as all RV8 variants"}
},

// ═══════════════════════════════════════════════════════════════
// FULLHW PART LIST — REAL FULL-ISA HARDWARE PATHS
// ═══════════════════════════════════════════════════════════════

FullHW_Part:{
    goal:"Make every RV8-R ISA feature a real TTL path, even if chip count rises.",
    package_count:{
        logic:49,
        memory:4,
        total:53,
        note:"2x AT28C256/SST39SF010 microcode ROM + 1x AT28C256 program ROM + 1x 62256 RAM are counted as memory/program packages."
    },

    buses:{
        IBUS:"internal 8-bit data bus: one active driver only",
        ABUS:"external 16-bit address bus to Program ROM and RAM",
        DBUS:"external 8-bit memory data bus",
        PCQ:"16-bit PC counter outputs",
        ARQ:"16-bit address register outputs",
        ALU_A:"IBUS direct into ALU A inputs",
        ALU_B:"U3 ALU_B latch outputs",
        ALU_R:"selected ALU result into U15"
    },

    pc_real:{
        U8_U11:"4x74HC161, 16-bit PC counter, Q=PCQ[15:0]",
        pins:"CLK=CPU_CLK, /CLR=/RST so reset PC=$0000, ENP/ENT=PC_INC, /LOAD=PC_LOAD_n, D[15:0]=ARQ[15:0]",
        fetch:"PCQ drives ABUS through U40-U43 when ADDR_OWNER=PC",
        branch_jump_irq_iret:"microcode first loads ARQ with target, then asserts PC_LOAD_n low for one clock",
        pc_to_ibus:"U44 drives PC_LO to IBUS, U45 drives PC_HI to IBUS for JAL and IRQ save"
    },

    address_real:{
        U20_U21:"2x74HC574 address registers, Q=ARQ[15:0]",
        U30_U37:"8x74HC157 two-stage address-source muxes feeding U20/U21 D[15:0]",
        source_00:"NORMAL: IBUS byte into selected low/high address register",
        source_01:"REG: $FFF8 + REG_SEL, where REG_SEL can be rd, rs, or r7",
        source_10:"FAST/IRQ: $FF00 + OPR for LBfp/SBfp, or $FFF6/$FFF7 for IRQ save/IRET",
        source_11:"VECTOR/CONST: $7F00 IRQ vector, $0000 reset/test, or PC_HI:ALU_LO for same-page relative branch",
        abus_select:"U40-U43 4x74HC157 select ABUS = PCQ or ARQ; no tri-state fight on address bus"
    },

    alu_real:{
        U3:"74HC574 ALU_B latch, D=IBUS, Q=ALU_B",
        U4_U5:"2x74HC283 adder, A=IBUS, B=ALU_B xor SUB, C0=ALU_CIN",
        U6_U7:"2x74HC86 B invert bank for SUB/SBC-style operations",
        U50_U51:"2x74HC08 AND result, Y=IBUS & ALU_B",
        U52_U53:"2x74HC32 OR result, Y=IBUS | ALU_B",
        U54_U55:"2x74HC86 XOR result, Y=IBUS ^ ALU_B",
        U56_U59:"4x74HC157 ALU result mux, selects ADD/SUB, AND, OR, XOR into U15.D[7:0]",
        U15:"74HC574 ALU result latch, Q drives IBUS only when ALUR_OE_n=0",
        constants:"U60 74HC244 drives $00 or $01 to IBUS for SLT/SLTI writeback and zero-B loads",
        sign_extend:"U61 74HC244 drives sext(OPR[4:0]) to IBUS for branch and off(rs) address math"
    },

    memory_real:{
        U12:"74HC245 bridge, IBUS <-> DBUS, BUF_DIR selects read/write, BUF_OE_n enables",
        ROM:"AT28C256 Program ROM, /CE=A15 active-low, /OE=/RD, /WE=VCC, range $0000-$7FFF",
        RAM:"62256 SRAM, /CE=NOT(A15) active-low, /OE=/RD, /WE=/WR, range $8000-$FFFF",
        fast_page:"LBfp/SBfp force address $FF00+OPR; $FFF6-$FFFF reserved by software and control tests",
        registers:"REG address source forces $FFF8+reg for r0-r7",
        r0_guard:"U62 gates RAM_WE off when REG_WRITE and REG_SEL=000"
    },

    control_real:{
        U13_U17:"2x AT28C256/SST39SF010 microcode ROMs, 16-bit direct control word",
        microcode_address:"{IRQ_ACTIVE, flag_C, flag_Z, step[3:0], opcode[7:0]} = 15 bits, exactly fills 32KB",
        frozen_control_word:{
            default_safe:"0x028D",
            "bit0":"BUF_OE_n, active low, enables U12",
            "bit1":"BUF_DIR, 0=DBUS to IBUS read, 1=IBUS to DBUS write",
            "bit2":"OPR_OE_n, active low, enables U2 operand onto IBUS",
            "bit3":"ALUR_OE_n, active low, enables U15 ALU result onto IBUS",
            "bit4":"ALUB_CLK, active high clock, loads U3 from IBUS",
            "bit5":"ALUR_CLK, active high clock, loads U15 from selected ALU result",
            "bit6":"FLAGS_CLK, active high clock, loads Z/C flags",
            "bit7":"RAM_WE_n, active low, writes RAM when guards allow it",
            "bit8":"PC_INC, active high clock enable for the PC counters",
            "bit9":"PC_LOAD_n, active low load for the PC counters from ARQ",
            "bit10":"AR_LO_CLK, active high clock for address low register",
            "bit11":"AR_HI_CLK, active high clock for address high register",
            "bits12_13":"ADDR_SRC: 00=NORMAL, 01=REG $FFF8+REG_SEL, 10=FAST/IRQ, 11=VECTOR/PC",
            "bits14_15":"ALU_SEL: 00=ADD/SUB, 01=AND, 10=OR, 11=XOR"
        },
        derived_controls:"IR_CLK, OPR_CLK, /RD, /WR, STEP_RST, ALU_SUB, ALU_CIN, CONST_OE, SEXT_OE, PC_LO_OE, PC_HI_OE, REG_SEL, SYS_EI, SYS_DI, SYS_IRET, IRQ_ACK, and HALT_SET are deterministic decode from opcode/operand/flags/step plus the control word; they are not extra ROM output bits",
        bus_rule:"IBUS may have exactly one owner: U12 memory read, U2 operand, U15 ALU result, U60 constant, U61 sign extension, U44 PC low, or U45 PC high",
        U16:"74HC161 step counter uses Q[3:0], allowing 16 micro-steps so PUSH/POP are real",
        U14:"74HC74 flags, Z and C/borrow latch into microcode address",
        U63:"74HC138 SYS decoder enabled only for opcode class SYS and OPR[2:0]",
        U22:"74HC74 IE and IRQ_PENDING",
        U64:"74HC74 HALT latch; SYS 1 sets HALT, /RST clears it, HALT gates CPU_CLK",
        misc:"U65-U66 74HC00/74HC08 gates for IRQ_ACTIVE, IRQ_ACK, IE_SET, IE_CLR, RAM_WE guard, mutually-exclusive bus enables"
    },

    real_feature_paths:[
        "Fetch: PCQ -> ABUS -> ROM -> DBUS -> U12 -> IBUS -> U1/U2",
        "Register read/write: address mux forces $FFF8+rd/rs/r7 -> RAM -> U12 -> IBUS, and U15 -> IBUS -> U12 -> RAM for writeback",
        "ALU ADD/SUB/AND/OR/XOR/SLL: RAM or OPR -> ALU_B; RAM[rd] on IBUS -> ALU_A; selected result -> U15 -> RAM[rd]",
        "SLT/SLTI: subtract sets C/borrow; next micro-step writes $01 or $00 from U60 to RAM[rd]",
        "LB/SB off(rs): RAM[rs] + sext(off5) -> AR_LO, AR_HI policy from microcode -> RAM data transfer",
        "LBfp/SBfp: address mux forces $FF00+OPR -> RAM data transfer",
        "PUSH/POP: REG_SEL=r7 reads/writes SP at $FFFF; ALU +/-1 updates SP; AR uses SP address; data moves through U12",
        "BEQ/BNE/BLT/BGE/J: compare or unconditional path computes same-page PC_LO target in ALU, loads AR={PC_HI,target_lo}, then PC_LOAD",
        "JAL: PC_LO from U44 -> RAM[rd], then same-page relative target through AR -> PC_LOAD",
        "JALR/RET: RAM[rs] -> AR_LO, PC_HI -> AR_HI, PC_LOAD; JALR is same-page indirect by hardware contract",
        "IRQ entry: U44/U45 write PC_LO/PC_HI to $FFF6/$FFF7, address mux loads AR=$7F00, PC_LOAD, IRQ_ACK clears pending and IE",
        "IRET: RAM[$FFF6] -> AR_LO, RAM[$FFF7] -> AR_HI, PC_LOAD, IE_SET"
    ]
},

// ═══════════════════════════════════════════════════════════════
// FULL ISA PIN TRACE
// ═══════════════════════════════════════════════════════════════
//
// Purpose:
//   Preserve the old 19-chip failure trace so we remember why FullHW was added.
//   Do not use this legacy block for schematic capture; use FullHW_Part above.

Legacy_19Chip_Blocker_Trace:{
    verdict:"SUPERSEDED: old 19-chip sketch is blocked; FullHW_Part above replaces it with real hardware",

    chip_pin_audit:[
        {
            chip:"U1 74HC574 opcode IR",
            pins:"2-9=IBUS in, 11=IR_CLK, 12-19=opcode out, 1=/OE tied active",
            trace:"Fetch opcode; opcode[7:0] feeds microcode address; opcode[2:0] is rd for register address.",
            status:"PASS for opcode fetch and rd visibility"
        },
        {
            chip:"U2 74HC574 operand IR",
            pins:"2-9=IBUS in, 11=OPR_CLK, 12-19=operand out, 1=OPR_OE",
            trace:"Immediate/offset byte; may drive IBUS for immediate ALU input.",
            status:"PARTIAL: operand[7:5] source-register path to the address-force network is not pinned"
        },
        {
            chip:"U3 74HC574 ALU B latch",
            pins:"2-9=IBUS in, 11=ALUB_CLK, 12-19=B operand out, 1=/OE disabled",
            trace:"Holds immediate or source register for ADD/SUB/address math.",
            status:"PASS for ADD/SUB/SLL/address-add"
        },
        {
            chip:"U4/U5 74HC283 adders",
            pins:"A inputs=IBUS[7:0], B inputs=U6/U7 outputs, C0=ALU_SUB or carry-in, S[7:0]=U15.D",
            trace:"ADD, SUB, SLL, address add, PC relative add if PC path exists.",
            status:"PARTIAL: no proven carry-in control for SLT/SLTI and no PC-to-ALU path is pinned"
        },
        {
            chip:"U6/U7 74HC86 XOR bank",
            pins:"one input=U3.Q, other input=ALU_SUB, output=adder B",
            trace:"Inverts B for SUB.",
            status:"BLOCKED: this is not enough for ISA XOR; AND/OR are also physically missing"
        },
        {
            chip:"U8/U9 PC registers",
            pins:"current guide says 74HC574, 1=PC_ADDR_n, 11=PC_CLK, 12-19=A bus",
            trace:"Fetch address, PC increment, branch/jump target, IRQ vector, IRET restore.",
            status:"BLOCKED: docs elsewhere say 74HC161 PC; current 574 wiring has no complete increment/reset/load/save path"
        },
        {
            chip:"U10/U11 address latches",
            pins:"1=PC_ADDR, 11=ADDR_LO/HI_CLK, 12-19=A bus",
            trace:"Data memory address, register window address, fast-page address, IRQ save slots.",
            status:"BLOCKED: full A[15:0] source selection is not pinned"
        },
        {
            chip:"U12 74HC245 data bridge",
            pins:"1=BUF_DIR, 19=BUF_OE_n, 2-9=IBUS, 11-18=D bus",
            trace:"ROM/RAM read to IBUS and IBUS write to RAM.",
            status:"PASS if microcode guarantees U2, U12, and U15 are mutually exclusive IBUS drivers"
        },
        {
            chip:"U13/U17 microcode ROM outputs",
            pins:"addr={IRQ_ACTIVE,C,Z,step[2:0],opcode[7:0]}, data=control",
            trace:"Generates all step control signals.",
            status:"BLOCKED: guide mixes an 8-bit group-encoded control word with two direct-control ROM bytes"
        },
        {
            chip:"U14 74HC74 flags",
            pins:"D=zero/carry, CLK=FLAGS_CLK, Q=flag_z/flag_c to microcode address",
            trace:"BEQ/BNE and unsigned BLT/BGE/SLT decision source.",
            status:"PARTIAL: Z is straightforward; C/borrow convention for BLT/BGE/SLT must be frozen and tested"
        },
        {
            chip:"U16 74HC161 step counter",
            pins:"2=CLK, 1=STEP_RST_n, Q[2:0]=microcode address A[10:8]",
            trace:"Instruction sequencing.",
            status:"PASS for up to 8 micro-steps; instructions listed as 9 cycles need proof or a wider step sequence"
        },
        {
            chip:"U18 74HC157 register-address mux",
            pins:"1=REG_ADDR_MODE, selected low-nibble inputs go to U10.D[3:0]",
            trace:"Generate RAM register address $FFF8+reg.",
            status:"BLOCKED: one 157 only handles 4 bits; A[7:4] and A[15:8] force/mux path is not pin-proven"
        },
        {
            chip:"U22 74HC74 interrupt state",
            pins:"IE FF and IRQ_PENDING FF",
            trace:"EI, DI, IRQ latch, IRQ_ACTIVE to microcode A13.",
            status:"BLOCKED: SYS set/clear pins, IRQ edge polarity, IRQ_ACK clear, and IRET re-enable path are not pinned"
        }
    ],

    isa_feature_trace:[
        {
            feature:"Fetch/reset",
            required_path:"/RST -> PC=$0000; PC -> A[15:0]; ROM -> D bus -> U12 -> IBUS -> U1/U2",
            status:"BLOCKED by PC implementation conflict"
        },
        {
            feature:"LI/ADDI/SUBI/SLL and ADD/SUB",
            required_path:"U2 or RAM[reg] -> IBUS -> U3/adder -> U15 -> IBUS -> U12 -> RAM[$FFF8+rd]",
            status:"PARTIAL: path exists conceptually, but register address force and PC/fetch must be fixed"
        },
        {
            feature:"AND/OR/XOR/NOT",
            required_path:"A and B must feed real logic gates and an ALU result mux before U15",
            status:"BLOCKED: current physical ALU only routes adder result"
        },
        {
            feature:"SLT/SLTI/BLT/BGE",
            required_path:"subtract -> C/borrow flag -> microcode conditional write 0/1 or branch",
            status:"BLOCKED until carry-in/borrow convention and constant 0/1 write path are pinned"
        },
        {
            feature:"LB/SB off(rs)",
            required_path:"RAM[$FFF8+rs] -> ALU A; sign-extend off5 -> ALU B; result -> ADDR; RAM read/write",
            status:"BLOCKED: sign extension and address-high behavior are not pin-proven"
        },
        {
            feature:"LBfp/SBfp",
            required_path:"frozen memory map needs RAM fast-page address $FF00+imm8, with $FFF6-$FFFF reserved",
            status:"BLOCKED: fast-page high-byte force and reserved-slot protection are not pin-proven"
        },
        {
            feature:"PUSH/POP and LBsp/SBsp",
            required_path:"r7 SP at $FFFF -> increment/decrement -> write back SP -> use SP as address",
            status:"BLOCKED: needs SP update, address latch, and stack-page policy proof"
        },
        {
            feature:"BEQ/BNE/J",
            required_path:"compare registers or unconditional path -> PC += signed offset",
            status:"BLOCKED until PC add/load path is pinned"
        },
        {
            feature:"JAL/JALR/RET",
            required_path:"save PC low to rd; load PC from relative target or register/page target",
            status:"BLOCKED: no complete PC save/load/high-byte path"
        },
        {
            feature:"SYS NOP/HLT/EI/DI/IRET",
            required_path:"operand subdecode controls halt, U22, and PC restore from $FFF6/$FFF7",
            status:"BLOCKED except NOP; HLT gate, EI/DI pins, and IRET PC restore are not pinned"
        },
        {
            feature:"IRQ entry",
            required_path:"IRQ_ACTIVE -> save PC_LO/HI to RAM[$FFF6/$FFF7] -> PC=$7F00 -> clear IRQ state",
            status:"BLOCKED: no PC-to-data path, fixed IRQ save-address path, or vector-load path is pinned"
        }
    ],

    required_fixes_before_build:[
        "Freeze PC hardware: choose either 4x74HC161 counter PC with a real address mux/buffer, or 2x74HC574 ALU-loaded PC with a proven PC increment/reset/read path. Update all docs to one choice.",
        "Freeze control style: either keep 8-bit group-encoded control and add a decoder table, or document two direct-control ROM bytes. Do not mix both.",
        "Add or remove physical ALU logic ops. Full ISA needs AND/OR/XOR result generation and a result mux; otherwise reduce ISA to ADD/SUB/SLL plus macros.",
        "Replace the partial U18 address mux with a full address-source network for normal address, register $FFF8+reg, fast page, IRQ save slots, and vector/PC load support.",
        "Resolve fast-page hardware: with ROM at $0000-$7FFF, LBfp/SBfp must generate $FF00+imm8 and protect reserved $FFF6-$FFFF.",
        "Pin PC save/restore: JAL, IRQ entry, and IRET need PC low/high paths to and from RAM.",
        "Pin U22 interrupt controls: EI set, DI clear, IRQ edge capture, IRQ_ACK clear, and IRET re-enable.",
        "After fixes, regenerate this trace as PASS/PARTIAL/BLOCKED and only then produce KiCad-ready pin tables."
    ]
},

// ═══════════════════════════════════════════════════════════════
// VERIFICATION
// ═══════════════════════════════════════════════════════════════
//
// Bus conflicts: REAL FULLHW OWNERSHIP DEFINED
//   IBUS drivers: U2(OPR), U12(memory read), U15(ALU result), U44/U45(PC byte),
//                 U60(constant), U61(sign-extend). Microcode must assert only one.
//   ABUS source: U40-U43 select PCQ or ARQ; PC and AR never directly share ABUS.
//   DBUS source: ROM/RAM during read, U12 during write. ROM /WE is tied inactive.
//
// Register access path (real FullHW):
//   Read: ADDR_SRC=REG forces $FFF8+reg_id through U30-U37 into AR, U40-U43 select ARQ
//         → RAM outputs register value → U12 → IBUS → adder A
//   Write: U15 (result) drives IBUS → U12 → RAM[register addr] via /WR pulse
//   Status: real hardware path defined; KiCad/ERC and sim proof pending
//
// PC increment: U8-U11 74HC161 PC counts when PC_INC is asserted during fetch.
// Reset/boot: PC clears to $0000, so A15=0 selects Program ROM for the first fetch.
// RAM remains at $8000-$FFFF for data, optional RAM-loaded code, stack, IRQ save slots, and $FFF8-$FFFF registers.
//
// CHIP COUNT: FullHW target
//   Logic: 49 packages
//   Memory/control ROM: 2 microcode ROM + 1 program ROM + 1 RAM = 4 packages
//   Total: 53 packages
}
