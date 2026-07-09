`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC00 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC00: https://www.ti.com/lit/ds/symlink/sn74hc00.pdf | N, 14-pin PDIP |
//
// ## 74HC00 - Quad 2-Input NAND Gate, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1A |
// | 2 | 1B |
// | 3 | 1Y |
// | 4 | 2A |
// | 5 | 2B |
// | 6 | 2Y |
// | 7 | GND |
// | 8 | 3Y |
// | 9 | 3A |
// | 10 | 3B |
// | 11 | 4Y |
// | 12 | 4A |
// | 13 | 4B |
// | 14 | VCC |
//
//


// 74HC00: quad 2-input NAND gate

module ttl_74hc00 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [3:0] A,
  input [3:0] B,
  output [3:0] Y
);

//------------------------------------------------//
wire [3:0] Y_computed;

assign Y_computed = ~(A & B);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
