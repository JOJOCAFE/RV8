`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC244 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC244: https://www.ti.com/lit/ds/symlink/sn74hc244.pdf | N, 20-pin PDIP |
//
// ## 74HC244 - Octal Buffer/Line Driver, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /1OE |
// | 2 | 1A1 |
// | 3 | 2Y4 |
// | 4 | 1A2 |
// | 5 | 2Y3 |
// | 6 | 1A3 |
// | 7 | 2Y2 |
// | 8 | 1A4 |
// | 9 | 2Y1 |
// | 10 | GND |
// | 11 | 2A1 |
// | 12 | 1Y4 |
// | 13 | 2A2 |
// | 14 | 1Y3 |
// | 15 | 2A3 |
// | 16 | 1Y2 |
// | 17 | 2A4 |
// | 18 | 1Y1 |
// | 19 | /2OE |
// | 20 | VCC |
//


// 74HC244: octal buffer/line driver with 3-state outputs

module ttl_74hc244 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE1_bar,
  input OE2_bar,
  input [7:0] A,
  output [7:0] Y
);

assign #(DELAY_RISE, DELAY_FALL) Y[3:0] = OE1_bar ? 4'hz : A[3:0];
assign #(DELAY_RISE, DELAY_FALL) Y[7:4] = OE2_bar ? 4'hz : A[7:4];

endmodule
