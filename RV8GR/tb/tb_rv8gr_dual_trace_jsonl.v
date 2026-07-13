// RV8GR settled phase trace collector.
//
// This bench is observation-only: it does not alter production RTL or claim
// physical timing.  Each record is sampled 150 ns after a rising clock edge,
// matching tb_rv8gr_dual_compare.v's settled-observation convention.
`timescale 1ns/1ps

module tb_rv8gr_dual_trace_jsonl;
  reg clk;
  reg rst_n;
  reg irq_n;
  integer i;
  integer cycle;
  integer maxcycles;
  integer trace_fd;
  integer chip_t0_count;
  integer chip_t1_count;
  integer chip_t2_count;
  integer behavior_t0_count;
  integer behavior_t1_count;
  integer behavior_t2_count;
  reg [1023:0] romfile;
  reg [1023:0] tracefile;

  rv8gr_cpu behavioral(.clk(clk), .rst_n(rst_n), .irq_n(irq_n));
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
  wire [15:0] chip_abus = {
    chip.n_ABUS15, chip.n_ABUS14, chip.n_ABUS13, chip.n_ABUS12,
    chip.n_ABUS11, chip.n_ABUS10, chip.n_ABUS9, chip.n_ABUS8,
    chip.n_ABUS7, chip.n_ABUS6, chip.n_ABUS5, chip.n_ABUS4,
    chip.n_ABUS3, chip.n_ABUS2, chip.n_ABUS1, chip.n_ABUS0
  };
  wire [7:0] chip_dbus = {
    chip.n_DBUS7, chip.n_DBUS6, chip.n_DBUS5, chip.n_DBUS4,
    chip.n_DBUS3, chip.n_DBUS2, chip.n_DBUS1, chip.n_DBUS0
  };

  task automatic load_common_program;
    begin
      if (!$value$plusargs("romfile=%s", romfile))
        $fatal(1, "Missing +romfile=<program.memh>");
      $readmemh(romfile, behavioral.rom);
      $readmemh(romfile, chip.ROM1.memory);
    end
  endtask

  task automatic write_trace_record;
    begin
      // Hex values are JSON strings deliberately: a contention/X/Z observation
      // remains representable in the trace instead of becoming invalid JSON.
      $fdisplay(trace_fd,
        "{\"schema\":\"rv8gr.phase-trace@1\",\"cycle\":%0d,\"time_ns\":%0t,\"settle_ns\":150,\"behavioral\":{\"phase\":%0d,\"pc\":\"%04h\",\"ac\":\"%02h\",\"z\":%0b,\"ie\":%0b,\"irq_ff\":%0b,\"pg\":\"%02h\",\"dp\":\"%02h\"},\"chip\":{\"phase\":\"%03b\",\"pc\":\"%04h\",\"ac\":\"%02h\",\"z\":%0b,\"ie\":%0b,\"irq_ff\":%0b,\"pg\":\"%02h\",\"dp\":\"%02h\",\"abus\":\"%04h\",\"dbus\":\"%02h\",\"ram_ce_bar\":%0b,\"ram_oe_bar\":%0b,\"ram_we_bar\":%0b,\"rom_ce_bar\":%0b,\"rom_oe_bar\":%0b,\"rom_we_bar\":1}}",
        cycle, $time, behavioral.state, behavioral.pc, behavioral.ac,
        behavioral.z_flag, behavioral.ie, behavioral.irq_ff,
        behavioral.page_reg, behavioral.data_page_reg,
        chip_phase, chip_pc, chip_ac, chip.n_Z_flag, chip.n_IE,
        chip.n_IRQ_FF, chip_pg, chip_dp, chip_abus, chip_dbus,
        chip.n_bar_A15, chip.n_RAM1_22, chip.n_bar_AC_BUF,
        chip.n_ABUS15, chip.n_WR_DIR);
    end
  endtask

  initial begin
    force chip.n_CLK = clk;
    force chip.n_bar_RST = rst_n;
    force chip.n_bar_IRQ = irq_n;

    for (i = 0; i < 32768; i = i + 1) begin
      behavioral.rom[i] = 8'h00;
      behavioral.ram[i] = 8'h00;
      chip.ROM1.memory[i] = 8'h00;
      chip.RAM1.memory[i] = 8'h00;
    end
    load_common_program();

    if (!$value$plusargs("tracefile=%s", tracefile))
      tracefile = "rv8gr_dual_phase_trace.jsonl";
    if (!$value$plusargs("maxcycles=%d", maxcycles))
      maxcycles = 1800;
    trace_fd = $fopen(tracefile, "w");
    if (trace_fd == 0)
      $fatal(1, "Cannot open trace file %0s", tracefile);

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
    #1 rst_n = 1'b1;
    #200 irq_n = 1'b0;
    #1000 irq_n = 1'b1;
    #200;

    cycle = 0;
    chip_t0_count = 0; chip_t1_count = 0; chip_t2_count = 0;
    behavior_t0_count = 0; behavior_t1_count = 0; behavior_t2_count = 0;
    while ((chip_pc !== 16'h0086 && chip_pc !== 16'h0087) && cycle < maxcycles) begin
      @(posedge clk);
      #150;
      if (^chip_pc === 1'bx || ^chip_ac === 1'bx || ^chip_phase === 1'bx)
        $fatal(1, "Chip-level X/Z at cycle %0d: pc=%h ac=%h phase=%b", cycle, chip_pc, chip_ac, chip_phase);
      if (^behavioral.pc === 1'bx || ^behavioral.ac === 1'bx || ^behavioral.state === 1'bx)
        $fatal(1, "Behavioral X/Z at cycle %0d: pc=%h ac=%h state=%0d", cycle, behavioral.pc, behavioral.ac, behavioral.state);

      case (chip_phase)
        3'b001: chip_t0_count = chip_t0_count + 1;
        3'b010: chip_t1_count = chip_t1_count + 1;
        3'b100: chip_t2_count = chip_t2_count + 1;
        default: $fatal(1, "Invalid chip phase at cycle %0d: %b", cycle, chip_phase);
      endcase
      case (behavioral.state)
        2'd0: behavior_t0_count = behavior_t0_count + 1;
        2'd1: behavior_t1_count = behavior_t1_count + 1;
        2'd2: behavior_t2_count = behavior_t2_count + 1;
        default: $fatal(1, "Invalid behavioral phase at cycle %0d: %0d", cycle, behavioral.state);
      endcase
      write_trace_record();
      cycle = cycle + 1;
    end

    $fclose(trace_fd);
    if (chip_pc !== 16'h0086 && chip_pc !== 16'h0087)
      $fatal(1, "Trace timeout: pc=%04h cycles=%0d", chip_pc, cycle);
    if (chip_t0_count == 0 || chip_t1_count == 0 || chip_t2_count == 0 ||
        behavior_t0_count == 0 || behavior_t1_count == 0 || behavior_t2_count == 0)
      $fatal(1, "Trace lacks a phase: chip T0/T1/T2=%0d/%0d/%0d behavioral T0/T1/T2=%0d/%0d/%0d",
             chip_t0_count, chip_t1_count, chip_t2_count,
             behavior_t0_count, behavior_t1_count, behavior_t2_count);
    $display("RV8GR dual JSONL trace PASS: records=%0d chip T0/T1/T2=%0d/%0d/%0d behavioral T0/T1/T2=%0d/%0d/%0d file=%0s",
             cycle, chip_t0_count, chip_t1_count, chip_t2_count,
             behavior_t0_count, behavior_t1_count, behavior_t2_count, tracefile);
    $finish;
  end
endmodule
