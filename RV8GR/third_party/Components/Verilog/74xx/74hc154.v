`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC154 DIP pinout
//
// - Function: 4-to-16 line decoder/demultiplexer
// - Package verified: DIP24
// - Source: `../Source/74HC154_NXP_344457.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | Y0 |
// | 2 | Y1 |
// | 3 | Y2 |
// | 4 | Y3 |
// | 5 | Y4 |
// | 6 | Y5 |
// | 7 | Y6 |
// | 8 | Y7 |
// | 9 | Y8 |
// | 10 | Y9 |
// | 11 | Y10 |
// | 12 | GND |
// | 13 | Y11 |
// | 14 | Y12 |
// | 15 | Y13 |
// | 16 | Y14 |
// | 17 | Y15 |
// | 18 | E0 |
// | 19 | E1 |
// | 20 | A3 |
// | 21 | A2 |
// | 22 | A1 |
// | 23 | A0 |
// | 24 | VCC |
//


// 74HC154: 4-line to 16-line decoder/demultiplexer (inverted outputs)

module ttl_74hc154 #(parameter WIDTH_OUT = 16, WIDTH_IN = $clog2(WIDTH_OUT),
                   DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable1_bar,
  input Enable2_bar,
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
    if (!Enable1_bar && !Enable2_bar && i == A)
      computed[i] = 1'b0;
    else
      computed[i] = 1'b1;
  end
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = computed;

endmodule
