`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC20 DIP pinout
//
// - Function: dual 4-input NAND gate
// - Package verified: DIP14 / PDIP14; TI SN74HC20N PDIP N package; pin numbers shared with D/DB/J/N/NS/PW/W packages
// - Source: `../Source/74HC20_TI_27902_SN74HC20N_DIPVERIFY.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1A |
// | 2 | 1B |
// | 3 | NC |
// | 4 | 1C |
// | 5 | 1D |
// | 6 | 1Y |
// | 7 | GND |
// | 8 | 2Y |
// | 9 | 2A |
// | 10 | 2B |
// | 11 | NC |
// | 12 | 2C |
// | 13 | 2D |
// | 14 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// 74HC20: Dual 4-input NAND gate

module ttl_74hc20 #(parameter BLOCKS = 2, WIDTH_IN = 4, DELAY_RISE = 0, DELAY_FALL = 0)
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
    computed[i] = ~(&A[i]);
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
