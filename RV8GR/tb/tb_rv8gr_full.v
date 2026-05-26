// RV8-GR Testbench — Full ISA + 64K jump + subroutine test
`timescale 1ns/1ps

module tb_rv8gr;
    reg clk, rst_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .halted(halted));

    // Clock: 100MHz (10ns period)
    always #5 clk = ~clk;

    integer cycle_count;
    integer i;

    initial begin
        $dumpfile("rv8gr_test.vcd");
        $dumpvars(0, tb_rv8gr);

        // Clear ROM and RAM
        for (i = 0; i < 32768; i = i + 1) cpu.rom[i] = 8'h00;
        for (i = 0; i < 32768; i = i + 1) cpu.ram[i] = 8'h00;

        // ROM at $8000-$FFFF → rom[addr - $8000] = rom[addr[14:0]]
        // RAM at $0000-$7FFF → ram[addr[14:0]]

        // === Page $80 ($8000+) — Main test (PC starts here) ===
        cpu.rom[15'h0000] = 8'h30; cpu.rom[15'h0001] = 8'h00; // LI $00
        cpu.rom[15'h0002] = 8'h02; cpu.rom[15'h0003] = 8'h08; // BEQ $08
        cpu.rom[15'h0004] = 8'h01; cpu.rom[15'h0005] = 8'h04; // FAIL halt
        cpu.rom[15'h0008] = 8'h30; cpu.rom[15'h0009] = 8'h05; // LI $05
        cpu.rom[15'h000A] = 8'h82; cpu.rom[15'h000B] = 8'h10; // BNE $10
        cpu.rom[15'h000C] = 8'h01; cpu.rom[15'h000D] = 8'h0C; // FAIL halt
        cpu.rom[15'h0010] = 8'h10; cpu.rom[15'h0011] = 8'h03; // ADDI $03
        cpu.rom[15'h0012] = 8'h90; cpu.rom[15'h0013] = 8'h08; // SUBI $08
        cpu.rom[15'h0014] = 8'h70; cpu.rom[15'h0015] = 8'hAA; // XORI $AA
        cpu.rom[15'h0016] = 8'h04; cpu.rom[15'h0017] = 8'h00; // MV $00,a0
        cpu.rom[15'h0018] = 8'h30; cpu.rom[15'h0019] = 8'h00; // LI $00
        cpu.rom[15'h001A] = 8'h38; cpu.rom[15'h001B] = 8'h00; // MV a0,$00
        cpu.rom[15'h001C] = 8'h90; cpu.rom[15'h001D] = 8'hAA; // SUBI $AA
        cpu.rom[15'h001E] = 8'h02; cpu.rom[15'h001F] = 8'h22; // BEQ $22
        cpu.rom[15'h0020] = 8'h01; cpu.rom[15'h0021] = 8'h20; // FAIL halt
        cpu.rom[15'h0022] = 8'h30; cpu.rom[15'h0023] = 8'h55; // LI $55
        cpu.rom[15'h0024] = 8'h04; cpu.rom[15'h0025] = 8'h01; // MV $01,a0
        cpu.rom[15'h0026] = 8'h18; cpu.rom[15'h0027] = 8'h01; // ADD $01
        cpu.rom[15'h0028] = 8'h98; cpu.rom[15'h0029] = 8'h00; // SUB $00
        cpu.rom[15'h002A] = 8'h02; cpu.rom[15'h002B] = 8'h2E; // BEQ $2E
        cpu.rom[15'h002C] = 8'h01; cpu.rom[15'h002D] = 8'h2C; // FAIL halt
        cpu.rom[15'h002E] = 8'h30; cpu.rom[15'h002F] = 8'hFF; // LI $FF
        cpu.rom[15'h0030] = 8'h04; cpu.rom[15'h0031] = 8'h02; // MV $02,a0
        cpu.rom[15'h0032] = 8'h78; cpu.rom[15'h0033] = 8'h02; // XOR $02
        cpu.rom[15'h0034] = 8'h02; cpu.rom[15'h0035] = 8'h38; // BEQ $38
        cpu.rom[15'h0036] = 8'h01; cpu.rom[15'h0037] = 8'h36; // FAIL halt
        // Jump to page $90 (still in ROM: $9000)
        cpu.rom[15'h0038] = 8'h20; cpu.rom[15'h0039] = 8'h90; // SETPG $90
        cpu.rom[15'h003A] = 8'h01; cpu.rom[15'h003B] = 8'h00; // J $00 → $9000

        // === Page $90 ($9000, ROM offset $1000) ===
        cpu.rom[15'h1000] = 8'h20; cpu.rom[15'h1001] = 8'hFF; // SETPG $FF
        cpu.rom[15'h1002] = 8'h01; cpu.rom[15'h1003] = 8'h00; // J $00 → $FF00

        // === Page $FF ($FF00, ROM offset $7F00) ===
        cpu.rom[15'h7F00] = 8'h20; cpu.rom[15'h7F01] = 8'h80; // SETPG $80
        cpu.rom[15'h7F02] = 8'h01; cpu.rom[15'h7F03] = 8'h40; // J $40 → $8040

        // === Back at $8040 — subroutine test ===
        cpu.rom[15'h0040] = 8'h30; cpu.rom[15'h0041] = 8'h00; // LI $00
        cpu.rom[15'h0042] = 8'h04; cpu.rom[15'h0043] = 8'h04; // MV $04,a0
        cpu.rom[15'h0044] = 8'h28; cpu.rom[15'h0045] = 8'h04; // SETPG_R $04 (PG=RAM[4]=0)
        cpu.rom[15'h0046] = 8'h20; cpu.rom[15'h0047] = 8'h80; // SETPG $80 (back to ROM page)
        cpu.rom[15'h0048] = 8'h30; cpu.rom[15'h0049] = 8'h5E; // LI $5E (return addr)
        cpu.rom[15'h004A] = 8'h04; cpu.rom[15'h004B] = 8'h07; // MV $07,a0 (save ret)
        cpu.rom[15'h004C] = 8'h01; cpu.rom[15'h004D] = 8'h70; // J $70 (call sub)
        // Return point $805E:
        cpu.rom[15'h005E] = 8'h38; cpu.rom[15'h005F] = 8'h05; // MV a0,$05
        cpu.rom[15'h0060] = 8'h90; cpu.rom[15'h0061] = 8'h42; // SUBI $42
        cpu.rom[15'h0062] = 8'h02; cpu.rom[15'h0063] = 8'h66; // BEQ $66 → PASS
        cpu.rom[15'h0064] = 8'h01; cpu.rom[15'h0065] = 8'h64; // FAIL halt
        cpu.rom[15'h0066] = 8'h01; cpu.rom[15'h0067] = 8'h66; // ALL PASS halt

        // Subroutine at $8070:
        cpu.rom[15'h0070] = 8'h30; cpu.rom[15'h0071] = 8'h42; // LI $42
        cpu.rom[15'h0072] = 8'h04; cpu.rom[15'h0073] = 8'h05; // MV $05,a0
        cpu.rom[15'h0074] = 8'h20; cpu.rom[15'h0075] = 8'h80; // SETPG $80
        cpu.rom[15'h0076] = 8'h01; cpu.rom[15'h0077] = 8'h5E; // J $5E (return)

        // Run simulation
        clk = 0;
        rst_n = 0;
        #20 rst_n = 1;

        cycle_count = 0;
        while (!halted && cycle_count < 500) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
        end

        // Check result
        if (cpu.pc == 16'h8066 || cpu.pc == 16'h8067) begin
            $display("=== ALL TESTS PASSED === (%0d cycles)", cycle_count);
            $display("  Final: AC=$%02X Z=%b PG=$%02X PC=$%04X",
                     cpu.ac, cpu.z_flag, cpu.page_reg, cpu.pc);
        end else begin
            $display("=== FAILED at PC=$%04X === (%0d cycles)", cpu.pc, cycle_count);
            $display("  AC=$%02X Z=%b PG=$%02X", cpu.ac, cpu.z_flag, cpu.page_reg);
            $display("  IR_HIGH=$%02X IR_LOW=$%02X", cpu.ir_high, cpu.ir_low);
        end

        $finish;
    end
endmodule
