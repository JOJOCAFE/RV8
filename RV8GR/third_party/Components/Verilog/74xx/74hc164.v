`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC164 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC164: https://www.ti.com/lit/ds/symlink/sn74hc164.pdf | N, 14-pin PDIP |
//
// ## 74HC164 - 8-Bit Serial-In Parallel-Out Shift Register, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | A |
// | 2 | B |
// | 3 | QA |
// | 4 | QB |
// | 5 | QC |
// | 6 | QD |
// | 7 | GND |
// | 8 | CLK |
// | 9 | /CLR |
// | 10 | QE |
// | 11 | QF |
// | 12 | QG |
// | 13 | QH |
// | 14 | VCC |
//
//


// 74HC164: 8-bit serial-in parallel-out shift register with asynchronous clear

module ttl_74hc164 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input Clk,
  input A,
  input B,
  output [WIDTH-1:0] Q
);

//------------------------------------------------//
reg [WIDTH-1:0] Q_current;
wire Serial_in;

assign Serial_in = A & B;

always @(posedge Clk or negedge Clear_bar)
begin
  if (!Clear_bar)
    Q_current <= {WIDTH{1'b0}};
  else
    Q_current <= {Q_current[WIDTH-2:0], Serial_in};
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;

endmodule
