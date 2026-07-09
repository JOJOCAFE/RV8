`timescale 1ns/1ps

module tb_memory_smoke;
  integer failures = 0;

  task check;
    input condition;
    input [255:0] message;
    begin
      if (!condition) begin
        $display("FAIL: %0s", message);
        failures = failures + 1;
      end
    end
  endtask

  reg [14:0] a15;
  reg [16:0] a17;
  wire [7:0] eeprom_dq;
  wire [7:0] flash_dq;
  wire [7:0] ram_dq;
  reg [7:0] eeprom_drive;
  reg [7:0] flash_drive;
  reg [7:0] ram_drive;
  reg eeprom_drive_en;
  reg flash_drive_en;
  reg ram_drive_en;
  reg ce_n;
  reg oe_n;
  reg we_n;

  assign eeprom_dq = eeprom_drive_en ? eeprom_drive : 8'hzz;
  assign flash_dq = flash_drive_en ? flash_drive : 8'hzz;
  assign ram_dq = ram_drive_en ? ram_drive : 8'hzz;

  mem_at28c256 u_eeprom(.A(a15), .DQ(eeprom_dq), .CE_bar(ce_n), .OE_bar(oe_n), .WE_bar(we_n));
  mem_sst39sf010a u_flash(.A(a17), .DQ(flash_dq), .CE_bar(ce_n), .OE_bar(oe_n), .WE_bar(we_n));
  mem_62256 u_ram(.A(a15), .DQ(ram_dq), .CE_bar(ce_n), .OE_bar(oe_n), .WE_bar(we_n));

  initial begin
    ce_n = 1'b1;
    oe_n = 1'b1;
    we_n = 1'b1;
    eeprom_drive_en = 1'b0;
    flash_drive_en = 1'b0;
    ram_drive_en = 1'b0;
    a15 = 15'h0123;
    a17 = 17'h10123;

    ce_n = 1'b0;
    oe_n = 1'b1;
    eeprom_drive = 8'ha5;
    eeprom_drive_en = 1'b1;
    #1 we_n = 1'b0; #1 we_n = 1'b1;
    eeprom_drive_en = 1'b0;
    oe_n = 1'b0;
    #1;
    check(eeprom_dq == 8'ha5, "AT28C256 write/read");

    oe_n = 1'b1;
    flash_drive = 8'h3c;
    flash_drive_en = 1'b1;
    #1 we_n = 1'b0; #1 we_n = 1'b1;
    flash_drive_en = 1'b0;
    oe_n = 1'b0;
    #1;
    check(flash_dq == 8'h3c, "SST39SF010A write/read");

    oe_n = 1'b1;
    ram_drive = 8'h5a;
    ram_drive_en = 1'b1;
    #1 we_n = 1'b0; #1 we_n = 1'b1;
    ram_drive_en = 1'b0;
    oe_n = 1'b0;
    #1;
    check(ram_dq == 8'h5a, "62256 write/read");

    ce_n = 1'b1;
    #1;
    check(eeprom_dq === 8'hzz && flash_dq === 8'hzz && ram_dq === 8'hzz, "disabled high-Z");

    if (failures == 0) begin
      $display("MEMORY SMOKE TEST PASSED");
      $finish;
    end

    $display("MEMORY SMOKE TEST FAILED: %0d failures", failures);
    $fatal(1);
  end
endmodule
