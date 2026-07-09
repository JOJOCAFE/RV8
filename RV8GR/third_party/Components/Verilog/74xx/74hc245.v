`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC245 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC245: https://www.ti.com/lit/ds/symlink/sn74hc245.pdf | N, 20-pin PDIP |
//
// ## 74HC245 - Octal Bus Transceiver, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | DIR |
// | 2 | A1 |
// | 3 | A2 |
// | 4 | A3 |
// | 5 | A4 |
// | 6 | A5 |
// | 7 | A6 |
// | 8 | A7 |
// | 9 | A8 |
// | 10 | GND |
// | 11 | B8 |
// | 12 | B7 |
// | 13 | B6 |
// | 14 | B5 |
// | 15 | B4 |
// | 16 | B3 |
// | 17 | B2 |
// | 18 | B1 |
// | 19 | /OE |
// | 20 | VCC |
//
//


// 74HC245: octal bus transceiver with 3-state outputs

module ttl_74hc245 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input DIR,
  inout [WIDTH-1:0] A,
  inout [WIDTH-1:0] B
);

//------------------------------------------------//
wire [WIDTH-1:0] A_drive;
wire [WIDTH-1:0] B_drive;

assign A_drive = (!OE_bar && !DIR) ? B : {WIDTH{1'bz}};
assign B_drive = (!OE_bar &&  DIR) ? A : {WIDTH{1'bz}};
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) A = A_drive;
assign #(DELAY_RISE, DELAY_FALL) B = B_drive;

endmodule
