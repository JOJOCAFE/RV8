// RV8-GR v1.0 polling IRQ testbench
// Tests: EI flag behavior, IRQ latching on /IRQ release, no hardware vector, no PC save.
// Memory map: ROM $0000-$7FFF, RAM $8000-$FFFF
`timescale 1ns/1ps

module tb_rv8gr_irq;
    reg clk, rst_n, irq_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .irq_n(irq_n), .halted(halted));

    always #5 clk = ~clk;

    integer errors;
    integer i;

    task reset_cpu;
    begin
        clk = 0; rst_n = 0; irq_n = 1;
        #20; rst_n = 1; #1;
    end
    endtask

    task step;
    begin @(posedge clk); #1; end
    endtask

    task run_instr;
    begin step; step; step; end
    endtask

    task pulse_irq;
    begin irq_n = 0; #1; irq_n = 1; end
    endtask

    task clear_mem;
    begin
        for (i = 0; i < 32768; i = i + 1) begin
            cpu.rom[i] = 8'h00;
            cpu.ram[i] = 8'h00;
        end
    end
    endtask

    initial begin
        $dumpfile("rv8gr_irq.vcd");
        $dumpvars(0, tb_rv8gr_irq);
        errors = 0;

        $display("\nTest 1: /IRQ latches but does not vector when IE=0");
        clear_mem;
        cpu.rom[0] = 8'h30; cpu.rom[1] = 8'hAA;  // LI $AA
        cpu.rom[2] = 8'h01; cpu.rom[3] = 8'h02;  // HLT
        cpu.ram[8'h0E] = 8'h55;
        cpu.ram[8'h0F] = 8'h66;

        reset_cpu;
        irq_n = 0; #1;
        if (cpu.irq_ff !== 1'b0) begin
            $display("FAIL: IRQ_FF latched before /IRQ release");
            errors = errors + 1;
        end else $display("PASS: IRQ_FF waits for /IRQ rising edge");
        irq_n = 1; #1;
        run_instr;
        if (cpu.irq_ff !== 1'b1) begin
            $display("FAIL: IRQ_FF=%b, expected 1", cpu.irq_ff);
            errors = errors + 1;
        end else $display("PASS: IRQ_FF latched");
        if (cpu.pc !== 16'h0002 || cpu.ac !== 8'hAA) begin
            $display("FAIL: PC=%04X AC=%02X, expected PC=$0002 AC=$AA", cpu.pc, cpu.ac);
            errors = errors + 1;
        end else $display("PASS: CPU continued normal instruction flow");

        $display("\nTest 2: EI sets IE but IRQ still does not vector");
        clear_mem;
        cpu.rom[0] = 8'h08; cpu.rom[1] = 8'h00;  // EI
        cpu.rom[2] = 8'h30; cpu.rom[3] = 8'h42;  // LI $42
        cpu.rom[4] = 8'h01; cpu.rom[5] = 8'h04;  // HLT
        cpu.ram[8'h0E] = 8'h55;
        cpu.ram[8'h0F] = 8'h66;

        reset_cpu;
        run_instr;
        if (cpu.ie !== 1'b1) begin
            $display("FAIL: IE=%b after EI", cpu.ie);
            errors = errors + 1;
        end else $display("PASS: EI sets IE");

        pulse_irq;
        run_instr;
        if (cpu.pc !== 16'h0004 || cpu.ac !== 8'h42) begin
            $display("FAIL: IRQ changed flow: PC=%04X AC=%02X", cpu.pc, cpu.ac);
            errors = errors + 1;
        end else $display("PASS: no hardware vector with IE=1");
        if (cpu.page_reg !== 8'h00) begin
            $display("FAIL: PG=%02X, expected unchanged $00", cpu.page_reg);
            errors = errors + 1;
        end else $display("PASS: page register unchanged");
        if (cpu.ram[8'h0E] !== 8'h55 || cpu.ram[8'h0F] !== 8'h66) begin
            $display("FAIL: PC-save slots changed: %02X %02X", cpu.ram[8'h0E], cpu.ram[8'h0F]);
            errors = errors + 1;
        end else $display("PASS: no automatic PC save to RAM");

        $display("\nTest 3: DI is inert in the 33-chip v1.0 build");
        clear_mem;
        cpu.rom[0] = 8'h08; cpu.rom[1] = 8'h00;  // EI
        cpu.rom[2] = 8'h48; cpu.rom[3] = 8'h00;  // DI
        cpu.rom[4] = 8'h30; cpu.rom[5] = 8'hCC;  // LI $CC

        reset_cpu;
        run_instr;
        run_instr;
        if (cpu.ie !== 1'b1) begin
            $display("FAIL: IE=%b after DI marker, expected IE to remain 1", cpu.ie);
            errors = errors + 1;
        end else $display("PASS: DI does not require extra clear hardware");
        pulse_irq;
        run_instr;
        if (cpu.irq_ff !== 1'b1 || cpu.ac !== 8'hCC || cpu.pc !== 16'h0006) begin
            $display("FAIL: IRQ/DI flow mismatch IRQ=%b AC=%02X PC=%04X", cpu.irq_ff, cpu.ac, cpu.pc);
            errors = errors + 1;
        end else $display("PASS: IRQ latch is independent of automatic control flow");

        $display("\n========================================");
        if (errors != 0)
            $fatal(1, "IRQ TESTS FAILED: %0d error(s)", errors);
        $display("ALL IRQ POLLING TESTS PASSED");
        $display("========================================");
        $finish;
    end
endmodule
