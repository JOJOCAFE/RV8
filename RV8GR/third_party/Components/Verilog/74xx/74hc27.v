`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC27 DIP pinout
//
// - Function: triple 3-input NOR gate
// - Package verified: DIP14; NXP 74HC27N plastic dual in-line package SOT27-1
// - Source: `../Source/74HC27_NXP_344450_DIPCHECK.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1A |
// | 2 | 1B |
// | 3 | 2A |
// | 4 | 2B |
// | 5 | 2C |
// | 6 | 2Y |
// | 7 | GND |
// | 8 | 3Y |
// | 9 | 3A |
// | 10 | 3B |
// | 11 | 3C |
// | 12 | 1Y |
// | 13 | 1C |
// | 14 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// 74HC27: Triple 3-input NOR gate

module ttl_74hc27 #(parameter BLOCKS = 3, WIDTH_IN = 3, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [BLOCKS*WIDTH_IN-1:0] A_2D,
  output [BLOCKS-1:0] Y
);

//------------------------------------------------//
wire [WIDTH_IN-1:0] A [0:BLOCKS-1];
reg [BLOCKS-1:0] computed;
integer i;

always @(*)
begin
  for (i = 0; i < BLOCKS; i++)
    computed[i] = ~(|A[i]);
end
//------------------------------------------------//

wire [BLOCKS*WIDTH_IN-1:0] A_pack_in;
assign A_pack_in = A_2D;
generate
  genvar unpk_idx;
  for (unpk_idx = 0; unpk_idx < BLOCKS; unpk_idx = unpk_idx + 1) begin: gen_unpack
    assign A[unpk_idx][WIDTH_IN-1:0] = A_pack_in[WIDTH_IN*unpk_idx+:WIDTH_IN];
  end
endgenerate
assign #(DELAY_RISE, DELAY_FALL) Y = computed;

endmodule
