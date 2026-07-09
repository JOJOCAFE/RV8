`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC166 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC166: https://www.ti.com/lit/ds/symlink/sn74hc166.pdf | N, 16-pin PDIP |
//
// ## 74HC166 - 8-Bit Parallel-Load Shift Register, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | SER |
// | 2 | A |
// | 3 | B |
// | 4 | C |
// | 5 | D |
// | 6 | CLK INH |
// | 7 | CLK |
// | 8 | GND |
// | 9 | /CLR |
// | 10 | H |
// | 11 | G |
// | 12 | F |
// | 13 | E |
// | 14 | /SH/LD |
// | 15 | QH |
// | 16 | VCC |
//


// 74HC166: 8-bit parallel-load shift register with serial output

module ttl_74hc166 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input ShiftLoad_bar,
  input Clk,
  input ClkInhibit,
  input Serial,
  input [7:0] D,
  output QH
);

reg [7:0] q;

always @(posedge Clk or negedge Clear_bar) begin
  if (!Clear_bar) begin
    q <= 8'h00;
  end else if (!ClkInhibit) begin
    if (!ShiftLoad_bar) begin
      q <= D;
    end else begin
      q <= {q[6:0], Serial};
    end
  end
end

assign #(DELAY_RISE, DELAY_FALL) QH = q[7];

endmodule
