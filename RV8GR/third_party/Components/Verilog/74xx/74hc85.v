`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC85 DIP pinout
//
// - Function: 4-bit magnitude comparator
// - Package verified: DIP16; Motorola MC74HC85N N suffix plastic package / plastic DIP
// - Source: `../Source/74HC85_MOTOROLA_4353_MC74HC85N_DIPVERIFY.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | B3 |
// | 2 | IA_LT_B |
// | 3 | IA_EQ_B |
// | 4 | IA_GT_B |
// | 5 | QA_GT_B |
// | 6 | QA_EQ_B |
// | 7 | QA_LT_B |
// | 8 | GND |
// | 9 | B0 |
// | 10 | A0 |
// | 11 | B1 |
// | 12 | A1 |
// | 13 | A2 |
// | 14 | B2 |
// | 15 | A3 |
// | 16 | VCC |
//
// Notes:
// - DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
// - Names use ASCII LT/EQ/GT for the datasheet comparison symbols.
//


// 74HC85: 4-bit magnitude comparator

module ttl_74hc85 #(parameter WIDTH_IN = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [WIDTH_IN-1:0] A,
  input [WIDTH_IN-1:0] B,
  input ALess_in,
  input Equal_in,
  input AGreater_in,
  output ALess_out,
  output Equal_out,
  output AGreater_out
);

//------------------------------------------------//
reg ALess_computed;
reg Equal_computed;
reg AGreater_computed;

always @(*)
begin
  if (A == B && !Equal_in && ALess_in == AGreater_in)
  begin
    // abnormal inputs used in parallel expansion configuration
    Equal_computed = 1'b0;
    ALess_computed = !ALess_in;
    AGreater_computed = !AGreater_in;
  end
  else
  begin
    // normal inputs
    Equal_computed = A == B && Equal_in;
    ALess_computed = !Equal_computed && {A, 1'b0} < {B, ALess_in};
    AGreater_computed = !Equal_computed && {A, AGreater_in} > {B, 1'b0};
  end
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) ALess_out = ALess_computed;
assign #(DELAY_RISE, DELAY_FALL) Equal_out = Equal_computed;
assign #(DELAY_RISE, DELAY_FALL) AGreater_out = AGreater_computed;

endmodule
