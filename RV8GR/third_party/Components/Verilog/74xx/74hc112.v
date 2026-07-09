`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC112 DIP pinout
//
// - Function: dual JK flip-flop with set and reset, negative-edge trigger
// - Package verified: DIP16; Philips 74HC112N plastic dual in-line package SOT38-1
// - Source: `../Source/74HC112_PHILIPS_15529_DIPCHECK.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1CP |
// | 2 | 1K |
// | 3 | 1J |
// | 4 | 1SD |
// | 5 | 1Q |
// | 6 | 1Q_bar |
// | 7 | 2Q_bar |
// | 8 | GND |
// | 9 | 2Q |
// | 10 | 2SD |
// | 11 | 2J |
// | 12 | 2K |
// | 13 | 2CP |
// | 14 | 2RD |
// | 15 | 1RD |
// | 16 | VCC |
//
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
// - Datasheet prints complemented outputs with an overbar; `_bar` is used here for ASCII.
//


// Dual J-K flip-flop with set and clear; negative-edge-triggered

module ttl_74hc112 #(parameter BLOCKS = 2, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [BLOCKS-1:0] Preset_bar,
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
    always @(negedge Clk[i] or negedge Clear_bar[i] or negedge Preset_bar[i])
    begin
      if (!Clear_bar[i])
        Q_current[i] <= 1'b0;
      else if (!Preset_bar[i])
        Q_current[i] <= 1'b1;
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
