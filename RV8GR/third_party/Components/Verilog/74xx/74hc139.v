`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC139 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC139: https://www.ti.com/lit/ds/symlink/sn74hc139.pdf | N, 16-pin PDIP |
//
// ## 74HC139 - Dual 2-Line to 4-Line Decoder/Demultiplexer, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /1G |
// | 2 | 1A |
// | 3 | 1B |
// | 4 | /1Y0 |
// | 5 | /1Y1 |
// | 6 | /1Y2 |
// | 7 | /1Y3 |
// | 8 | GND |
// | 9 | /2Y3 |
// | 10 | /2Y2 |
// | 11 | /2Y1 |
// | 12 | /2Y0 |
// | 13 | 2B |
// | 14 | 2A |
// | 15 | /2G |
// | 16 | VCC |
//


// 74HC139: dual 2-line to 4-line decoder/demultiplexer, active-low outputs

module ttl_74hc139 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] Enable_bar,
  input [1:0] A,
  input [1:0] B,
  output [3:0] Y1_bar,
  output [3:0] Y2_bar
);

reg [3:0] y1_next;
reg [3:0] y2_next;

always @* begin
  y1_next = 4'hf;
  y2_next = 4'hf;
  if (!Enable_bar[0]) y1_next[{B[0], A[0]}] = 1'b0;
  if (!Enable_bar[1]) y2_next[{B[1], A[1]}] = 1'b0;
end

assign #(DELAY_RISE, DELAY_FALL) Y1_bar = y1_next;
assign #(DELAY_RISE, DELAY_FALL) Y2_bar = y2_next;

endmodule
