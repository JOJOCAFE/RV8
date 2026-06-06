// RV8-GR IRQ Testbench
// Tests: EI/DI, IRQ latching, vector jump, PC save, nested prevention
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

    initial begin
        $dumpfile("rv8gr_irq.vcd");
        $dumpvars(0, tb_rv8gr_irq);
        errors = 0;

        for (i = 0; i < 32768; i = i + 1) begin
            cpu.rom[i] = 8'h00;
            cpu.ram[i] = 8'h00;
        end

        $display("\nTest 1: IRQ blocked when IE=0");
        cpu.rom[0] = 8'h30; cpu.rom[1] = 8'hAA;
        cpu.rom[2] = 8'h01; cpu.rom[3] = 8'h02;
        cpu.rom[16'h7F00] = 8'h30; cpu.rom[16'h7F01] = 8'hDD;

        reset_cpu;
        irq_n = 0; #10; irq_n = 1;
        run_instr;
        if (cpu.ac !== 8'hAA) begin
            $display("FAIL: AC=%02X, expected $AA", cpu.ac);
            errors = errors + 1;
        end else
            $display("PASS: IRQ ignored when IE=0, AC=$%02X", cpu.ac);

        $display("\nTest 2: EI + IRQ fires");
        for (i = 0; i < 32768; i = i + 1) begin
            cpu.rom[i] = 8'h00; cpu.ram[i] = 8'h00;
        end
        cpu.rom[0] = 8'h08; cpu.rom[1] = 8'h00;
        cpu.rom[2] = 8'h30; cpu.rom[3] = 8'h42;
        cpu.rom[4] = 8'h01; cpu.rom[5] = 8'h04;
        cpu.rom[16'h7F00] = 8'h30; cpu.rom[16'h7F01] = 8'hBB;
        cpu.rom[16'h7F02] = 8'h01; cpu.rom[16'h7F03] = 8'h02;

        reset_cpu;
        run_instr;
        if (cpu.ie !== 1'b1) begin
            $display("FAIL: IE=%b after EI", cpu.ie);
            errors = errors + 1;
        end else $display("PASS: IE=1 after EI");

        irq_n = 0; #10; irq_n = 1;
        run_instr;
        run_instr;
        if (cpu.ac !== 8'hBB) begin
            $display("FAIL: AC=%02X, expected $BB", cpu.ac);
            errors = errors + 1;
        end else $display("PASS: ISR executed, AC=$%02X", cpu.ac);

        $display("\nTest 3: PC saved to RAM[$0E:$0F]");
        if (cpu.ram[8'h0E] !== 8'h04) begin
            $display("FAIL: RAM[$0E]=%02X, expected $04", cpu.ram[8'h0E]);
            errors = errors + 1;
        end else $display("PASS: PC low saved = $%02X", cpu.ram[8'h0E]);
        if (cpu.ram[8'h0F] !== 8'h80) begin
            $display("FAIL: RAM[$0F]=%02X, expected $80", cpu.ram[8'h0F]);
            errors = errors + 1;
        end else $display("PASS: PC high saved = $%02X", cpu.ram[8'h0F]);

        $display("\nTest 4: IE cleared after IRQ");
        if (cpu.ie !== 1'b0) begin
            $display("FAIL: IE=%b, expected 0 after IRQ", cpu.ie);
            errors = errors + 1;
        end else $display("PASS: IE=0 after IRQ");

        $display("\nTest 5: DI disables interrupts");
        for (i = 0; i < 32768; i = i + 1) begin
            cpu.rom[i] = 8'h00; cpu.ram[i] = 8'h00;
        end
        cpu.rom[0] = 8'h08; cpu.rom[1] = 8'h00;
        cpu.rom[2] = 8'h48; cpu.rom[3] = 8'h00;
        cpu.rom[4] = 8'h30; cpu.rom[5] = 8'hCC;
        cpu.rom[6] = 8'h01; cpu.rom[7] = 8'h06;
        cpu.rom[16'h7F00] = 8'h30; cpu.rom[16'h7F01] = 8'hDD;

        reset_cpu;
        run_instr; run_instr;
        irq_n = 0; #10; irq_n = 1;
        run_instr;
        if (cpu.ac !== 8'hCC) begin
            $display("FAIL: AC=%02X, expected $CC", cpu.ac);
            errors = errors + 1;
        end else $display("PASS: DI blocks IRQ, AC=$%02X", cpu.ac);

        $display("\n========================================");
        if (errors == 0) $display("ALL IRQ TESTS PASSED");
        else $display("FAILED: %0d error(s)", errors);
        $display("========================================");
        $finish;
    end
endmodule