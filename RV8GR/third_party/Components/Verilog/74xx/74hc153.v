`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC153 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC153: https://www.ti.com/lit/ds/symlink/sn74hc153.pdf | N, 16-pin PDIP |
//
// ## 74HC153 - Dual 4-Line to 1-Line Data Selector/Multiplexer, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /1G |
// | 2 | B |
// | 3 | 1C3 |
// | 4 | 1C2 |
// | 5 | 1C1 |
// | 6 | 1C0 |
// | 7 | 1Y |
// | 8 | GND |
// | 9 | 2Y |
// | 10 | 2C0 |
// | 11 | 2C1 |
// | 12 | 2C2 |
// | 13 | 2C3 |
// | 14 | A |
// | 15 | /2G |
// | 16 | VCC |
//


// 74HC153: dual 4-line to 1-line data selector/multiplexer

module ttl_74hc153 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] Enable_bar,
  input [1:0] Select,
  input [3:0] C1,
  input [3:0] C2,
  output Y1,
  output Y2
);

wire y1_computed;
wire y2_computed;

assign y1_computed = Enable_bar[0] ? 1'b0 : C1[Select];
assign y2_computed = Enable_bar[1] ? 1'b0 : C2[Select];

assign #(DELAY_RISE, DELAY_FALL) Y1 = y1_computed;
assign #(DELAY_RISE, DELAY_FALL) Y2 = y2_computed;

endmodule
