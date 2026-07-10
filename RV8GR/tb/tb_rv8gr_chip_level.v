// RV8GR generated chip-level netlist bring-up test.
`timescale 1ns/1ps

module tb_rv8gr_chip_level;
  reg clk;
  reg rst_n;
  reg irq_n;
  integer cycle;
  integer i;
  reg [1023:0] dumpfile;

  rv8gr_chip_level dut();

  always #500 clk = ~clk;

  wire [15:0] pc = {
    dut.n_PC15, dut.n_PC14, dut.n_PC13, dut.n_PC12,
    dut.n_PC11, dut.n_PC10, dut.n_PC9, dut.n_PC8,
    dut.n_PC7, dut.n_PC6, dut.n_PC5, dut.n_PC4,
    dut.n_PC3, dut.n_PC2, dut.n_PC1, dut.n_PC0
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

    // A tiny non-halting ROM image is enough for chip-level bring-up. This
    // bench checks reset, ring timing, memory fetch visibility, and PC motion.
    dut.ROM1.memory[15'h0000] = 8'h30; // LI
    dut.ROM1.memory[15'h0001] = 8'h05;
    dut.ROM1.memory[15'h0002] = 8'h01; // J $02 loop, useful once full checks exist
    dut.ROM1.memory[15'h0003] = 8'h02;

    if (!$value$plusargs("dumpfile=%s", dumpfile))
      dumpfile = "rv8gr_chip_level.vcd";
    $dumpfile(dumpfile);
    $dumpvars(0, tb_rv8gr_chip_level);

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

    for (cycle = 0; cycle < 18; cycle = cycle + 1) begin
      @(posedge clk);
      #100;
      if (^pc === 1'bx) begin
        $fatal(1, "PC contains X/Z after cycle %0d: pc=%h phase=%b", cycle, pc, phase);
      end
      if (^phase === 1'bx) begin
        $fatal(1, "Ring phase contains X/Z after cycle %0d: phase=%b", cycle, phase);
      end
    end

    if (pc == 16'h0000)
      $fatal(1, "PC did not advance from reset");

    if ((dut.n_T0 !== 1'b1) && (dut.n_T1 !== 1'b1) && (dut.n_T2 !== 1'b1))
      $fatal(1, "No ring-counter phase is active");

    $display("RV8GR chip-level bring-up PASS: pc=%h phase=%b", pc, phase);
    $finish;
  end
endmodule
