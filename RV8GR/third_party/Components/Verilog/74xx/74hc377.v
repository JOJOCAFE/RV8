`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC377 DIP pinout
//
// - Function: octal D-type flip-flop with data enable, positive-edge trigger
// - Package verified: DIP20 / PDIP20; TI SN74HC377N PDIP N package
// - Source: `../Source/74HC377_TI_27924_SN74HC377N_DIPVERIFY.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | E |
// | 2 | Q0 |
// | 3 | D0 |
// | 4 | D1 |
// | 5 | Q1 |
// | 6 | Q2 |
// | 7 | D2 |
// | 8 | D3 |
// | 9 | Q3 |
// | 10 | GND |
// | 11 | CP |
// | 12 | Q4 |
// | 13 | D4 |
// | 14 | D5 |
// | 15 | Q5 |
// | 16 | Q6 |
// | 17 | D6 |
// | 18 | D7 |
// | 19 | Q7 |
// | 20 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// Octal D flip-flop with enable

module ttl_74hc377 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input [WIDTH-1:0] D,
  input Clk,
  output [WIDTH-1:0] Q
);

//------------------------------------------------//
reg [WIDTH-1:0] Q_current;

always @(posedge Clk)
begin
  if (!Enable_bar)
    Q_current <= D;
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;

endmodule
