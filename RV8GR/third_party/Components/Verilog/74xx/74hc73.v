`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC73 DIP pinout
//
// - Function: dual JK flip-flop with reset, negative-edge trigger
// - Package verified: DIP14; NXP 74HC73N plastic dual in-line package SOT27-1
// - Source: `../Source/74HC73_NXP_344664_DIPCHECK.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1CP |
// | 2 | 1R |
// | 3 | 1K |
// | 4 | VCC |
// | 5 | 2CP |
// | 6 | 2R |
// | 7 | 2J |
// | 8 | 2Q_bar |
// | 9 | 2Q |
// | 10 | 2K |
// | 11 | GND |
// | 12 | 1Q_bar |
// | 13 | 1Q |
// | 14 | 1J |
//
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
// - Datasheet prints complemented outputs with an overbar; `_bar` is used here for ASCII.
//


// 74HC73: Dual J-K flip-flop with clear; negative-edge-triggered

module ttl_74hc73 #(parameter BLOCKS = 2, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [BLOCKS-1:0] Clear_bar,
  input [BLOCKS-1:0] J,
  input [BLOCKS-1:0] K,
  input [BLOCKS-1:0] Clk,
  output [BLOCKS-1:0] Q,
  output [BLOCKS-1:0] Q_bar
);

//------------------------------------------------//
reg [BLOCKS-1:0] Q_current;

generate
  genvar i;
  for (i = 0; i < BLOCKS; i = i + 1)
  begin: gen_blocks
    always @(negedge Clk[i] or negedge Clear_bar[i])
    begin
      if (!Clear_bar[i])
        Q_current[i] <= 1'b0;
      else
      begin
        if (J[i] && !K[i] || !J[i] && K[i])
          Q_current[i] <= J[i];
        else if (J[i] && K[i])
          Q_current[i] <= !Q_current[i];
        else
          Q_current[i] <= Q_current[i];
      end
    end
  end
endgenerate
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;
assign #(DELAY_RISE, DELAY_FALL) Q_bar = ~Q_current;

endmodule
