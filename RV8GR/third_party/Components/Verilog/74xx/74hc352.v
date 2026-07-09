`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC352 DIP pinout
//
// - Function: dual 4-input multiplexer, inverting outputs
// - Package verified: DIP16
// - Source: `../Source/74HC352_STMICROELECTRONICS_23075.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1G |
// | 2 | B |
// | 3 | 1C3 |
// | 4 | 1C2 |
// | 5 | 1C1 |
// | 6 | 1C0 |
// | 7 | 1Y |
// | 8 | GND |
// | 9 | 2Y |
// | 10 | 2C0 |
// | 11 | 2C1 |
// | 12 | 2C2 |
// | 13 | 2C3 |
// | 14 | A |
// | 15 | 2G |
// | 16 | VCC |
//


// Dual 4-input multiplexer (inverted outputs)

module ttl_74hc352 #(parameter BLOCKS = 2, WIDTH_IN = 4, WIDTH_SELECT = $clog2(WIDTH_IN),
                   DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [BLOCKS-1:0] Enable_bar,
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
    if (!Enable_bar[i])
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
