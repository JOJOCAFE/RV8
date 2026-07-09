`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC374 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC374: https://www.ti.com/lit/ds/symlink/sn74hc374.pdf | N, 20-pin PDIP |
//
// ## 74HC374 - Octal D-Type Flip-Flop With 3-State Outputs, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /OE |
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


// 74HC374: octal D-type flip-flop with 3-state outputs

module ttl_74hc374 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input Clk,
  input [7:0] D,
  output [7:0] Q
);

reg [7:0] q;

always @(posedge Clk) begin
  q <= D;
end

assign #(DELAY_RISE, DELAY_FALL) Q = OE_bar ? 8'hzz : q;

endmodule
