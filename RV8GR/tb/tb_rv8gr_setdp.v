// RV8-GR Testbench — SETDP large RAM test (5KB + ROM read)
`timescale 1ns/1ps

module tb_rv8gr_setdp;
    reg clk, rst_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .irq_n(1'b1), .halted(halted));

    always #5 clk = ~clk;
    integer cycle_count;

    initial begin
        $dumpfile("rv8gr_setdp.vcd");
        $dumpvars(0, tb_rv8gr_setdp);

        // Write phase
        cpu.rom[0]  = 8'h40; cpu.rom[1]  = 8'h10;
        cpu.rom[2]  = 8'h30; cpu.rom[3]  = 8'h10;
        cpu.rom[4]  = 8'h04; cpu.rom[5]  = 8'h00;
        cpu.rom[6]  = 8'h04; cpu.rom[7]  = 8'h80;
        cpu.rom[8]  = 8'h04; cpu.rom[9]  = 8'hFF;
        cpu.rom[10] = 8'h40; cpu.rom[11] = 8'h15;
        cpu.rom[12] = 8'h30; cpu.rom[13] = 8'h15;
        cpu.rom[14] = 8'h04; cpu.rom[15] = 8'h00;
        cpu.rom[16] = 8'h04; cpu.rom[17] = 8'h40;
        cpu.rom[18] = 8'h40; cpu.rom[19] = 8'h20;
        cpu.rom[20] = 8'h30; cpu.rom[21] = 8'h20;
        cpu.rom[22] = 8'h04; cpu.rom[23] = 8'h00;
        cpu.rom[24] = 8'h04; cpu.rom[25] = 8'hFF;
        cpu.rom[26] = 8'h40; cpu.rom[27] = 8'h23;
        cpu.rom[28] = 8'h30; cpu.rom[29] = 8'h23;
        cpu.rom[30] = 8'h04; cpu.rom[31] = 8'hFF;
        // Read phase
        cpu.rom[32] = 8'h40; cpu.rom[33] = 8'h10;
        cpu.rom[34] = 8'h38; cpu.rom[35] = 8'h00;
        cpu.rom[36] = 8'h90; cpu.rom[37] = 8'h10;
        cpu.rom[38] = 8'h02; cpu.rom[39] = 8'h2A;
        cpu.rom[40] = 8'h01; cpu.rom[41] = 8'h7C;
        cpu.rom[42] = 8'h38; cpu.rom[43] = 8'hFF;
        cpu.rom[44] = 8'h90; cpu.rom[45] = 8'h10;
        cpu.rom[46] = 8'h02; cpu.rom[47] = 8'h32;
        cpu.rom[48] = 8'h01; cpu.rom[49] = 8'h7C;
        cpu.rom[50] = 8'h40; cpu.rom[51] = 8'h15;
        cpu.rom[52] = 8'h38; cpu.rom[53] = 8'h00;
        cpu.rom[54] = 8'h90; cpu.rom[55] = 8'h15;
        cpu.rom[56] = 8'h02; cpu.rom[57] = 8'h3C;
        cpu.rom[58] = 8'h01; cpu.rom[59] = 8'h7C;
        cpu.rom[60] = 8'h38; cpu.rom[61] = 8'h40;
        cpu.rom[62] = 8'h90; cpu.rom[63] = 8'h15;
        cpu.rom[64] = 8'h02; cpu.rom[65] = 8'h44;
        cpu.rom[66] = 8'h01; cpu.rom[67] = 8'h7C;
        cpu.rom[68] = 8'h40; cpu.rom[69] = 8'h20;
        cpu.rom[70] = 8'h38; cpu.rom[71] = 8'h00;
        cpu.rom[72] = 8'h90; cpu.rom[73] = 8'h20;
        cpu.rom[74] = 8'h02; cpu.rom[75] = 8'h4E;
        cpu.rom[76] = 8'h01; cpu.rom[77] = 8'h7C;
        cpu.rom[78] = 8'h38; cpu.rom[79] = 8'hFF;
        cpu.rom[80] = 8'h90; cpu.rom[81] = 8'h20;
        cpu.rom[82] = 8'h02; cpu.rom[83] = 8'h56;
        cpu.rom[84] = 8'h01; cpu.rom[85] = 8'h7C;
        cpu.rom[86] = 8'h40; cpu.rom[87] = 8'h23;
        cpu.rom[88] = 8'h38; cpu.rom[89] = 8'hFF;
        cpu.rom[90] = 8'h90; cpu.rom[91] = 8'h23;
        cpu.rom[92] = 8'h02; cpu.rom[93] = 8'h60;
        cpu.rom[94] = 8'h01; cpu.rom[95] = 8'h7C;
        // ROM read test
        cpu.rom[96] = 8'h40; cpu.rom[97] = 8'h80;
        cpu.rom[98] = 8'h38; cpu.rom[99] = 8'h00;
        cpu.rom[100]= 8'h90; cpu.rom[101]= 8'h40;
        cpu.rom[102]= 8'h02; cpu.rom[103]= 8'h6A;
        cpu.rom[104]= 8'h01; cpu.rom[105]= 8'h7C;
        // Page 0 register test
        cpu.rom[106]= 8'h40; cpu.rom[107]= 8'h00;
        cpu.rom[108]= 8'h30; cpu.rom[109]= 8'h77;
        cpu.rom[110]= 8'h04; cpu.rom[111]= 8'h05;
        cpu.rom[112]= 8'h30; cpu.rom[113]= 8'h00;
        cpu.rom[114]= 8'h38; cpu.rom[115]= 8'h05;
        cpu.rom[116]= 8'h90; cpu.rom[117]= 8'h77;
        cpu.rom[118]= 8'h02; cpu.rom[119]= 8'h7A;
        cpu.rom[120]= 8'h01; cpu.rom[121]= 8'h7C;
        // pass:
        cpu.rom[122]= 8'h01; cpu.rom[123]= 8'h7A;
        // fail:
        cpu.rom[124]= 8'h30; cpu.rom[125]= 8'hFF;
        cpu.rom[126]= 8'h01; cpu.rom[127]= 8'h7E;

        // Reset
        clk = 0; rst_n = 0;
        #20 rst_n = 1;

        // Run
        cycle_count = 0;
        while (!halted && cycle_count < 1000) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
        end

        if (!halted)
            $display("FAIL: Timeout after %0d cycles", cycle_count);
        else if (cpu.ac == 8'hFF)
            $display("FAIL: Test failed at cycle %0d, PC=$%04X", cycle_count, cpu.pc);
        else begin
            $display("=== SETDP TEST PASSED === (%0d cycles)", cycle_count);
            $display("  5KB RAM write/read across pages $10-$23: OK");
            $display("  ROM read via SETDP $80: OK");
            $display("  Page 0 registers: OK");
        end

        $finish;
    end
endmodule