`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC02 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC02: https://www.ti.com/lit/ds/symlink/sn74hc02.pdf | N, 14-pin PDIP |
//
// ## 74HC02 - Quad 2-Input NOR Gate, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1Y |
// | 2 | 1A |
// | 3 | 1B |
// | 4 | 2Y |
// | 5 | 2A |
// | 6 | 2B |
// | 7 | GND |
// | 8 | 3A |
// | 9 | 3B |
// | 10 | 3Y |
// | 11 | 4A |
// | 12 | 4B |
// | 13 | 4Y |
// | 14 | VCC |
//


// 74HC02: quad 2-input NOR gate

module ttl_74hc02 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [3:0] A,
  input [3:0] B,
  output [3:0] Y
);

wire [3:0] Y_computed;

assign Y_computed = ~(A | B);

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
