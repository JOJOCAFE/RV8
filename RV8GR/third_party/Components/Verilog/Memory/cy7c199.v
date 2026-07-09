`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # CY7C199 DIP Pinout
//
// Manufacturer source: Infineon/Cypress CY7C199 datasheet:
// https://www.infineon.com/dgdl/Infineon-CY7C199_32K_x_8_Static_RAM-DataSheet-v07_00-EN.pdf
//
// Package checked: 28-pin DIP-compatible 32K x 8 SRAM pinout.
//
// Active-low pins are written with a leading slash.
//
// | Pin | Name |
// |---:|---|
// | 1 | A14 |
// | 2 | A12 |
// | 3 | A7 |
// | 4 | A6 |
// | 5 | A5 |
// | 6 | A4 |
// | 7 | A3 |
// | 8 | A2 |
// | 9 | A1 |
// | 10 | A0 |
// | 11 | I/O0 |
// | 12 | I/O1 |
// | 13 | I/O2 |
// | 14 | GND |
// | 15 | I/O3 |
// | 16 | I/O4 |
// | 17 | I/O5 |
// | 18 | I/O6 |
// | 19 | I/O7 |
// | 20 | /CE |
// | 21 | A10 |
// | 22 | /OE |
// | 23 | A11 |
// | 24 | A9 |
// | 25 | A8 |
// | 26 | A13 |
// | 27 | /WE |
// | 28 | VCC |
//


// CY7C199: 32K x 8 static RAM wrapper

module mem_cy7c199 #(parameter ADDR_WIDTH = 15, DATA_WIDTH = 8, INIT_FILE = "")
(
  input [ADDR_WIDTH-1:0] A,
  inout [DATA_WIDTH-1:0] DQ,
  input CE_bar,
  input OE_bar,
  input WE_bar
);

  mem_62256 #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .INIT_FILE(INIT_FILE)) ram (
    .A(A),
    .DQ(DQ),
    .CE_bar(CE_bar),
    .OE_bar(OE_bar),
    .WE_bar(WE_bar)
  );
endmodule
