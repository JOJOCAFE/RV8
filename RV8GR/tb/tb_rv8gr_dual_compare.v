// RV8GR dual-version architectural comparison.
// Compares behavioral rv8gr_cpu.v against structural rv8gr_chip_level.v.
`timescale 1ns/1ps

module tb_rv8gr_dual_compare;
  reg clk;
  reg rst_n;
  reg irq_n;
  wire behavioral_halted;
  integer i;
  integer cycles;
  integer behavior_events;
  integer chip_events;
  reg [1023:0] dumpfile;

  rv8gr_cpu behavioral(.clk(clk), .rst_n(rst_n), .irq_n(irq_n), .halted(behavioral_halted));
  rv8gr_chip_level chip();

  always #500 clk = ~clk;

  wire [15:0] chip_pc = {
    chip.n_PC15, chip.n_PC14, chip.n_PC13, chip.n_PC12,
    chip.n_PC11, chip.n_PC10, chip.n_PC9, chip.n_PC8,
    chip.n_PC7, chip.n_PC6, chip.n_PC5, chip.n_PC4,
    chip.n_PC3, chip.n_PC2, chip.n_PC1, chip.n_PC0
  };

  wire [7:0] chip_ac = {
    chip.n_AC7, chip.n_AC6, chip.n_AC5, chip.n_AC4,
    chip.n_AC3, chip.n_AC2, chip.n_AC1, chip.n_AC0
  };

  wire [7:0] chip_pg = {
    chip.n_PG7, chip.n_PG6, chip.n_PG5, chip.n_PG4,
    chip.n_PG3, chip.n_PG2, chip.n_PG1, chip.n_PG0
  };

  wire [7:0] chip_dp = {
    chip.n_DP7, chip.n_DP6, chip.n_DP5, chip.n_DP4,
    chip.n_DP3, chip.n_DP2, chip.n_DP1, chip.n_DP0
  };

  wire [2:0] chip_phase = {chip.n_T2, chip.n_T1, chip.n_T0};

  reg expected_valid [0:65535];
  reg [7:0] expected_ac [0:65535];
  reg expected_z [0:65535];
  reg expected_ie [0:65535];
  reg expected_irq_ff [0:65535];
  reg [7:0] expected_pg [0:65535];
  reg [7:0] expected_dp [0:65535];
  reg chip_seen [0:65535];

  task automatic load_rom_byte(input [14:0] addr, input [7:0] value);
    begin
      behavioral.rom[addr] = value;
      chip.ROM1.memory[addr] = value;
    end
  endtask

  task automatic load_common_program;
    begin
      load_rom_byte(15'h0000, 8'h30); load_rom_byte(15'h0001, 8'h00);
      load_rom_byte(15'h0002, 8'h02); load_rom_byte(15'h0003, 8'h08);
      load_rom_byte(15'h0004, 8'h01); load_rom_byte(15'h0005, 8'h04);
      load_rom_byte(15'h0008, 8'h30); load_rom_byte(15'h0009, 8'h05);
      load_rom_byte(15'h000A, 8'h82); load_rom_byte(15'h000B, 8'h10);
      load_rom_byte(15'h000C, 8'h01); load_rom_byte(15'h000D, 8'h0C);
      load_rom_byte(15'h0010, 8'h10); load_rom_byte(15'h0011, 8'h03);
      load_rom_byte(15'h0012, 8'h90); load_rom_byte(15'h0013, 8'h08);
      load_rom_byte(15'h0014, 8'h70); load_rom_byte(15'h0015, 8'hAA);
      load_rom_byte(15'h0016, 8'h04); load_rom_byte(15'h0017, 8'h00);
      load_rom_byte(15'h0018, 8'h30); load_rom_byte(15'h0019, 8'h00);
      load_rom_byte(15'h001A, 8'h38); load_rom_byte(15'h001B, 8'h00);
      load_rom_byte(15'h001C, 8'h90); load_rom_byte(15'h001D, 8'hAA);
      load_rom_byte(15'h001E, 8'h02); load_rom_byte(15'h001F, 8'h22);
      load_rom_byte(15'h0020, 8'h01); load_rom_byte(15'h0021, 8'h20);
      load_rom_byte(15'h0022, 8'h30); load_rom_byte(15'h0023, 8'h55);
      load_rom_byte(15'h0024, 8'h04); load_rom_byte(15'h0025, 8'h01);
      load_rom_byte(15'h0026, 8'h18); load_rom_byte(15'h0027, 8'h01);
      load_rom_byte(15'h0028, 8'h98); load_rom_byte(15'h0029, 8'h00);
      load_rom_byte(15'h002A, 8'h02); load_rom_byte(15'h002B, 8'h2E);
      load_rom_byte(15'h002C, 8'h01); load_rom_byte(15'h002D, 8'h2C);
      load_rom_byte(15'h002E, 8'h30); load_rom_byte(15'h002F, 8'hFF);
      load_rom_byte(15'h0030, 8'h04); load_rom_byte(15'h0031, 8'h02);
      load_rom_byte(15'h0032, 8'h78); load_rom_byte(15'h0033, 8'h02);
      load_rom_byte(15'h0034, 8'h02); load_rom_byte(15'h0035, 8'h38);
      load_rom_byte(15'h0036, 8'h01); load_rom_byte(15'h0037, 8'h36);
      load_rom_byte(15'h0038, 8'h20); load_rom_byte(15'h0039, 8'h10);
      load_rom_byte(15'h003A, 8'h01); load_rom_byte(15'h003B, 8'h00);
      load_rom_byte(15'h1000, 8'h20); load_rom_byte(15'h1001, 8'h7F);
      load_rom_byte(15'h1002, 8'h01); load_rom_byte(15'h1003, 8'h00);
      load_rom_byte(15'h7F00, 8'h20); load_rom_byte(15'h7F01, 8'h00);
      load_rom_byte(15'h7F02, 8'h01); load_rom_byte(15'h7F03, 8'h40);
      load_rom_byte(15'h0040, 8'h30); load_rom_byte(15'h0041, 8'h00);
      load_rom_byte(15'h0042, 8'h04); load_rom_byte(15'h0043, 8'h04);
      load_rom_byte(15'h0044, 8'h28); load_rom_byte(15'h0045, 8'h04);
      load_rom_byte(15'h0046, 8'h20); load_rom_byte(15'h0047, 8'h00);
      load_rom_byte(15'h0048, 8'h30); load_rom_byte(15'h0049, 8'h5E);
      load_rom_byte(15'h004A, 8'h04); load_rom_byte(15'h004B, 8'h07);
      load_rom_byte(15'h004C, 8'h01); load_rom_byte(15'h004D, 8'h90);
      load_rom_byte(15'h005E, 8'h38); load_rom_byte(15'h005F, 8'h05);
      load_rom_byte(15'h0060, 8'h90); load_rom_byte(15'h0061, 8'h42);
      load_rom_byte(15'h0062, 8'h02); load_rom_byte(15'h0063, 8'h66);
      load_rom_byte(15'h0064, 8'h01); load_rom_byte(15'h0065, 8'h64);
      // SETDP cross-page memory checks before final pass.
      load_rom_byte(15'h0066, 8'h40); load_rom_byte(15'h0067, 8'h90); // SETDP $90
      load_rom_byte(15'h0068, 8'h30); load_rom_byte(15'h0069, 8'hA5); // LI $A5
      load_rom_byte(15'h006A, 8'h04); load_rom_byte(15'h006B, 8'h00); // SB $00 -> RAM[$9000]
      load_rom_byte(15'h006C, 8'h30); load_rom_byte(15'h006D, 8'h00); // LI $00
      load_rom_byte(15'h006E, 8'h38); load_rom_byte(15'h006F, 8'h00); // LB $00 -> $A5
      load_rom_byte(15'h0070, 8'h90); load_rom_byte(15'h0071, 8'hA5); // SUBI $A5
      load_rom_byte(15'h0072, 8'h02); load_rom_byte(15'h0073, 8'h76); // BEQ $76
      load_rom_byte(15'h0074, 8'h01); load_rom_byte(15'h0075, 8'h74); // FAIL halt
      load_rom_byte(15'h0076, 8'h40); load_rom_byte(15'h0077, 8'h00); // SETDP $00
      load_rom_byte(15'h0078, 8'h38); load_rom_byte(15'h0079, 8'h00); // LB $00 -> ROM[$0000]=$30
      load_rom_byte(15'h007A, 8'h90); load_rom_byte(15'h007B, 8'h30); // SUBI $30
      load_rom_byte(15'h007C, 8'h02); load_rom_byte(15'h007D, 8'h80); // BEQ $80
      load_rom_byte(15'h007E, 8'h01); load_rom_byte(15'h007F, 8'h7E); // FAIL halt
      load_rom_byte(15'h0080, 8'h08); load_rom_byte(15'h0081, 8'h00); // EI
      load_rom_byte(15'h0082, 8'h48); load_rom_byte(15'h0083, 8'h00); // DI is inert
      load_rom_byte(15'h0084, 8'h00); load_rom_byte(15'h0085, 8'h00); // NOP
      load_rom_byte(15'h0086, 8'h01); load_rom_byte(15'h0087, 8'h86); // PASS halt
      // Subroutine at $0090.
      load_rom_byte(15'h0090, 8'h30); load_rom_byte(15'h0091, 8'h42);
      load_rom_byte(15'h0092, 8'h04); load_rom_byte(15'h0093, 8'h05);
      load_rom_byte(15'h0094, 8'h20); load_rom_byte(15'h0095, 8'h00);
      load_rom_byte(15'h0096, 8'h01); load_rom_byte(15'h0097, 8'h5E);
    end
  endtask

  task automatic remember_behavioral_checkpoint;
    begin
      if (!expected_valid[behavioral.pc]) begin
        expected_valid[behavioral.pc] = 1'b1;
        expected_ac[behavioral.pc] = behavioral.ac;
        expected_z[behavioral.pc] = behavioral.z_flag;
        expected_ie[behavioral.pc] = behavioral.ie;
        expected_irq_ff[behavioral.pc] = behavioral.irq_ff;
        expected_pg[behavioral.pc] = behavioral.page_reg;
        expected_dp[behavioral.pc] = behavioral.data_page_reg;
        behavior_events = behavior_events + 1;
      end
    end
  endtask

  task automatic compare_chip_checkpoint;
    begin
      if (expected_valid[chip_pc] && !chip_seen[chip_pc]) begin
        chip_seen[chip_pc] = 1'b1;
        chip_events = chip_events + 1;
        if (chip_ac !== expected_ac[chip_pc] ||
            chip.n_Z_flag !== expected_z[chip_pc] ||
            chip.n_IE !== expected_ie[chip_pc] ||
            chip.n_IRQ_FF !== expected_irq_ff[chip_pc] ||
            chip_pg !== expected_pg[chip_pc] ||
            chip_dp !== expected_dp[chip_pc]) begin
          $fatal(1,
            "Dual compare mismatch at PC=%04h: chip AC=%02h Z=%b IE=%b IRQ=%b PG=%02h DP=%02h, behavioral AC=%02h Z=%b IE=%b IRQ=%b PG=%02h DP=%02h",
            chip_pc, chip_ac, chip.n_Z_flag, chip.n_IE, chip.n_IRQ_FF, chip_pg, chip_dp,
            expected_ac[chip_pc], expected_z[chip_pc], expected_ie[chip_pc], expected_irq_ff[chip_pc],
            expected_pg[chip_pc], expected_dp[chip_pc]);
        end
      end
    end
  endtask

  task automatic compare_ram_byte(input [14:0] addr);
    begin
      if (chip.RAM1.memory[addr] !== behavioral.ram[addr]) begin
        $fatal(1, "RAM mismatch at $%04h: chip=%02h behavioral=%02h",
               {1'b1, addr}, chip.RAM1.memory[addr], behavioral.ram[addr]);
      end
    end
  endtask

  initial begin
    force chip.n_CLK = clk;
    force chip.n_bar_RST = rst_n;
    force chip.n_bar_IRQ = irq_n;

    for (i = 0; i < 65536; i = i + 1) begin
      expected_valid[i] = 1'b0;
      chip_seen[i] = 1'b0;
    end
    for (i = 0; i < 32768; i = i + 1) begin
      behavioral.rom[i] = 8'h00;
      behavioral.ram[i] = 8'h00;
      chip.ROM1.memory[i] = 8'h00;
      chip.RAM1.memory[i] = 8'h00;
    end
    load_common_program();

    if (!$value$plusargs("dumpfile=%s", dumpfile))
      dumpfile = "rv8gr_dual_compare.vcd";
    $dumpfile(dumpfile);
    $dumpvars(0, tb_rv8gr_dual_compare);

    clk = 1'b0;
    irq_n = 1'b1;
    rst_n = 1'b0;
    #30;
    chip.U5.Q_current = 8'h00;
    chip.U6.Q_current = 8'h00;
    chip.U9.Q_current = 8'h00;
    chip.U21.Q_current = 2'b01;
    chip.U23.Q_current = 8'h00;
    chip.U31.Q_current = 2'b00;
    chip.U32.Q_current = 8'h80;
    #1;
    rst_n = 1'b1;
    #200;
    irq_n = 1'b0;
    #1000;
    irq_n = 1'b1;
    #200;

    cycles = 0;
    behavior_events = 0;
    chip_events = 0;
    while ((chip_pc !== 16'h0086 && chip_pc !== 16'h0087) && cycles < 1800) begin
      @(posedge clk);
      #150;
      if (^chip_pc === 1'bx || ^chip_ac === 1'bx || ^chip_phase === 1'bx)
        $fatal(1, "Chip-level X/Z at cycle %0d: pc=%h ac=%h phase=%b", cycles, chip_pc, chip_ac, chip_phase);
      if (^behavioral.pc === 1'bx || ^behavioral.ac === 1'bx)
        $fatal(1, "Behavioral X/Z at cycle %0d: pc=%h ac=%h state=%0d", cycles, behavioral.pc, behavioral.ac, behavioral.state);

      if (behavioral.state == 2'd0)
        remember_behavioral_checkpoint();

      if (chip_phase == 3'b001)
        compare_chip_checkpoint();

      cycles = cycles + 1;
    end

    if (chip_pc !== 16'h0086 && chip_pc !== 16'h0087)
      $fatal(1, "Dual compare timeout: chip_pc=%04h behavioral_pc=%04h chip_events=%0d behavior_events=%0d",
             chip_pc, behavioral.pc, chip_events, behavior_events);

    if (!expected_valid[chip_pc])
      $fatal(1, "Final chip PC=%04h was not reached by behavioral model", chip_pc);

    compare_chip_checkpoint();
    compare_ram_byte(15'h0000);
    compare_ram_byte(15'h0001);
    compare_ram_byte(15'h0002);
    compare_ram_byte(15'h0004);
    compare_ram_byte(15'h0005);
    compare_ram_byte(15'h0007);
    compare_ram_byte(15'h1000);

    if (chip_events < 30)
      $fatal(1, "Dual compare too shallow: only %0d chip checkpoints matched", chip_events);

    if (chip.n_IE !== 1'b1 || chip.n_IRQ_FF !== 1'b1 || behavioral.ie !== 1'b1 || behavioral.irq_ff !== 1'b1)
      $fatal(1, "IRQ/EI final mismatch: chip IE=%b IRQ=%b behavioral IE=%b IRQ=%b",
             chip.n_IE, chip.n_IRQ_FF, behavioral.ie, behavioral.irq_ff);

    $display("RV8GR dual compare PASS: matched %0d chip checkpoints against %0d behavioral checkpoints, final pc=%04h ac=%02h z=%b ie=%b irq=%b pg=%02h dp=%02h cycles=%0d",
             chip_events, behavior_events, chip_pc, chip_ac, chip.n_Z_flag, chip.n_IE, chip.n_IRQ_FF, chip_pg, chip_dp, cycles);
    $finish;
  end
endmodule
