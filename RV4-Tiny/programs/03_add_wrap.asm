; Four-bit add wraps: 14 + 3 = 1.
LI 14
SW $E
LI 3
SW $F
LW $E
ADD $F
OUT
HLT
