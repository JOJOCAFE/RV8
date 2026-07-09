`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # SST39SF010A DIP Pinout
//
// Manufacturer source: Microchip SST39SF010A/SST39SF020A/SST39SF040 datasheet:
// https://ww1.microchip.com/downloads/en/DeviceDoc/SST39SF010A-SST39SF020A-SST39SF040-Data-Sheet-DS20005022.pdf
//
// Package checked: 32-pin PDIP flash package. Pins that are address pins on
// larger family members but not used by the 1-Mbit SST39SF010A are listed as NC.
//
// Active-low pins are written with a leading slash.
//
// | Pin | Name |
// |---:|---|
// | 1 | NC |
// | 2 | A16 |
// | 3 | A15 |
// | 4 | A12 |
// | 5 | A7 |
// | 6 | A6 |
// | 7 | A5 |
// | 8 | A4 |
// | 9 | A3 |
// | 10 | A2 |
// | 11 | A1 |
// | 12 | A0 |
// | 13 | DQ0 |
// | 14 | DQ1 |
// | 15 | DQ2 |
// | 16 | VSS |
// | 17 | DQ3 |
// | 18 | DQ4 |
// | 19 | DQ5 |
// | 20 | DQ6 |
// | 21 | DQ7 |
// | 22 | /CE |
// | 23 | A10 |
// | 24 | /OE |
// | 25 | A11 |
// | 26 | A9 |
// | 27 | A8 |
// | 28 | A13 |
// | 29 | A14 |
// | 30 | NC |
// | 31 | /WE |
// | 32 | VDD |
//


// SST39SF010A: 128K x 8 flash EEPROM, simulation model

module mem_sst39sf010a #(parameter ADDR_WIDTH = 17, DATA_WIDTH = 8, INIT_FILE = "")
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
  assign write_enable = !CE_bar && OE_bar && !WE_bar;
  assign DQ = read_enable ? memory[A] : {DATA_WIDTH{1'bz}};

  always @(negedge WE_bar) begin
    if (write_enable)
      memory[A] <= DQ;
  end

  initial begin
    if (INIT_FILE != "")
      $readmemh(INIT_FILE, memory);
  end
endmodule
