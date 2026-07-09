; RV8GR example: echo-style buffer copy
; Closest supported equivalent to terminal echo without UART hardware:
; seed RAM[$8020..$8023], then copy it to RAM[$8030..$8033].

.org $0000

start:
    SETDP $80       ; RAM/register page
    SETPG $00

    ; Seed an input buffer with "RV8!".
    LI $52
    SB $20
    LI $56
    SB $21
    LI $38
    SB $22
    LI $21
    SB $23

    ; Echo/copy input buffer to output buffer.
    LB $20
    SB $30
    LB $21
    SB $31
    LB $22
    SB $32
    LB $23
    SB $33

done:
    HLT

