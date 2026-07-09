`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC163 DIP pinout
//
// - Function: presettable synchronous 4-bit binary counter, synchronous reset
// - Package verified: DIP16 / PDIP16; TI SN74HC163N PDIP N package; pin numbers shared with D/DB/J/N/NS/PW/W packages
// - Source: `../Source/74HC163_TI_27897_SN74HC163N_DIPVERIFY.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | MR |
// | 2 | CP |
// | 3 | D0 |
// | 4 | D1 |
// | 5 | D2 |
// | 6 | D3 |
// | 7 | CEP |
// | 8 | GND |
// | 9 | PE |
// | 10 | CET |
// | 11 | Q3 |
// | 12 | Q2 |
// | 13 | Q1 |
// | 14 | Q0 |
// | 15 | TC |
// | 16 | VCC |
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
//


// 4-bit modulo 16 binary counter with parallel load, synchronous clear

module ttl_74hc163 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input Load_bar,
  input ENT,
  input ENP,
  input [WIDTH-1:0] D,
  input Clk,
  output RCO,
  output [WIDTH-1:0] Q
);

//------------------------------------------------//
wire RCO_current;
reg [WIDTH-1:0] Q_current;
wire [WIDTH-1:0] Q_next;

assign Q_next = Q_current + 1;

always @(posedge Clk)
begin
  if (!Clear_bar)
  begin
    Q_current <= {WIDTH{1'b0}};
  end
  else
  begin
    if (!Load_bar)
    begin
      Q_current <= D;
    end

    if (Load_bar && ENT && ENP)
    begin
      Q_current <= Q_next;
    end
  end
end

// output
assign RCO_current = ENT && (&Q_current);

//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) RCO = RCO_current;
assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;

endmodule
