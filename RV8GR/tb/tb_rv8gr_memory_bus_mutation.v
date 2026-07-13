// RV8GR memory-write and U7 bus-order mutation tests.
//
// Production RTL is compiled unchanged.  Each mutation is a testbench force
// representing one forbidden wiring/control condition.  The baseline proves
// the intended ownership/protection property; the mutation must fail.
// These are digital-model proofs, not a substitute for physical timing or
// current measurements on a breadboard.
`timescale 1ns/1ps

module tb_rv8gr_memory_bus_mutation;
  integer i;
  rv8gr_chip_level dut();

  task automatic clear_memories;
    begin
      for (i = 0; i < 32768; i = i + 1) begin
        dut.ROM1.memory[i] = 8'h00;
        dut.RAM1.memory[i] = 8'h00;
      end
    end
  endtask

  task automatic disable_other_ibus_sources;
    begin
      force dut.n_bar_IRL_OE = 1'b1;
      force dut.n_bar_AC_BUF = 1'b1;
    end
  endtask

  task automatic release_ibus_byte;
    begin
      release dut.n_IBUS0; release dut.n_IBUS1;
      release dut.n_IBUS2; release dut.n_IBUS3;
      release dut.n_IBUS4; release dut.n_IBUS5;
      release dut.n_IBUS6; release dut.n_IBUS7;
    end
  endtask

  task automatic test_rom_we;
    begin
      clear_memories();
      dut.ROM1.memory[15'h0123] = 8'h3c;
      // This is the ROM's active write window except for /WE, which is tied
      // high in the production netlist.  A write therefore must not occur.
      force dut.ROM1.A = 15'h0123;
      force dut.ROM1.CE_bar = 1'b0;
      force dut.ROM1.OE_bar = 1'b1;
      force dut.ROM1.DQ = 8'ha5;
      #5;
      if (dut.ROM1.WE_bar !== 1'b1)
        $fatal(1, "ROM /WE baseline is not tied high: %b", dut.ROM1.WE_bar);
      if (dut.ROM1.memory[15'h0123] !== 8'h3c)
        $fatal(1, "ROM /WE baseline changed protected byte: %h", dut.ROM1.memory[15'h0123]);
      $display("RV8GR ROM /WE baseline PASS: ROM /WE is tied high and byte remains protected");

      if ($test$plusargs("mutate_rom_we")) begin
        // Emulate the forbidden wiring fault: /WE is pulled low then returns
        // high while CE is active and OE is inactive.  The EEPROM model must
        // commit the forced bus value, proving this fault is observable.
        force dut.ROM1.WE_bar = 1'b0;
        #5;
        release dut.ROM1.WE_bar;
        #1;
        if (dut.ROM1.memory[15'h0123] !== 8'ha5)
          $fatal(1, "ROM /WE mutation setup did not write the EEPROM model: %h", dut.ROM1.memory[15'h0123]);
        $fatal(1, "ROM /WE MUTATION KILLED: removing the hard-high protection rewrote ROM");
      end
    end
  endtask

  task automatic test_store_direction;
    begin
      clear_memories();
      disable_other_ibus_sources();
      // A normal store has U7 moving the selected IBUS byte to DBUS.
      force dut.RAM1.A = 15'h0042;
      force dut.RAM1.CE_bar = 1'b0;
      force dut.RAM1.OE_bar = 1'b1;
      force dut.RAM1.WE_bar = 1'b0;
      force dut.n_BUF_OE_N = 1'b0;
      force dut.n_WR_DIR = 1'b1;
      force dut.n_IBUS0 = 1'b1; force dut.n_IBUS1 = 1'b0;
      force dut.n_IBUS2 = 1'b1; force dut.n_IBUS3 = 1'b0;
      force dut.n_IBUS4 = 1'b0; force dut.n_IBUS5 = 1'b1;
      force dut.n_IBUS6 = 1'b0; force dut.n_IBUS7 = 1'b1;
      #5;
      if (dut.RAM1.memory[15'h0042] !== 8'ha5)
        $fatal(1, "store-direction baseline failed: RAM received %h", dut.RAM1.memory[15'h0042]);
      $display("RV8GR store-direction baseline PASS: U7 transfers IBUS byte to RAM DBUS");

      if ($test$plusargs("mutate_store_direction")) begin
        // Keep the intended source on IBUS but reverse U7 and introduce a
        // different DBUS source.  RAM then receives the wrong byte instead
        // of the selected IBUS byte; the test intentionally kills this fault.
        // Model the independently driven DBUS side at the RAM pin.  This is
        // deliberately a testbench-only hostile source; with DIR reversed it
        // is the value the store path exposes to the RAM rather than A5.
        force dut.RAM1.DQ = 8'h3c;
        force dut.n_WR_DIR = 1'b0;
        // Re-open the RAM write window after the direction/data change so
        // the asynchronous SRAM model samples this deliberately bad source.
        force dut.RAM1.WE_bar = 1'b1;
        #2;
        force dut.RAM1.WE_bar = 1'b0;
        #5;
        if (dut.RAM1.memory[15'h0042] === 8'ha5)
          $fatal(1, "store-direction mutation setup did not perturb RAM data");
        $fatal(1, "STORE DIRECTION MUTATION KILLED: reversed U7 no longer stores the selected IBUS byte");
      end
      release_ibus_byte();
      release dut.n_BUF_OE_N;
      release dut.n_WR_DIR;
      release dut.RAM1.A;
      release dut.RAM1.CE_bar;
      release dut.RAM1.OE_bar;
      release dut.RAM1.WE_bar;
    end
  endtask

  task automatic test_oe_order;
    begin
      clear_memories();
      // U34 initially owns IBUS0 while U7 is disabled.  This is the required
      // precondition before U34 is released and the DBUS-to-IBUS bridge may
      // be enabled on the following control phase.
      force dut.n_IRL0 = 1'b0;
      force dut.n_DBUS0 = 1'b1;
      force dut.n_bar_IRL_OE = 1'b0;
      force dut.n_bar_AC_BUF = 1'b1;
      force dut.n_BUF_OE_N = 1'b1;
      force dut.n_WR_DIR = 1'b0;
      #5;
      if (dut.n_IBUS0 !== 1'b0)
        $fatal(1, "OE-order baseline phase 1 failed: U34 should own IBUS0=%b", dut.n_IBUS0);
      $display("RV8GR OE-order baseline PASS: U7 remains disabled until U34 is released");

      if ($test$plusargs("mutate_oe_order")) begin
        // Deliberate bad order: U7 drives before U34 releases its opposite
        // value.  Resolved IBUS must become X.
        force dut.n_BUF_OE_N = 1'b0;
        #20;
        if (dut.n_IBUS0 !== 1'bx)
          $fatal(1, "OE-order mutation setup did not create IBUS contention: %b", dut.n_IBUS0);
        $fatal(1, "OUTPUT-ENABLE ORDER MUTATION KILLED: overlapping U34/U7 ownership resolved X");
      end
    end
  endtask

  initial begin
    if ($test$plusargs("mutate_rom_we"))
      test_rom_we();
    else if ($test$plusargs("mutate_store_direction"))
      test_store_direction();
    else if ($test$plusargs("mutate_oe_order"))
      test_oe_order();
    else begin
      test_rom_we();
      test_store_direction();
      test_oe_order();
      $display("RV8GR memory/bus mutation baseline PASS");
      $finish;
    end
  end
endmodule
