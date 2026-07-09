`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC273 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC273: https://www.ti.com/lit/ds/symlink/sn74hc273.pdf | N, 20-pin PDIP |
//
// ## 74HC273 - Octal D-Type Flip-Flop With Clear, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /CLR |
// | 2 | 1Q |
// | 3 | 1D |
// | 4 | 2D |
// | 5 | 2Q |
// | 6 | 3Q |
// | 7 | 3D |
// | 8 | 4D |
// | 9 | 4Q |
// | 10 | GND |
// | 11 | CLK |
// | 12 | 5Q |
// | 13 | 5D |
// | 14 | 6D |
// | 15 | 6Q |
// | 16 | 7Q |
// | 17 | 7D |
// | 18 | 8D |
// | 19 | 8Q |
// | 20 | VCC |
//


// 74HC273: octal D-type flip-flop with asynchronous clear

module ttl_74hc273 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input Clk,
  input [7:0] D,
  output [7:0] Q
);

reg [7:0] q;

always @(posedge Clk or negedge Clear_bar) begin
  if (!Clear_bar) q <= 8'h00;
  else q <= D;
end

assign #(DELAY_RISE, DELAY_FALL) Q = q;

endmodule
