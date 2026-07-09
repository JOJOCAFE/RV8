`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC42 DIP pinout
//
// - Function: BCD to decimal decoder, 1-of-10
// - Package verified: DIP16 / PDIP16; TI SN74HC42N N package, 300-mil DIP; pin numbers shared with D/J/N/W packages
// - Source: `../Source/74HC42_TI_27931_SN74HC42N_DIPVERIFY.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 0Y |
// | 2 | 1Y |
// | 3 | 2Y |
// | 4 | 3Y |
// | 5 | 4Y |
// | 6 | 5Y |
// | 7 | 6Y |
// | 8 | GND |
// | 9 | 7Y |
// | 10 | 8Y |
// | 11 | 9Y |
// | 12 | 3A |
// | 13 | 2A |
// | 14 | 1A |
// | 15 | 0A |
// | 16 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// BCD to decimal one-of-ten decoder

module ttl_74hc42 #(parameter WIDTH_OUT = 10, WIDTH_IN = $clog2(WIDTH_OUT),
                  DELAY_RISE = 0, DELAY_FALL = 0)
(
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
    if (i == A)
      computed[i] = 1'b0;
    else
      computed[i] = 1'b1;
  end
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = computed;

endmodule
