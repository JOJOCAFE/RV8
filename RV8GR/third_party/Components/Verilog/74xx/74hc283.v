`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC283 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments CD74HC283: https://www.ti.com/lit/ds/symlink/cd74hc283.pdf | N, 16-pin PDIP |
//
// ## 74HC283 - 4-Bit Binary Full Adder, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | S2 |
// | 2 | B2 |
// | 3 | A2 |
// | 4 | S1 |
// | 5 | A1 |
// | 6 | B1 |
// | 7 | C0 |
// | 8 | GND |
// | 9 | C4 |
// | 10 | S4 |
// | 11 | B4 |
// | 12 | A4 |
// | 13 | S3 |
// | 14 | A3 |
// | 15 | B3 |
// | 16 | VCC |
//
//


// 74HC283: 4-bit binary full adder with carry

module ttl_74hc283 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [WIDTH-1:0] A,
  input [WIDTH-1:0] B,
  input C_in,
  output [WIDTH-1:0] Sum,
  output C_out
);

//------------------------------------------------//
reg [WIDTH-1:0] Sum_computed;
reg C_computed;

always @(*)
begin
  {C_computed, Sum_computed} = {1'b0, A} + {1'b0, B} + C_in;
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Sum = Sum_computed;
assign #(DELAY_RISE, DELAY_FALL) C_out = C_computed;

endmodule
