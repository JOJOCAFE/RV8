; B-024: RV8-GR Deterministic Game ROM
; "Reaction Countdown" — a tiny deterministic demo game
;
; HOW IT WORKS (no external device, no randomness, fully deterministic):
;   - A countdown timer t0 starts at 10 and ticks down: 10,9,8,...,0.
;   - There is one "reaction window" at count == 7.
;   - In a real build a button press during that window is the player's
;     reaction. Here there is no input device, so we deterministically
;     latch a WIN the first (and only) time the count equals 7.
;   - The countdown ALWAYS runs all the way down to 0 and then stops.
;     The win is latched once and never re-triggered, so the loop always
;     terminates at game_over. This makes the outcome regression-testable.
;
; RESULT:
;   result = 1 (WIN)  because the countdown passes through 7.
;   (If you change START_COUNT below 7, the window is never hit and
;    result stays 0 = LOSE — still deterministic.)
;
; RAM LAYOUT (data page $80 selects RAM $8000-$80FF window):
;   $8000-$8007 : register aliases a0-a2,t0-t2,s0,ra
;   $8010       : live countdown value (updated each tick)
;   $8011       : final result copy for verification (0=lose, 1=win)
;   $8020       : result latch (0=lose, 1=win)
; I/O MIRRORS (data page $FF, only visible with a board on the I/O slot):
;   $FF10       : final result mirror
;   $FF20       : win pulse mirror
;
; BUILD: python3 tools/rv8gr_asm.py programs/game.asm -o /tmp/rv8gr-game.bin
; TEST:  python3 sim/test_game.py

.org $0000

start:
    SETDP $80           ; RAM/register page
    SETPG $00           ; code lives on page $00

    LI $0A              ; countdown = 10
    MV t0, a0           ; t0 = 10

    CLR                 ; result = 0 (lose until proven otherwise)
    SB $20              ; RAM[$8020] = 0

game_loop:
    ; write live countdown to RAM mirror
    MV a0, t0
    SB $10              ; RAM[$8010] = current count

    ; reached zero? -> game over
    MV a0, t0
    SUBI $00            ; Z = 1 when t0 == 0
    BEQ game_over

    ; reaction window: is count == 7?
    MV a0, t0
    SUBI $07            ; Z = 1 when t0 == 7
    BNE tick            ; not the window -> just tick down

    ; --- win window hit exactly once ---
    LI $01
    SB $20              ; RAM[$8020] = 1 (win latched)
    SETDP $FF
    SB $20              ; pulse win mirror $FF20 (needs I/O board to see)
    SETDP $80           ; ALWAYS restore RAM page before continuing

tick:
    ; decrement countdown and loop
    MV a0, t0
    DEC                 ; t0 = t0 - 1
    MV t0, a0
    J game_loop

game_over:
    ; countdown expired; publish the latched result
    LB $20              ; a0 = result (data page still $80)
    SB $11              ; RAM[$8011] = final result copy

    SETDP $FF
    SB $10              ; mirror final result to $FF10
    SETDP $80           ; leave the CPU on the RAM page at halt

    HLT                 ; J self
