// RV8GR U34-to-U7 IBUS ownership mutation test.
//
// This testbench does not alter the production netlist.  It first proves the
// safe ownership state (U34 enabled while U7 is disabled), then uses only
// testbench forces to emulate the forbidden state: U34 and U7 both drive
// IBUS[0] with opposite values.  The primitive resolution must become X and
// the mutation run must exit nonzero.  This is digital bus-resolution
// evidence only; it is not a measured 74HC turn-around/deadband proof.
`timescale 1ns/1ps

module tb_rv8gr_u34_u7_handoff_mutation;
  reg mutate_handoff_conflict;
  integer i;
  rv8gr_chip_level dut();

  task automatic force_common_sources;
    begin
      // U34 reads a zero instruction-low bit while the external DBUS source
      // supplies one.  Only the mutated U7 DBUS-to-IBUS path can make these
      // two values contend on IBUS[0].
      force dut.n_IRL0 = 1'b0;
      force dut.n_DBUS0 = 1'b1;
      force dut.n_bar_IRL_OE = 1'b0;
      // U14 is another legal IBUS driver in a different CPU phase.  Disable
      // it explicitly so this isolated ownership test contains only U34 and
      // (in the mutation run) U7.
      force dut.n_bar_AC_BUF = 1'b1;
    end
  endtask

  initial begin
    mutate_handoff_conflict = $test$plusargs("mutate_u34_u7_conflict");
    for (i = 0; i < 32768; i = i + 1) begin
      dut.ROM1.memory[i] = 8'h00;
      dut.RAM1.memory[i] = 8'h00;
    end
    force_common_sources();

    if (!mutate_handoff_conflict) begin
      // Normal ownership: U34 drives IBUS, while U7 is high-Z.
      force dut.n_BUF_OE_N = 1'b1;
      force dut.n_WR_DIR = 1'b0;
      #20;
      if (dut.n_IBUS0 !== 1'b0)
        $fatal(1, "U34/U7 baseline failure: expected U34-only IBUS0=0, got %b", dut.n_IBUS0);
      $display("RV8GR U34/U7 handoff baseline PASS: U34 owns IBUS0 and U7 is high-Z");
      $finish;
    end

    // Deliberate fault: U7 is enabled DBUS-to-IBUS while U34 remains enabled.
    force dut.n_BUF_OE_N = 1'b0;
    force dut.n_WR_DIR = 1'b0;
    #20;
    if (dut.n_IBUS0 !== 1'bx)
      $fatal(1, "U34/U7 mutation setup did not create a resolved conflict: IBUS0=%b", dut.n_IBUS0);
    $fatal(1, "U34/U7 HANDOFF MUTATION KILLED: opposing U34/U7 IBUS drivers resolved X");
  end
endmodule
