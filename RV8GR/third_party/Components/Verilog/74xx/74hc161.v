`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC161 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC161: https://www.ti.com/lit/ds/symlink/sn74hc161.pdf | N, 16-pin PDIP |
//
// ## 74HC161 - 4-Bit Binary Counter, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /CLR |
// | 2 | CLK |
// | 3 | A |
// | 4 | B |
// | 5 | C |
// | 6 | D |
// | 7 | ENP |
// | 8 | GND |
// | 9 | /LOAD |
// | 10 | ENT |
// | 11 | QD |
// | 12 | QC |
// | 13 | QB |
// | 14 | QA |
// | 15 | RCO |
// | 16 | VCC |
//
//


// 74HC161: 4-bit binary counter with parallel load and asynchronous clear

module ttl_74hc161 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
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
reg [WIDTH-1:0] Q_current;
wire [WIDTH-1:0] Q_next;
wire RCO_current;

assign Q_next = Q_current + {{WIDTH-1{1'b0}}, 1'b1};

always @(posedge Clk or negedge Clear_bar)
begin
  if (!Clear_bar)
    Q_current <= {WIDTH{1'b0}};
  else if (!Load_bar)
    Q_current <= D;
  else if (ENT && ENP)
    Q_current <= Q_next;
end

assign RCO_current = ENT && (&Q_current);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) RCO = RCO_current;
assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;

endmodule
