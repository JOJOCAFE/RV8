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
  reg [1023:0] romfile;

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

  task automatic load_common_program;
    begin
      if (!$value$plusargs("romfile=%s", romfile))
        $fatal(1, "Missing +romfile=<all_isa_equivalence.memh>");
      $readmemh(romfile, behavioral.rom);
      $readmemh(romfile, chip.ROM1.memory);
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
        $display("VERILOG_CHECKPOINT idx=%0d pc=%04h ac=%02h z=%0d ie=%0d irq=%0d pg=%02h dp=%02h",
                 behavior_events, behavioral.pc, behavioral.ac, behavioral.z_flag,
                 behavioral.ie, behavioral.irq_ff, behavioral.page_reg,
                 behavioral.data_page_reg);
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
