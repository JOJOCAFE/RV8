`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC151 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC151: https://www.ti.com/lit/ds/symlink/sn74hc151.pdf | N, 16-pin PDIP |
//
// ## 74HC151 - 8-Line to 1-Line Data Selector/Multiplexer, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | D3 |
// | 2 | D2 |
// | 3 | D1 |
// | 4 | D0 |
// | 5 | Y |
// | 6 | /Y |
// | 7 | /G |
// | 8 | GND |
// | 9 | C |
// | 10 | B |
// | 11 | A |
// | 12 | D7 |
// | 13 | D6 |
// | 14 | D5 |
// | 15 | D4 |
// | 16 | VCC |
//


// 74HC151: 8-line to 1-line data selector/multiplexer

module ttl_74hc151 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input [2:0] Select,
  input [7:0] D,
  output Y,
  output Y_bar
);

wire y_computed;

assign y_computed = Enable_bar ? 1'b0 : D[Select];

assign #(DELAY_RISE, DELAY_FALL) Y = y_computed;
assign #(DELAY_RISE, DELAY_FALL) Y_bar = ~y_computed;

endmodule
