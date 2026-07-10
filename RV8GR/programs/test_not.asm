; RV8-GR NOT pseudo-instruction truth-table test.
; NOT is an assembler pseudo-instruction: XORI $FF.

.org $0000
    SETDP $80
    SETPG $00

    LI $00
    NOT
    SB $10

    LI $55
    NOT
    SB $11

    LI $AA
    NOT
    SB $12

    LI $FF
    NOT
    SB $13

    LI $01
    NOT
    SB $14

    LI $80
    NOT
    SB $15

    LI $7F
    NOT
    SB $16

    LI $F0
    NOT
    SB $17

    LI $0F
    NOT
    SB $18

pass:
    HLT
