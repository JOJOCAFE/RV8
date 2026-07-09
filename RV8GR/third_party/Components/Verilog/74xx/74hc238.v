`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC238 DIP pinout
//
// - Function: 3-to-8 line decoder/demultiplexer, active-high outputs
// - Package verified: DIP16; NXP 74HC238N plastic dual in-line package SOT38-4
// - Source: `../Source/74HC238_NXP_344486_DIPCHECK.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | A0 |
// | 2 | A1 |
// | 3 | A2 |
// | 4 | E1 |
// | 5 | E2 |
// | 6 | E3 |
// | 7 | Y7 |
// | 8 | GND |
// | 9 | Y6 |
// | 10 | Y5 |
// | 11 | Y4 |
// | 12 | Y3 |
// | 13 | Y2 |
// | 14 | Y1 |
// | 15 | Y0 |
// | 16 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// 3-line to 8-line decoder/demultiplexer (active high outputs)

module ttl_74hc238 #(parameter WIDTH_OUT = 8, WIDTH_IN = $clog2(WIDTH_OUT),
                   DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable1_bar,
  input Enable2_bar,
  input Enable3,
  input [WIDTH_IN-1:0] A,
  output [WIDTH_OUT-1:0] Y
);

//------------------------------------------------//
reg [WIDTH_OUT-1:0] computed;
integer i;

always @(*)
begin
  for (i = 0; i < WIDTH_OUT; i++)
  begin
    if (!Enable1_bar && !Enable2_bar && Enable3 && i == A)
      computed[i] = 1'b1;
    else
      computed[i] = 1'b0;
  end
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = computed;

endmodule
