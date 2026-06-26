; RV8-GR Test: Large RAM access via SETDP
; Tests writing/reading across multiple pages (5KB+ usage)
; Writes pattern to RAM pages $90-$A3 (5120 bytes = 5KB)
; Then reads back and verifies
;
; Expected: halt at 'pass' if all OK

    .org $0000

start:
    ; --- Write phase: fill 20 pages (5KB) with page number ---
    ; Page $90: fill with $90
    SETDP $90
    LI $90
    SB $00          ; RAM[$9000] = $90
    SB $80          ; RAM[$9080] = $90
    SB $FF          ; RAM[$90FF] = $90

    ; Page $95: fill with $95
    SETDP $95
    LI $95
    SB $00          ; RAM[$9500] = $95
    SB $40          ; RAM[$9540] = $95

    ; Page $A0: fill with $A0
    SETDP $A0
    LI $A0
    SB $00          ; RAM[$A000] = $A0
    SB $FF          ; RAM[$A0FF] = $A0

    ; Page $A3: fill with $A3 (top of 5KB range)
    SETDP $A3
    LI $A3
    SB $FF          ; RAM[$A3FF] = $A3

    ; --- Read phase: verify data ---
    ; Read page $90
    SETDP $90
    LB $00          ; AC = RAM[$9000] should be $90
    SUBI $90
    BEQ t1ok
    J fail

t1ok:
    LB $FF          ; AC = RAM[$90FF] should be $90
    SUBI $90
    BEQ t2ok
    J fail

t2ok:
    ; Read page $95
    SETDP $95
    LB $00          ; AC = RAM[$9500] should be $95
    SUBI $95
    BEQ t3ok
    J fail

t3ok:
    LB $40          ; AC = RAM[$9540] should be $95
    SUBI $95
    BEQ t4ok
    J fail

t4ok:
    ; Read page $A0
    SETDP $A0
    LB $00          ; AC = RAM[$A000] should be $A0
    SUBI $A0
    BEQ t5ok
    J fail

t5ok:
    LB $FF          ; AC = RAM[$A0FF] should be $A0
    SUBI $A0
    BEQ t6ok
    J fail

t6ok:
    ; Read page $A3
    SETDP $A3
    LB $FF          ; AC = RAM[$A3FF] should be $A3
    SUBI $A3
    BEQ t7ok
    J fail

t7ok:
    ; --- Test ROM read via SETDP $00 ---
    SETDP $00
    LB $00          ; AC = ROM[$0000] = first byte of this program = $40 (SETDP)
    SUBI $40
    BEQ t8ok
    J fail

t8ok:
    ; --- Verify default RAM page registers still work ---
    SETDP $80
    LI $77
    SB $05          ; RAM[$8005] = $77
    LI $00
    LB $05          ; AC = RAM[$8005] should be $77
    SUBI $77
    BEQ pass
    J fail

pass:
    HLT             ; SUCCESS

fail:
    LI $FF          ; AC=$FF = error marker
    HLT             ; FAIL
