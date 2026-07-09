`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC4078 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | STMicroelectronics M74HC4078: `Components/Source/M74HC4078.PDF` | DIP, 14-pin |
//
// ## 74HC4078 - 8-Input NOR/OR Gate, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | Y |
// | 2 | A |
// | 3 | B |
// | 4 | C |
// | 5 | D |
// | 6 | NC |
// | 7 | GND |
// | 8 | NC |
// | 9 | E |
// | 10 | F |
// | 11 | G |
// | 12 | H |
// | 13 | X |
// | 14 | VCC |
//
// `X` is the NOR output and `Y` is the OR output.
//


// 74HC4078: 8-input NOR/OR gate

module ttl_74hc4078 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [7:0] A,
  output X,
  output Y
);

wire any_high;

assign any_high = |A;

assign #(DELAY_RISE, DELAY_FALL) X = ~any_high;
assign #(DELAY_RISE, DELAY_FALL) Y = any_high;

endmodule
