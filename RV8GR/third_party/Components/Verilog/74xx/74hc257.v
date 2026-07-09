`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC257 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC257: https://www.ti.com/lit/ds/symlink/sn74hc257.pdf | N, 16-pin PDIP |
//
// ## 74HC257 - Quad 2-Input Multiplexer With 3-State Outputs, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | S |
// | 2 | 1A |
// | 3 | 1B |
// | 4 | 1Y |
// | 5 | 2A |
// | 6 | 2B |
// | 7 | 2Y |
// | 8 | GND |
// | 9 | 3Y |
// | 10 | 3B |
// | 11 | 3A |
// | 12 | 4Y |
// | 13 | 4B |
// | 14 | 4A |
// | 15 | /OE |
// | 16 | VCC |
//


// 74HC257: quad 2-input multiplexer with 3-state outputs

module ttl_74hc257 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input Select,
  input [3:0] A,
  input [3:0] B,
  output [3:0] Y
);

assign #(DELAY_RISE, DELAY_FALL) Y = OE_bar ? 4'hz : (Select ? B : A);

endmodule
