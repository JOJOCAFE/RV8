`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC157 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC157: https://www.ti.com/lit/ds/symlink/sn74hc157.pdf | N, 16-pin PDIP |
//
// ## 74HC157 - Quad 2-Line to 1-Line Multiplexer, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | A/B |
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
// | 15 | /G |
// | 16 | VCC |
//
//


// 74HC157: quad 2-input multiplexer with active-low enable

module ttl_74hc157 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input Select,
  input [WIDTH-1:0] A,
  input [WIDTH-1:0] B,
  output [WIDTH-1:0] Y
);

//------------------------------------------------//
wire [WIDTH-1:0] Y_computed;

assign Y_computed = Enable_bar ? {WIDTH{1'b0}} : (Select ? B : A);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
