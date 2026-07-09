`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 62256 DIP Pinout
//
// Manufacturer source: Alliance Memory AS6C62256 datasheet:
// https://www.alliancememory.com/wp-content/uploads/pdf/AS6C62256.pdf
//
// Package checked: 28-pin PDIP-compatible 32K x 8 SRAM pinout.
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


// 62256: 32K x 8 static RAM, simulation model

module mem_62256 #(parameter ADDR_WIDTH = 15, DATA_WIDTH = 8, INIT_FILE = "")
(
  input [ADDR_WIDTH-1:0] A,
  inout [DATA_WIDTH-1:0] DQ,
  input CE_bar,
  input OE_bar,
  input WE_bar
);

  reg [DATA_WIDTH-1:0] memory [0:(1 << ADDR_WIDTH)-1];
  wire read_enable;
  wire write_enable;

  assign read_enable = !CE_bar && !OE_bar && WE_bar;
  assign write_enable = !CE_bar && !WE_bar;
  assign DQ = read_enable ? memory[A] : {DATA_WIDTH{1'bz}};

  always @(*) begin
    if (write_enable)
      memory[A] = DQ;
  end

  initial begin
    if (INIT_FILE != "")
      $readmemh(INIT_FILE, memory);
  end
endmodule
