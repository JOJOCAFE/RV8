`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC04 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC04: https://www.ti.com/lit/ds/symlink/sn74hc04.pdf | N, 14-pin PDIP |
//
// ## 74HC04 - Hex Inverter, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1A |
// | 2 | 1Y |
// | 3 | 2A |
// | 4 | 2Y |
// | 5 | 3A |
// | 6 | 3Y |
// | 7 | GND |
// | 8 | 4Y |
// | 9 | 4A |
// | 10 | 5Y |
// | 11 | 5A |
// | 12 | 6Y |
// | 13 | 6A |
// | 14 | VCC |
//
//


// 74HC04: hex inverter

module ttl_74hc04 #(parameter WIDTH = 6, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [WIDTH-1:0] A,
  output [WIDTH-1:0] Y
);

//------------------------------------------------//
wire [WIDTH-1:0] Y_computed;

assign Y_computed = ~A;
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
