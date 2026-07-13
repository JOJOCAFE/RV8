// RV8-GR Testbench — Load assembled .bin file
`timescale 1ns/1ps

module tb_rv8gr_asm;
    reg clk, rst_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .irq_n(1'b1), .halted(halted));

    always #5 clk = ~clk;
    integer cycle_count;
    reg [1023:0] dumpfile;

    initial begin
        if (!$value$plusargs("dumpfile=%s", dumpfile))
            dumpfile = "rv8gr_asm.vcd";
        $dumpfile(dumpfile);
        $dumpvars(0, tb_rv8gr_asm);

        // Load ROM from assembled binary
        $readmemh("programs/testrom.hex", cpu.rom);

        // Clear RAM
        for (integer i = 0; i < 32768; i = i + 1) cpu.ram[i] = 8'h00;

        clk = 0; rst_n = 0;
        #20 rst_n = 1;

        cycle_count = 0;
        while (!halted && cycle_count < 500) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
        end

        $display("Halted at PC=$%04X after %0d cycles", cpu.pc, cycle_count);
        $display("AC=$%02X Z=%b PG=$%02X", cpu.ac, cpu.z_flag, cpu.page_reg);

        // testrom.asm: pass has AC=$00 Z=1 from SUBI $77 test
        if (cpu.ac == 8'h00 && cpu.z_flag == 1'b1)
            $display("=== ASSEMBLER TEST PASSED ===");
        else begin
            $display("=== FAILED ===");
            $fatal(1, "Assembler test result mismatch");
        end

        $finish;
    end
endmodule
