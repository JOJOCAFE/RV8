// RV8-GR NOT pseudo-instruction test.
// The assembler emits NOT as XORI $FF; hardware still executes frozen ISA only.
`timescale 1ns/1ps

module tb_rv8gr_not;
    reg clk, rst_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .irq_n(1'b1), .halted(halted));

    always #5 clk = ~clk;
    integer cycle_count;
    integer failures;
    reg [1023:0] dumpfile;

    task check_ram;
        input [14:0] addr;
        input [7:0] expected;
        begin
            if (cpu.ram[addr] !== expected) begin
                $display("FAIL: RAM[$%04X] expected $%02X got $%02X", 16'h8000 + addr, expected, cpu.ram[addr]);
                failures = failures + 1;
            end else begin
                $display("PASS: RAM[$%04X] = $%02X", 16'h8000 + addr, expected);
            end
        end
    endtask

    initial begin
        if (!$value$plusargs("dumpfile=%s", dumpfile))
            dumpfile = "rv8gr_not.vcd";
        $dumpfile(dumpfile);
        $dumpvars(0, tb_rv8gr_not);

        $readmemh("programs/test_not.memh", cpu.rom, 0, 59);

        for (integer i = 0; i < 32768; i = i + 1) cpu.ram[i] = 8'h00;

        clk = 0; rst_n = 0;
        failures = 0;
        #20 rst_n = 1;

        cycle_count = 0;
        while (!halted && cycle_count < 300) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
        end

        if (!halted) begin
            $display("FAIL: NOT test did not halt");
            failures = failures + 1;
        end

        check_ram(15'h0010, 8'hFF);
        check_ram(15'h0011, 8'hAA);
        check_ram(15'h0012, 8'h55);
        check_ram(15'h0013, 8'h00);
        check_ram(15'h0014, 8'hFE);
        check_ram(15'h0015, 8'h7F);
        check_ram(15'h0016, 8'h80);
        check_ram(15'h0017, 8'h0F);
        check_ram(15'h0018, 8'hF0);

        if (cpu.ac !== 8'hF0 || cpu.z_flag !== 1'b0) begin
            $display("FAIL: final AC/Z expected AC=$F0 Z=0 got AC=$%02X Z=%b", cpu.ac, cpu.z_flag);
            failures = failures + 1;
        end

        if (failures == 0)
            $display("=== NOT PSEUDO-INSTRUCTION TEST PASSED ===");
        else begin
            $display("=== NOT PSEUDO-INSTRUCTION TEST FAILED: %0d failures ===", failures);
            $fatal(1, "NOT pseudo-instruction test failed");
        end

        $finish;
    end
endmodule
