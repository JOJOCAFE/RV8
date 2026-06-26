; RV8-GR Test ROM — Full hardware verification
; Flash to SST39SF010A. PC starts at $0000.
; PASS: halts at 'pass' label. FAIL: halts earlier.

; === TEST 1: ALU immediate ===
start:
    LI $00          ; AC=0, Z=1
    ADDI $01        ; AC=1
    ADDI $FE        ; AC=$FF
    ADDI $01        ; AC=$00 (overflow), Z=1
    BEQ t1ok
    HLT
t1ok:
    LI $80
    SUBI $80        ; AC=0, Z=1
    BEQ t2ok
    HLT
t2ok:

; === TEST 2: XOR immediate ===
    LI $AA
    XORI $FF        ; $AA^$FF=$55
    SUBI $55        ; =0
    BEQ t3ok
    HLT
t3ok:

; === TEST 3: Store/Load ===
    LI $42
    MV $00, a0      ; RAM[0]=$42
    LI $00
    MV a0, $00      ; AC=$42
    SUBI $42        ; =0
    BEQ t4ok
    HLT
t4ok:

; === TEST 4: ADD/SUB register ===
    LI $33
    MV $01, a0      ; RAM[1]=$33
    LI $11
    MV $02, a0      ; RAM[2]=$11
    LI $00
    ADD $01         ; AC=$33
    ADD $02         ; AC=$44
    SUB $01         ; AC=$11
    SUB $02         ; AC=$00, Z=1
    BEQ t5ok
    HLT
t5ok:

; === TEST 5: XOR register ===
    LI $FF
    MV $03, a0      ; RAM[3]=$FF
    LI $AA
    XOR $03         ; $AA^$FF=$55
    SUBI $55        ; =0
    BEQ t6ok
    HLT
t6ok:

; === TEST 6: BEQ taken + not-taken ===
    LI $00          ; Z=1
    BEQ t6a         ; taken
    HLT
t6a:
    LI $01          ; Z=0
    BEQ t6fail      ; NOT taken (Z=0)
    J lo(t7ok)
t6fail:
    HLT
t7ok:

; === TEST 7: BNE taken + not-taken ===
    LI $01          ; Z=0
    BNE t7a         ; taken
    HLT
t7a:
    LI $00          ; Z=1
    BNE t7fail      ; NOT taken (Z=1)
    J lo(t8ok)
t7fail:
    HLT
t8ok:

; === TEST 8: SETPG + J (cross-page) ===
    SETPG $10
    J $00           ; → $1000

; === TEST 9: SETPG_R ===
t8ret:
    LI $00
    MV $04, a0      ; RAM[4]=$00
    SETPG_R $04     ; PG=RAM[4]=$00

; === TEST 10: Subroutine ===
    LI lo(subret)
    MV $07, a0      ; save return addr
    J lo(mysub)     ; call

subret:
    MV a0, $05      ; AC=RAM[5]
    SUBI $77        ; =0 if sub wrote $77
    BEQ pass
    HLT

; === ALL PASS ===
pass:
    HLT

; === Subroutine at $00C0 ===
.ORG $00C0
mysub:
    LI $77
    MV $05, a0      ; RAM[5]=$77
    SETPG $00
    J lo(subret)    ; return

; === Page $10 code ===
.ORG $1000
page10:
    SETPG $00
    J lo(t8ret)     ; back to page $00
