`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC148 DIP pinout
//
// - Function: 8-to-3 line priority encoder
// - Package verified: DIP16
// - Source: `../Source/74HC148_STMICROELECTRONICS_23041.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | I3 |
// | 2 | I4 |
// | 3 | I5 |
// | 4 | I6 |
// | 5 | EI |
// | 6 | A2 |
// | 7 | A1 |
// | 8 | GND |
// | 9 | A0 |
// | 10 | I7 |
// | 11 | I0 |
// | 12 | I1 |
// | 13 | I2 |
// | 14 | GS |
// | 15 | EO |
// | 16 | VCC |
//


// 74HC148: 8-line to 3-line priority encoder

module ttl_74hc148 #(parameter WIDTH_IN = 8, WIDTH_OUT = 3, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input EI_bar,
  input [WIDTH_IN-1:0] A_bar,
  output EO_bar,
  output GS_bar,
  output [WIDTH_OUT-1:0] Y_bar
);

//------------------------------------------------//
reg EO_computed;
reg GS_computed;
reg [WIDTH_OUT-1:0] Y_computed;

always @(*)
begin
  if (EI_bar)
  begin
    // equal to EI (inverted)
    EO_computed = 0;
    // equal to EI (inverted)
    GS_computed = 0;

    // lowest priority (inverted)
    Y_computed = 3'b000;
  end
  else
  begin
    // normally opposite of EI (inverted)
    EO_computed = 0;
    // normally equal to EI (inverted)
    GS_computed = 1;

    casez (A_bar)
      8'b0???????: Y_computed = 3'b111;
      8'b10??????: Y_computed = 3'b110;
      8'b110?????: Y_computed = 3'b101;
      8'b1110????: Y_computed = 3'b100;
      8'b11110???: Y_computed = 3'b011;
      8'b111110??: Y_computed = 3'b010;
      8'b1111110?: Y_computed = 3'b001;
      8'b11111110: Y_computed = 3'b000;
      8'b11111111:
      begin
        // exception: equal to EI (inverted)
        EO_computed = 1;
        // exception: opposite of EI (inverted)
        GS_computed = 0;

        // lowest priority (inverted)
        Y_computed = 3'b000;
      end
      default: Y_computed = 3'b000;
    endcase
  end
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) EO_bar = ~EO_computed;
assign #(DELAY_RISE, DELAY_FALL) GS_bar = ~GS_computed;
assign #(DELAY_RISE, DELAY_FALL) Y_bar = ~Y_computed;

endmodule
