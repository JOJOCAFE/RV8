; RV8GR all-ISA equivalence program.
; Single source for Python-vs-Verilog equivalence tests.
;
; Expected final state:
;   PC=$0086, AC=$00, Z=1, IE=1, IRQ_FF=1, PG=$00, DP=$00
; Expected RAM checkpoints:
;   RAM[$8000]=$AA, RAM[$8001]=$55, RAM[$8002]=$FF, RAM[$8004]=$00
;   RAM[$8005]=$42, RAM[$8007]=$5E, RAM[$9000]=$A5

.org $0000
    LI $00
    BEQ zero_ok
fail_0004:
    HLT

.org $0008
zero_ok:
    LI $05
    BNE nonzero_ok
fail_000c:
    HLT

.org $0010
nonzero_ok:
    ADDI $03
    SUBI $08
    XORI $AA
    SB $00
    LI $00
    LB $00
    SUBI $AA
    BEQ ram0_ok
fail_0020:
    HLT

.org $0022
ram0_ok:
    LI $55
    SB $01
    ADD $01
    SUB $00
    BEQ sub_ok
fail_002c:
    HLT

.org $002e
sub_ok:
    LI $FF
    SB $02
    XOR $02
    BEQ xor_ok
fail_0036:
    HLT

.org $0038
xor_ok:
    SETPG $10
    J $00

.org $1000
page10:
    SETPG $7F
    J $00

.org $7F00
page7f:
    SETPG $00
    J $40

.org $0040
page_return:
    LI $00
    SB $04
    SETPG_R $04
    SETPG $00
    LI lo(return_from_subroutine)
    SB ra
    J subroutine

.org $005E
return_from_subroutine:
    LB $05
    SUBI $42
    BEQ setdp_tests
fail_0064:
    HLT

.org $0066
setdp_tests:
    SETDP $90
    LI $A5
    SB $00
    LI $00
    LB $00
    SUBI $A5
    BEQ rom_read_test
fail_0074:
    HLT

.org $0076
rom_read_test:
    SETDP $00
    LB $00
    SUBI $30
    BEQ irq_and_pass
fail_007e:
    HLT

.org $0080
irq_and_pass:
    EI
    DI
    NOP
pass:
    HLT

.org $0090
subroutine:
    LI $42
    SB $05
    SETPG $00
    J return_from_subroutine
