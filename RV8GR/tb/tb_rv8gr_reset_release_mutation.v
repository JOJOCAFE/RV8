// RV8GR reset-release protocol mutation test.
//
// This is a bench-only test: it drives the same top-level test points as the
// existing chip-level benches, but it never changes rv8gr_chip_level.v or a
// component primitive.  The normal case releases reset while CLK is low and
// proves one clean, one-hot ring phase after the next rising edge.  The
// +mutate_bad_reset_release case deliberately releases reset after a rising
// edge and must be rejected by this protocol checker.
//
// It proves a digital test discipline, not 74HC recovery/removal timing or
// PCB clock quality.
`timescale 1ns/1ps

module tb_rv8gr_reset_release_mutation;
  reg clk;
  reg rst_n;
  reg irq_n;
  reg mutate_bad_reset_release;
  integer i;

  rv8gr_chip_level dut();

  always #500 clk = ~clk;

  wire [2:0] phase = {dut.n_T2, dut.n_T1, dut.n_T0};
  wire [15:0] pc = {
    dut.n_PC15, dut.n_PC14, dut.n_PC13, dut.n_PC12,
    dut.n_PC11, dut.n_PC10, dut.n_PC9, dut.n_PC8,
    dut.n_PC7, dut.n_PC6, dut.n_PC5, dut.n_PC4,
    dut.n_PC3, dut.n_PC2, dut.n_PC1, dut.n_PC0
  };

  task automatic initialise_latches;
    begin
      // Match the established chip-level benches.  These are testbench setup
      // values for primitives whose model state is not otherwise initialized.
      dut.U5.Q_current = 8'h00;
      dut.U6.Q_current = 8'h00;
      dut.U9.Q_current = 8'h00;
      dut.U21.Q_current = 2'b01;
      dut.U23.Q_current = 8'h00;
      dut.U31.Q_current = 2'b00;
      dut.U32.Q_current = 8'h80;
    end
  endtask

  task automatic assert_clean_first_edge;
    begin
      @(posedge clk);
      #150;
      if (rst_n !== 1'b1)
        $fatal(1, "Reset remained asserted after the first clock edge");
      if (^phase === 1'bx)
        $fatal(1, "RESET RELEASE FAILURE: ring phase is X/Z after first edge: %b", phase);
      if (phase !== 3'b001 && phase !== 3'b010 && phase !== 3'b100)
        $fatal(1, "RESET RELEASE FAILURE: ring phase is not one-hot after first edge: %b", phase);
      if (pc !== 16'h0000)
        $fatal(1, "RESET RELEASE FAILURE: PC changed at first edge: %h", pc);
    end
  endtask

  initial begin
    force dut.n_CLK = clk;
    force dut.n_bar_RST = rst_n;
    force dut.n_bar_IRQ = irq_n;

    for (i = 0; i < 32768; i = i + 1) begin
      dut.ROM1.memory[i] = 8'h00;
      dut.RAM1.memory[i] = 8'h00;
    end

    clk = 1'b0;
    rst_n = 1'b0;
    irq_n = 1'b1;
    mutate_bad_reset_release = $test$plusargs("mutate_bad_reset_release");
    #30;
    initialise_latches();

    if (mutate_bad_reset_release) begin
      // Deliberate test-only fault: a reset release after the active clock
      // edge violates the frozen bring-up protocol.  The checker below must
      // fail nonzero even if a zero-delay RTL model happens to settle.
      @(posedge clk);
      #10 rst_n = 1'b1;
      if (clk !== 1'b0)
        $fatal(1, "RESET RELEASE MUTATION KILLED: reset released while CLK=%b at %0t ns", clk, $time);
      $fatal(1, "RESET RELEASE MUTATION KILLED: release occurred after active edge at %0t ns", $time);
    end

    // Baseline release has 400 ns of low-clock margin before the first edge.
    #100 rst_n = 1'b1;
    if (clk !== 1'b0)
      $fatal(1, "Baseline reset release was not during CLK low");
    assert_clean_first_edge();
    $display("RV8GR reset-release baseline PASS: phase=%b pc=%h", phase, pc);
    $finish;
  end
endmodule
