`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC21 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC21: https://www.ti.com/lit/ds/symlink/sn74hc21.pdf | N, 14-pin PDIP |
//
// ## 74HC21 - Dual 4-Input AND Gate, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1A |
// | 2 | 1B |
// | 3 | NC |
// | 4 | 1C |
// | 5 | 1D |
// | 6 | 1Y |
// | 7 | GND |
// | 8 | 2Y |
// | 9 | 2A |
// | 10 | 2B |
// | 11 | NC |
// | 12 | 2C |
// | 13 | 2D |
// | 14 | VCC |
//
//


// 74HC21: dual 4-input AND gate

module ttl_74hc21 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] A,
  input [1:0] B,
  input [1:0] C,
  input [1:0] D,
  output [1:0] Y
);

//------------------------------------------------//
wire [1:0] Y_computed;

assign Y_computed = A & B & C & D;
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
