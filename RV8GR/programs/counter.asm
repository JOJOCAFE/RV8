; RV8GR example: counter
; Counts $00..$0F. Each value is stored in RAM[$8010] and also written
; to memory-mapped I/O address $FF10 when an output board is attached.

.org $0000

start:
    SETDP $80       ; RAM/register page
    SETPG $00
    LI $00
    MV t0, a0       ; t0 = current count

count_loop:
    MV a0, t0
    SB $10          ; RAM[$8010] = current count

    SETDP $FF
    SB $10          ; optional output mirror at $FF10

    SETDP $80
    MV a0, t0
    INC
    MV t0, a0
    SUBI $10        ; stop after count reaches $10
    BEQ done
    J count_loop

done:
    MV a0, t0
    SB $11          ; RAM[$8011] = final count marker ($10)
    HLT

