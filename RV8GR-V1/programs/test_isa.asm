; RV8-GR Full ISA Test
; Assembles to ROM at $0000
; Expected: halts at 'pass' label with AC=$00, Z=1

start:
    LI $10          ; AC=$10
    ADDI $05        ; AC=$15
    SUBI $15        ; AC=$00, Z=1
    XORI $AA        ; AC=$AA, Z=0
    MV $00, a0      ; RAM[0]=$AA
    MV $01, a0      ; RAM[1]=$AA
    LI $00          ; AC=$00
    MV a0, $00      ; AC=RAM[0]=$AA
    SUB $01         ; AC=$AA-$AA=$00, Z=1
    BEQ ok1
    HLT             ; FAIL

ok1:
    LI $FF          ; AC=$FF, Z=0
    BEQ fail1       ; should NOT take (Z=0)
    BNE ok2         ; should take (Z=0)
fail1:
    HLT             ; FAIL

ok2:
    MV $02, a0      ; RAM[2]=$FF
    LI $55          ; AC=$55
    ADD $02         ; AC=$55+$FF=$54
    XOR $02         ; AC=$54^$FF=$AB
    SETPG $10       ; PG=$10
    J lo(page10)    ; jump to $1000

.ORG $1000
page10:
    SETPG $00       ; PG=$00
    J lo(back)      ; jump back to $002E

.ORG $002E
back:
    LI $80          ; AC=$80
    MV $03, a0      ; RAM[3]=$80
    SETPG_R $03     ; PG=RAM[3]=$80 (used below but doesn't matter for $00xx)
    LI $00          ; AC=$00
    SUBI $00        ; AC=$00, Z=1

pass:
    HLT             ; ALL PASS
