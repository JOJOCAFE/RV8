// RV8GR chip-level full ROM-program test.
`timescale 1ns/1ps

module tb_rv8gr_chip_full;
  reg clk;
  reg rst_n;
  reg irq_n;
  integer cycle_count;
  integer i;

  rv8gr_chip_level dut();

  always #500 clk = ~clk;

  wire [15:0] pc = {
    dut.n_PC15, dut.n_PC14, dut.n_PC13, dut.n_PC12,
    dut.n_PC11, dut.n_PC10, dut.n_PC9, dut.n_PC8,
    dut.n_PC7, dut.n_PC6, dut.n_PC5, dut.n_PC4,
    dut.n_PC3, dut.n_PC2, dut.n_PC1, dut.n_PC0
  };

  wire [7:0] ac = {
    dut.n_AC7, dut.n_AC6, dut.n_AC5, dut.n_AC4,
    dut.n_AC3, dut.n_AC2, dut.n_AC1, dut.n_AC0
  };

  wire [7:0] pg = {
    dut.n_PG7, dut.n_PG6, dut.n_PG5, dut.n_PG4,
    dut.n_PG3, dut.n_PG2, dut.n_PG1, dut.n_PG0
  };

  wire [7:0] irh = {
    dut.n_ALU_SUB, dut.n_XOR_MODE, dut.n_MUX_SEL, dut.n_AC_WR,
    dut.n_SRC, dut.n_STR, dut.n_BR, dut.n_JMP
  };

  wire [7:0] irl = {
    dut.n_IRL7, dut.n_IRL6, dut.n_IRL5, dut.n_IRL4,
    dut.n_IRL3, dut.n_IRL2, dut.n_IRL1, dut.n_IRL0
  };

  wire [2:0] phase = {dut.n_T2, dut.n_T1, dut.n_T0};

  initial begin
    force dut.n_CLK = clk;
    force dut.n_bar_RST = rst_n;
    force dut.n_bar_IRQ = irq_n;

    for (i = 0; i < 32768; i = i + 1) begin
      dut.ROM1.memory[i] = 8'h00;
      dut.RAM1.memory[i] = 8'h00;
    end

    // Same ROM program as tb_rv8gr_full.v.
    dut.ROM1.memory[15'h0000] = 8'h30; dut.ROM1.memory[15'h0001] = 8'h00;
    dut.ROM1.memory[15'h0002] = 8'h02; dut.ROM1.memory[15'h0003] = 8'h08;
    dut.ROM1.memory[15'h0004] = 8'h01; dut.ROM1.memory[15'h0005] = 8'h04;
    dut.ROM1.memory[15'h0008] = 8'h30; dut.ROM1.memory[15'h0009] = 8'h05;
    dut.ROM1.memory[15'h000A] = 8'h82; dut.ROM1.memory[15'h000B] = 8'h10;
    dut.ROM1.memory[15'h000C] = 8'h01; dut.ROM1.memory[15'h000D] = 8'h0C;
    dut.ROM1.memory[15'h0010] = 8'h10; dut.ROM1.memory[15'h0011] = 8'h03;
    dut.ROM1.memory[15'h0012] = 8'h90; dut.ROM1.memory[15'h0013] = 8'h08;
    dut.ROM1.memory[15'h0014] = 8'h70; dut.ROM1.memory[15'h0015] = 8'hAA;
    dut.ROM1.memory[15'h0016] = 8'h04; dut.ROM1.memory[15'h0017] = 8'h00;
    dut.ROM1.memory[15'h0018] = 8'h30; dut.ROM1.memory[15'h0019] = 8'h00;
    dut.ROM1.memory[15'h001A] = 8'h38; dut.ROM1.memory[15'h001B] = 8'h00;
    dut.ROM1.memory[15'h001C] = 8'h90; dut.ROM1.memory[15'h001D] = 8'hAA;
    dut.ROM1.memory[15'h001E] = 8'h02; dut.ROM1.memory[15'h001F] = 8'h22;
    dut.ROM1.memory[15'h0020] = 8'h01; dut.ROM1.memory[15'h0021] = 8'h20;
    dut.ROM1.memory[15'h0022] = 8'h30; dut.ROM1.memory[15'h0023] = 8'h55;
    dut.ROM1.memory[15'h0024] = 8'h04; dut.ROM1.memory[15'h0025] = 8'h01;
    dut.ROM1.memory[15'h0026] = 8'h18; dut.ROM1.memory[15'h0027] = 8'h01;
    dut.ROM1.memory[15'h0028] = 8'h98; dut.ROM1.memory[15'h0029] = 8'h00;
    dut.ROM1.memory[15'h002A] = 8'h02; dut.ROM1.memory[15'h002B] = 8'h2E;
    dut.ROM1.memory[15'h002C] = 8'h01; dut.ROM1.memory[15'h002D] = 8'h2C;
    dut.ROM1.memory[15'h002E] = 8'h30; dut.ROM1.memory[15'h002F] = 8'hFF;
    dut.ROM1.memory[15'h0030] = 8'h04; dut.ROM1.memory[15'h0031] = 8'h02;
    dut.ROM1.memory[15'h0032] = 8'h78; dut.ROM1.memory[15'h0033] = 8'h02;
    dut.ROM1.memory[15'h0034] = 8'h02; dut.ROM1.memory[15'h0035] = 8'h38;
    dut.ROM1.memory[15'h0036] = 8'h01; dut.ROM1.memory[15'h0037] = 8'h36;
    dut.ROM1.memory[15'h0038] = 8'h20; dut.ROM1.memory[15'h0039] = 8'h10;
    dut.ROM1.memory[15'h003A] = 8'h01; dut.ROM1.memory[15'h003B] = 8'h00;
    dut.ROM1.memory[15'h1000] = 8'h20; dut.ROM1.memory[15'h1001] = 8'h7F;
    dut.ROM1.memory[15'h1002] = 8'h01; dut.ROM1.memory[15'h1003] = 8'h00;
    dut.ROM1.memory[15'h7F00] = 8'h20; dut.ROM1.memory[15'h7F01] = 8'h00;
    dut.ROM1.memory[15'h7F02] = 8'h01; dut.ROM1.memory[15'h7F03] = 8'h40;
    dut.ROM1.memory[15'h0040] = 8'h30; dut.ROM1.memory[15'h0041] = 8'h00;
    dut.ROM1.memory[15'h0042] = 8'h04; dut.ROM1.memory[15'h0043] = 8'h04;
    dut.ROM1.memory[15'h0044] = 8'h28; dut.ROM1.memory[15'h0045] = 8'h04;
    dut.ROM1.memory[15'h0046] = 8'h20; dut.ROM1.memory[15'h0047] = 8'h00;
    dut.ROM1.memory[15'h0048] = 8'h30; dut.ROM1.memory[15'h0049] = 8'h5E;
    dut.ROM1.memory[15'h004A] = 8'h04; dut.ROM1.memory[15'h004B] = 8'h07;
    dut.ROM1.memory[15'h004C] = 8'h01; dut.ROM1.memory[15'h004D] = 8'h70;
    dut.ROM1.memory[15'h005E] = 8'h38; dut.ROM1.memory[15'h005F] = 8'h05;
    dut.ROM1.memory[15'h0060] = 8'h90; dut.ROM1.memory[15'h0061] = 8'h42;
    dut.ROM1.memory[15'h0062] = 8'h02; dut.ROM1.memory[15'h0063] = 8'h66;
    dut.ROM1.memory[15'h0064] = 8'h01; dut.ROM1.memory[15'h0065] = 8'h64;
    dut.ROM1.memory[15'h0066] = 8'h01; dut.ROM1.memory[15'h0067] = 8'h66;
    dut.ROM1.memory[15'h0070] = 8'h30; dut.ROM1.memory[15'h0071] = 8'h42;
    dut.ROM1.memory[15'h0072] = 8'h04; dut.ROM1.memory[15'h0073] = 8'h05;
    dut.ROM1.memory[15'h0074] = 8'h20; dut.ROM1.memory[15'h0075] = 8'h00;
    dut.ROM1.memory[15'h0076] = 8'h01; dut.ROM1.memory[15'h0077] = 8'h5E;

    $dumpfile("rv8gr_chip_full.vcd");
    $dumpvars(0, tb_rv8gr_chip_full);

    clk = 1'b0;
    irq_n = 1'b1;
    rst_n = 1'b0;
    #30;
    dut.U5.Q_current = 8'h00;   // IR high
    dut.U6.Q_current = 8'h00;   // IR low
    dut.U9.Q_current = 8'h00;   // AC
    dut.U21.Q_current = 2'b01;  // Z flag set, spare FF clear
    dut.U23.Q_current = 8'h00;  // page register
    dut.U31.Q_current = 2'b00;  // IRQ/IE latch
    dut.U32.Q_current = 8'h80;  // data page default
    #1;
    rst_n = 1'b1;

    cycle_count = 0;
    while (pc !== 16'h0066 && pc !== 16'h0067 && cycle_count < 1500) begin
      @(posedge clk);
      #100;
      if (^pc === 1'bx)
        $fatal(1, "PC contains X/Z at cycle %0d: pc=%h phase=%b ir=%02h/%02h ac=%02h pg=%02h z=%b",
               cycle_count, pc, phase, irh, irl, ac, pg, dut.n_Z_flag);
      if (^ac === 1'bx)
        $fatal(1, "AC contains X/Z at cycle %0d: pc=%h phase=%b ir=%02h/%02h ac=%02h pg=%02h z=%b ibus=%b ac_in=%b",
               cycle_count, pc, phase, irh, irl, ac, pg, dut.n_Z_flag,
               {dut.n_IBUS7, dut.n_IBUS6, dut.n_IBUS5, dut.n_IBUS4, dut.n_IBUS3, dut.n_IBUS2, dut.n_IBUS1, dut.n_IBUS0},
               {dut.n_AC_IN7, dut.n_AC_IN6, dut.n_AC_IN5, dut.n_AC_IN4, dut.n_AC_IN3, dut.n_AC_IN2, dut.n_AC_IN1, dut.n_AC_IN0});
      cycle_count = cycle_count + 1;
    end

    if (pc !== 16'h0066 && pc !== 16'h0067) begin
      $fatal(1, "RV8GR chip full test timeout: pc=%h phase=%b ir=%02h/%02h ac=%02h pg=%02h z=%b cycles=%0d",
             pc, phase, irh, irl, ac, pg, dut.n_Z_flag, cycle_count);
    end
    if (ac !== 8'h00 || dut.n_Z_flag !== 1'b1 || pg !== 8'h00) begin
      $fatal(1, "RV8GR chip final state mismatch: pc=%h ac=%02h z=%b pg=%02h cycles=%0d",
             pc, ac, dut.n_Z_flag, pg, cycle_count);
    end

    $display("RV8GR chip-level full PASS: pc=%h ac=%02h z=%b pg=%02h cycles=%0d",
             pc, ac, dut.n_Z_flag, pg, cycle_count);
    $finish;
  end
endmodule
