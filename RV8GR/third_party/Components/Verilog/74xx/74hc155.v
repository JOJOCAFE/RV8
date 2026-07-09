`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC155 DIP pinout
//
// - Function: dual 2-to-4 line decoder / 3-to-8 line decoder
// - Package verified: DIP16
// - Source: `../Source/74HC155_STMICROELECTRONICS_23044.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1C |
// | 2 | 1G |
// | 3 | B |
// | 4 | 1Y3 |
// | 5 | 1Y2 |
// | 6 | 1Y1 |
// | 7 | 1Y0 |
// | 8 | GND |
// | 9 | 2Y0 |
// | 10 | 2Y1 |
// | 11 | 2Y2 |
// | 12 | 2Y3 |
// | 13 | A |
// | 14 | 2G |
// | 15 | 2C |
// | 16 | VCC |
//


// 74HC155: Dual 2-line to 4-line decoder/demultiplexer (inverted outputs)

module ttl_74hc155 #(parameter BLOCKS_DIFFERENT = 2, BLOCK0 = 0, BLOCK1 = 1, WIDTH_OUT = 4,
                   WIDTH_IN = $clog2(WIDTH_OUT), DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable1C,
  input Enable1G_bar,
  input Enable2C_bar,
  input Enable2G_bar,
  input [WIDTH_IN-1:0] A,
  output [BLOCKS_DIFFERENT*WIDTH_OUT-1:0] Y_2D
);

//------------------------------------------------//
reg [WIDTH_OUT-1:0] computed [0:BLOCKS_DIFFERENT-1];
integer i;

always @(*)
begin
  for (i = 0; i < WIDTH_OUT; i++)
  begin
    if (Enable1C && !Enable1G_bar && i == A)
      computed[BLOCK0][i] = 1'b0;
    else
      computed[BLOCK0][i] = 1'b1;

    if (!Enable2C_bar && !Enable2G_bar && i == A)
      computed[BLOCK1][i] = 1'b0;
    else
      computed[BLOCK1][i] = 1'b1;
  end
end
//------------------------------------------------//

wire [BLOCKS_DIFFERENT*WIDTH_OUT-1:0] computed_pack_out;
generate
  genvar pk_idx;
  for (pk_idx = 0; pk_idx < BLOCKS_DIFFERENT; pk_idx = pk_idx + 1) begin: gen_pack
    assign computed_pack_out[WIDTH_OUT*pk_idx+:WIDTH_OUT] = computed[pk_idx][WIDTH_OUT-1:0];
  end
endgenerate
assign #(DELAY_RISE, DELAY_FALL) Y_2D = computed_pack_out;

endmodule
