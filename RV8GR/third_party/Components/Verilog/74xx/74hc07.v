`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC07 DIP pinout
//
// - Function: hex buffer with open-drain outputs
// - Package verified: DIP14 / PDIP14
// - Source: `../Source/74HC07_STMICROELECTRONICS_23210.pdf`
//
// | Pin | Name |
// | --- | --- |
// | 1 | 1A |
// | 2 | 1Y |
// | 3 | 2A |
// | 4 | 2Y |
// | 5 | 3A |
// | 6 | 3Y |
// | 7 | GND |
// | 8 | 4Y |
// | 9 | 4A |
// | 10 | 5Y |
// | 11 | 5A |
// | 12 | 6Y |
// | 13 | 6A |
// | 14 | VCC |
//


// Hex buffer/driver (OC)

module ttl_74hc07 #(parameter BLOCKS = 6, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [BLOCKS-1:0] A,
  output [BLOCKS-1:0] Y
);

//------------------------------------------------//
reg [BLOCKS-1:0] computed;

always @(*)
begin
  computed = A;
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = computed;

endmodule
