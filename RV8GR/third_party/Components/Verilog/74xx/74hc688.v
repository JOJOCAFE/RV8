`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC688 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments CD74HC688: https://www.ti.com/lit/gpn/cd74hc688 | E, 20-pin PDIP |
//
// ## 74HC688 - 8-Bit Identity Comparator, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /E |
// | 2 | A0 |
// | 3 | B0 |
// | 4 | A1 |
// | 5 | B1 |
// | 6 | A2 |
// | 7 | B2 |
// | 8 | A3 |
// | 9 | B3 |
// | 10 | GND |
// | 11 | A4 |
// | 12 | B4 |
// | 13 | A5 |
// | 14 | B5 |
// | 15 | A6 |
// | 16 | B6 |
// | 17 | A7 |
// | 18 | B7 |
// | 19 | Y |
// | 20 | VCC |
//
//


// 74HC688: 8-bit identity comparator with active-low enable and output

module ttl_74hc688 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input [WIDTH-1:0] A,
  input [WIDTH-1:0] B,
  output Equal_bar
);

//------------------------------------------------//
wire Equal_bar_computed;

assign Equal_bar_computed = Enable_bar ? 1'b1 : (A == B ? 1'b0 : 1'b1);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Equal_bar = Equal_bar_computed;

endmodule
