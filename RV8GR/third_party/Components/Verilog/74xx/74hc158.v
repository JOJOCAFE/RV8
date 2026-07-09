`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC158 DIP pinout
//
// - Function: quad 2-input multiplexer, inverting outputs
// - Package verified: DIP16 / PDIP16; TI SN74HC158N N package, 300-mil DIP; pin numbers shared with D/J/N/W packages
// - Source: `../Source/74HC158_TI_27895_SN74HC158N_DIPVERIFY.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | S |
// | 2 | 1I0 |
// | 3 | 1I1 |
// | 4 | 1Y |
// | 5 | 2I0 |
// | 6 | 2I1 |
// | 7 | 2Y |
// | 8 | GND |
// | 9 | 3Y |
// | 10 | 3I1 |
// | 11 | 3I0 |
// | 12 | 4Y |
// | 13 | 4I1 |
// | 14 | 4I0 |
// | 15 | E |
// | 16 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// Quad 2-input multiplexer (inverted outputs)

module ttl_74hc158 #(parameter BLOCKS = 4, WIDTH_IN = 2, WIDTH_SELECT = $clog2(WIDTH_IN),
                   DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input [WIDTH_SELECT-1:0] Select,
  input [BLOCKS*WIDTH_IN-1:0] A_2D,
  output [BLOCKS-1:0] Y_bar
);

//------------------------------------------------//
wire [WIDTH_IN-1:0] A [0:BLOCKS-1];
reg [BLOCKS-1:0] computed;
integer i;

always @(*)
begin
  for (i = 0; i < BLOCKS; i++)
  begin
    if (!Enable_bar)
      computed[i] = A[i][Select];
    else
      computed[i] = 1'b0;
  end
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
assign #(DELAY_RISE, DELAY_FALL) Y_bar = ~computed;

endmodule
