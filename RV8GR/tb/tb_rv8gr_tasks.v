// RV8-GR task-level milestone tests
`timescale 1ns/1ps

module tb_rv8gr_tasks;
    reg clk, rst_n;
    wire halted;
    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .irq_n(1'b1), .halted(halted));
    always #5 clk = ~clk;
    integer errors; integer i;
    reg [1023:0] dumpfile;

    task clear_mem;
    begin for (i = 0; i < 32768; i = i + 1) begin cpu.rom[i] = 8'h00; cpu.ram[i] = 8'h00; end end endtask

    task reset_cpu;
    begin clk = 1'b0; rst_n = 1'b0; #20; rst_n = 1'b1; #1; end endtask

    task step; begin @(posedge clk); #1; end endtask

    initial begin
        if (!$value$plusargs("dumpfile=%s", dumpfile))
            dumpfile = "rv8gr_tasks.vcd";
        $dumpfile(dumpfile); $dumpvars(0, tb_rv8gr_tasks); errors = 0;
        clear_mem; reset_cpu;

        // Task 1: Reset
        $display("Task 1: Reset");
        if (cpu.pc !== 16'h0000) begin $display("FAIL: PC=%04X", cpu.pc); errors++; end else $display("PASS: PC after reset = $0000");
        if (cpu.page_reg !== 8'h00) begin $display("FAIL: PG=%02X", cpu.page_reg); errors++; end else $display("PASS: page register after reset = $00");
        if (cpu.ac !== 8'h00) begin $display("FAIL: AC=%02X", cpu.ac); errors++; end else $display("PASS: AC after reset = $00");
        if (cpu.z_flag !== 1'b1) begin $display("FAIL: Z=%b", cpu.z_flag); errors++; end else $display("PASS: Z after reset = 1");
        if (cpu.state !== 2'd0) begin $display("FAIL: state=%d", cpu.state); errors++; end else $display("PASS: state after reset = $00");
        if (cpu.halted !== 1'b0) begin $display("FAIL: halted=%b", cpu.halted); errors++; end else $display("PASS: halted after reset = 0");

        // Task 2: Basic Fetch
        clear_mem; reset_cpu;
        cpu.rom[0] = 8'h30; cpu.rom[1] = 8'h42;
        step; if (cpu.ir_high !== 8'h30) begin $display("FAIL: IR=%02X", cpu.ir_high); errors++; end else $display("PASS: T0 latches control = $30");
        if (cpu.pc !== 16'h0001) begin $display("FAIL: PC=%04X", cpu.pc); errors++; end else $display("PASS: PC after T0 = $0001");
        step; if (cpu.ir_low !== 8'h42) begin $display("FAIL: IRL=%02X", cpu.ir_low); errors++; end else $display("PASS: T1 latches operand = $42");
        if (cpu.pc !== 16'h0002) begin $display("FAIL: PC=%04X", cpu.pc); errors++; end else $display("PASS: PC after T1 = $0002");
        step; if (cpu.ac !== 8'h42) begin $display("FAIL: AC=%02X", cpu.ac); errors++; end else $display("PASS: T2 executes LI = $42");
        if (cpu.pc !== 16'h0002) begin $display("FAIL: PC=%04X", cpu.pc); errors++; end else $display("PASS: PC stable after T2 = $0002");
        if (cpu.state !== 2'd0) begin $display("FAIL: state=%d", cpu.state); errors++; end else $display("PASS: state returns to T0 = $00");

        // ... full test continues ...

        $display("\n========================================");
        if (errors == 0) $display("ALL TASK TESTS PASSED");
        else begin
            $display("FAILED: %0d error(s)", errors);
            $fatal(1, "Task-level milestone tests failed");
        end
        $display("========================================");
        $finish;
    end
endmodule
