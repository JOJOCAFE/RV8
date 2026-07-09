`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC74 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC74: https://www.ti.com/lit/ds/symlink/sn74hc74.pdf | N, 14-pin PDIP |
//
// ## 74HC74 - Dual D-Type Flip-Flop, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /1CLR |
// | 2 | 1D |
// | 3 | 1CLK |
// | 4 | /1PRE |
// | 5 | 1Q |
// | 6 | /1Q |
// | 7 | GND |
// | 8 | /2Q |
// | 9 | 2Q |
// | 10 | /2PRE |
// | 11 | 2CLK |
// | 12 | 2D |
// | 13 | /2CLR |
// | 14 | VCC |
//
//


// 74HC74: dual D flip-flop with asynchronous preset and clear

module ttl_74hc74 #(parameter BLOCKS = 2, DELAY_RISE = 0, DELAY_FALL = 0, SAMPLE_DELAY = 0)
(
  input [BLOCKS-1:0] Preset_bar,
  input [BLOCKS-1:0] Clear_bar,
  input [BLOCKS-1:0] D,
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
    always @(posedge Clk[i] or negedge Preset_bar[i] or negedge Clear_bar[i])
    begin
      if (SAMPLE_DELAY != 0 && Clk[i])
        #SAMPLE_DELAY;
      if (!Clear_bar[i])
        Q_current[i] <= 1'b0;
      else if (!Preset_bar[i])
        Q_current[i] <= 1'b1;
      else
        Q_current[i] <= D[i];
    end
  end
endgenerate
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;
assign #(DELAY_RISE, DELAY_FALL) Q_bar = ~Q_current;

endmodule
