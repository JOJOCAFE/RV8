`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC193 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC193: https://www.ti.com/lit/ds/symlink/sn74hc193.pdf | N, 16-pin PDIP |
//
// ## 74HC193 - 4-Bit Synchronous Up/Down Binary Counter, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | B |
// | 2 | QB |
// | 3 | QA |
// | 4 | DOWN |
// | 5 | UP |
// | 6 | QC |
// | 7 | QD |
// | 8 | GND |
// | 9 | D |
// | 10 | C |
// | 11 | /LOAD |
// | 12 | /CO |
// | 13 | /BO |
// | 14 | CLR |
// | 15 | A |
// | 16 | VCC |
//


// 74HC193: 4-bit synchronous up/down binary counter

module ttl_74hc193 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear,
  input Load_bar,
  input Up,
  input Down,
  input [3:0] D,
  output [3:0] Q,
  output Carry_bar,
  output Borrow_bar
);

reg [3:0] q;

always @(posedge Up or posedge Clear or negedge Load_bar) begin
  if (Clear) q <= 4'h0;
  else if (!Load_bar) q <= D;
  else if (Down) q <= q + 4'h1;
end

always @(posedge Down or posedge Clear or negedge Load_bar) begin
  if (Clear) q <= 4'h0;
  else if (!Load_bar) q <= D;
  else if (Up) q <= q - 4'h1;
end

assign #(DELAY_RISE, DELAY_FALL) Q = q;
assign #(DELAY_RISE, DELAY_FALL) Carry_bar = ~(Up == 1'b0 && q == 4'hf);
assign #(DELAY_RISE, DELAY_FALL) Borrow_bar = ~(Down == 1'b0 && q == 4'h0);

endmodule
