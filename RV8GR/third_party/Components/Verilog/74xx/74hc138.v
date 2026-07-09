`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC138 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC138: https://www.ti.com/lit/ds/symlink/sn74hc138.pdf | N, 16-pin PDIP |
//
// ## 74HC138 - 3-Line to 8-Line Decoder/Demultiplexer, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | A |
// | 2 | B |
// | 3 | C |
// | 4 | /G2A |
// | 5 | /G2B |
// | 6 | G1 |
// | 7 | /Y7 |
// | 8 | GND |
// | 9 | /Y6 |
// | 10 | /Y5 |
// | 11 | /Y4 |
// | 12 | /Y3 |
// | 13 | /Y2 |
// | 14 | /Y1 |
// | 15 | /Y0 |
// | 16 | VCC |
//


// 74HC138: 3-line to 8-line decoder/demultiplexer, active-low outputs

module ttl_74hc138 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input A,
  input B,
  input C,
  input G1,
  input G2A_bar,
  input G2B_bar,
  output [7:0] Y_bar
);

wire enabled;
wire [2:0] sel;
reg [7:0] y_next;

assign enabled = G1 & ~G2A_bar & ~G2B_bar;
assign sel = {C, B, A};

always @* begin
  y_next = 8'hff;
  if (enabled) begin
    y_next[sel] = 1'b0;
  end
end

assign #(DELAY_RISE, DELAY_FALL) Y_bar = y_next;

endmodule
