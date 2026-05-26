// RV8-GR Testbench — Load assembled .bin file
`timescale 1ns/1ps

module tb_rv8gr_asm;
    reg clk, rst_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .halted(halted));

    always #5 clk = ~clk;
    integer cycle_count;

    initial begin
        $dumpfile("rv8gr_asm.vcd");
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

        if (cpu.pc == 16'h8084)
            $display("=== ASSEMBLER TEST PASSED ===");
        else
            $display("=== FAILED ===");

        $finish;
    end
endmodule
