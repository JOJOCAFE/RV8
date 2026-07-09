`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC595 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC595: https://www.ti.com/lit/ds/symlink/sn74hc595.pdf | N, 16-pin PDIP |
//
// ## 74HC595 - 8-Bit Serial-In Shift Register With Output Register, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | QB |
// | 2 | QC |
// | 3 | QD |
// | 4 | QE |
// | 5 | QF |
// | 6 | QG |
// | 7 | QH |
// | 8 | GND |
// | 9 | QH' |
// | 10 | /SRCLR |
// | 11 | SRCLK |
// | 12 | RCLK |
// | 13 | /OE |
// | 14 | SER |
// | 15 | QA |
// | 16 | VCC |
//


// 74HC595: 8-bit serial-in shift register with output storage register

module ttl_74hc595 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input SER,
  input SRCLK,
  input RCLK,
  input SRCLR_bar,
  input OE_bar,
  output [7:0] Q,
  output QH_prime
);

reg [7:0] shift_q;
reg [7:0] store_q;

always @(posedge SRCLK or negedge SRCLR_bar) begin
  if (!SRCLR_bar) shift_q <= 8'h00;
  else shift_q <= {shift_q[6:0], SER};
end

always @(posedge RCLK) begin
  store_q <= shift_q;
end

assign #(DELAY_RISE, DELAY_FALL) Q = OE_bar ? 8'hzz : store_q;
assign #(DELAY_RISE, DELAY_FALL) QH_prime = shift_q[7];

endmodule
