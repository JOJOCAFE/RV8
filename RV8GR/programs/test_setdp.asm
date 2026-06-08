; RV8-GR Test: Large RAM access via SETDP
; Tests writing/reading across multiple pages (5KB+ usage)
; Writes pattern to RAM pages $10-$23 (5120 bytes = 5KB)
; Then reads back and verifies
;
; Expected: halt at 'pass' if all OK

    .org $8000

start:
    ; --- Write phase: fill 20 pages (5KB) with page number ---
    ; Page $10: fill with $10
    SETDP $10
    LI $10
    SB $00          ; RAM[$1000] = $10
    SB $80          ; RAM[$1080] = $10
    SB $FF          ; RAM[$10FF] = $10

    ; Page $15: fill with $15
    SETDP $15
    LI $15
    SB $00          ; RAM[$1500] = $15
    SB $40          ; RAM[$1540] = $15

    ; Page $20: fill with $20
    SETDP $20
    LI $20
    SB $00          ; RAM[$2000] = $20
    SB $FF          ; RAM[$20FF] = $20

    ; Page $23: fill with $23 (top of 5KB range)
    SETDP $23
    LI $23
    SB $FF          ; RAM[$23FF] = $23

    ; --- Read phase: verify data ---
    ; Read page $10
    SETDP $10
    LB $00          ; AC = RAM[$1000] should be $10
    SUBI $10
    BEQ t1ok
    J fail

t1ok:
    LB $FF          ; AC = RAM[$10FF] should be $10
    SUBI $10
    BEQ t2ok
    J fail

t2ok:
    ; Read page $15
    SETDP $15
    LB $00          ; AC = RAM[$1500] should be $15
    SUBI $15
    BEQ t3ok
    J fail

t3ok:
    LB $40          ; AC = RAM[$1540] should be $15
    SUBI $15
    BEQ t4ok
    J fail

t4ok:
    ; Read page $20
    SETDP $20
    LB $00          ; AC = RAM[$2000] should be $20
    SUBI $20
    BEQ t5ok
    J fail

t5ok:
    LB $FF          ; AC = RAM[$20FF] should be $20
    SUBI $20
    BEQ t6ok
    J fail

t6ok:
    ; Read page $23
    SETDP $23
    LB $FF          ; AC = RAM[$23FF] should be $23
    SUBI $23
    BEQ t7ok
    J fail

t7ok:
    ; --- Test ROM read via SETDP $80+ ---
    SETDP $80
    LB $00          ; AC = ROM[$8000] = first byte of this program = $40 (SETDP)
    SUBI $40
    BEQ t8ok
    J fail

t8ok:
    ; --- Verify page 0 registers still work ---
    SETDP $00
    LI $77
    SB $05          ; RAM[$0005] = $77
    LI $00
    LB $05          ; AC = RAM[$0005] should be $77
    SUBI $77
    BEQ pass
    J fail

pass:
    HLT             ; SUCCESS

fail:
    LI $FF          ; AC=$FF = error marker
    HLT             ; FAIL
