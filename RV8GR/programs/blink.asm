; RV8GR example: blink-style output pattern
; Writes alternating values to memory-mapped I/O address $FF10.
; If an LED latch or GPIO board is attached to /SLOT1, the pattern is visible.

.org $0000

start:
    SETDP $80       ; RAM/register page for delay counter
    SETPG $00       ; code runs on page $00

blink_loop:
    SETDP $FF       ; I/O page
    LI $55
    SB $10          ; write pattern to $FF10

    SETDP $80
    LI $20
    MV t0, a0
delay_on:
    MV a0, t0
    DEC
    MV t0, a0
    BNE delay_on

    SETDP $FF
    LI $AA
    SB $10          ; write inverse pattern to $FF10

    SETDP $80
    LI $20
    MV t0, a0
delay_off:
    MV a0, t0
    DEC
    MV t0, a0
    BNE delay_off

    J blink_loop

