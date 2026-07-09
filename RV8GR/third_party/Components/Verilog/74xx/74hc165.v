`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC165 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC165: https://www.ti.com/lit/ds/symlink/sn74hc165.pdf | N, 16-pin PDIP |
//
// ## 74HC165 - 8-Bit Parallel-Load Shift Register, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /SH/LD |
// | 2 | CLK |
// | 3 | E |
// | 4 | F |
// | 5 | G |
// | 6 | H |
// | 7 | /QH |
// | 8 | GND |
// | 9 | QH |
// | 10 | SER |
// | 11 | A |
// | 12 | B |
// | 13 | C |
// | 14 | D |
// | 15 | CLK INH |
// | 16 | VCC |
//


// 74HC165: 8-bit parallel-load shift register

module ttl_74hc165 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input ShiftLoad_bar,
  input Clk,
  input ClkInhibit,
  input Serial,
  input [7:0] D,
  output QH,
  output QH_bar
);

reg [7:0] q;

always @(posedge Clk or negedge ShiftLoad_bar) begin
  if (!ShiftLoad_bar) begin
    q <= D;
  end else if (!ClkInhibit) begin
    q <= {q[6:0], Serial};
  end
end

assign #(DELAY_RISE, DELAY_FALL) QH = q[7];
assign #(DELAY_RISE, DELAY_FALL) QH_bar = ~q[7];

endmodule
