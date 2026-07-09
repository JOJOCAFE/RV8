`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC30 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments CD74HC30: https://www.ti.com/lit/ds/symlink/cd74hc30.pdf | E, 14-pin PDIP |
//
// ## 74HC30 - Single 8-Input NAND Gate, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | A |
// | 2 | B |
// | 3 | C |
// | 4 | D |
// | 5 | E |
// | 6 | F |
// | 7 | GND |
// | 8 | Y |
// | 9 | NC |
// | 10 | NC |
// | 11 | G |
// | 12 | H |
// | 13 | NC |
// | 14 | VCC |
//


// 74HC30: single 8-input NAND gate

module ttl_74hc30 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [7:0] A,
  output Y
);

wire Y_computed;

assign Y_computed = ~&A;

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
