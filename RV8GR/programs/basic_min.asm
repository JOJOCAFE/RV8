; RV8GR B-011 minimal BASIC-style ROM, phase 1.
;
; This is not an interactive Tiny BASIC. RV8GR v1.0 has no UART and no
; indexed/indirect load, so the first ROM proves the runtime conventions:
; fixed ROM program, RAM variables, PRINT output buffer, and optional $FF10
; output mirror.
;
; BASIC program represented:
;   10 LET A = 1
;   20 PRINT A
;   30 LET A = A + 1
;   40 PRINT A
;   50 LET A = A + 1
;   60 PRINT A
;   70 END
;
; RAM page $80:
;   $8020 = variable A
;   $8040..$8042 = PRINT transcript: 1, 2, 3
;   $8043 = pass marker $42
;
; Optional I/O:
;   $FF10 receives each PRINT value when an output board exists.

.org $0000

start:
    SETDP $80
    SETPG $00

    ; Clear transcript.
    LI $00
    SB $40
    SB $41
    SB $42
    SB $43

line10_let_a_1:
    LI $01
    SB $20

line20_print_a:
    LB $20
    SB $40
    SETDP $FF
    SB $10
    SETDP $80

line30_let_a_add_1:
    LB $20
    INC
    SB $20

line40_print_a:
    LB $20
    SB $41
    SETDP $FF
    SB $10
    SETDP $80

line50_let_a_add_1:
    LB $20
    INC
    SB $20

line60_print_a:
    LB $20
    SB $42
    SETDP $FF
    SB $10
    SETDP $80

line70_end:
    LI $42
    SB $43

pass:
    HLT

; Documented token stream for the same program. Phase 1 keeps this as ROM data
; while the runtime is direct-coded. A later interactive/token interpreter can
; consume this format once I/O and indirect/indexed addressing are available.
;
; Token ids:
;   1=LET_A_IMM, 2=PRINT_A, 3=LET_A_ADD_IMM, 4=END
.org $0100
token_program:
    .db 10, 1, 1       ; 10 LET A = 1
    .db 20, 2          ; 20 PRINT A
    .db 30, 3, 1       ; 30 LET A = A + 1
    .db 40, 2          ; 40 PRINT A
    .db 50, 3, 1       ; 50 LET A = A + 1
    .db 60, 2          ; 60 PRINT A
    .db 70, 4          ; 70 END
