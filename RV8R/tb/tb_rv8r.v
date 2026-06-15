`timescale 1ns / 1ps
// RV8-R Testbench — tests all instruction classes

module tb_rv8r;

reg clk, rst_n;
wire [15:0] addr;
wire [7:0] data_out;
wire mem_rd, mem_wr;
reg [7:0] data_in;

rv8r_cpu uut (
    .clk(clk), .rst_n(rst_n),
    .addr(addr), .data_out(data_out), .data_in(data_in),
    .mem_rd(mem_rd), .mem_wr(mem_wr)
);

// --- Memory (64KB) ---
reg [7:0] mem [0:65535];

// Memory read (active when mem_rd or address changes)
always @(*) begin
    data_in = mem[addr];
end

// Memory write
always @(posedge clk) begin
    if (mem_wr && addr != 16'h0000) begin // r0 protection
        mem[addr] <= data_out;
    end
end

// --- Clock ---
initial clk = 0;
always #5 clk = ~clk; // 100MHz sim clock

// --- Test ---
integer i, errors;
integer cycle_count;

task load_program;
    input [15:0] start;
    input [15:0] len;
    reg [15:0] a;
    begin
        // Program is pre-loaded into mem[]
    end
endtask

task wait_halt;
    input integer max_cycles;
    begin
        cycle_count = 0;
        while (!uut.halt && cycle_count < max_cycles) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
            // Debug: trace instruction fetch
            if (uut.step == 3'd1 && cycle_count < 200)
                $display("  [%0d] FETCH ir=%02X @ PC=%04X", cycle_count, data_in, uut.pc);
        end
    end
endtask

task check_reg;
    input [2:0] rn;
    input [7:0] expected;
    begin
        if (mem[rn] !== expected) begin
            $display("FAIL: r%0d = $%02X, expected $%02X", rn, mem[rn], expected);
            errors = errors + 1;
        end else begin
            $display("  OK: r%0d = $%02X", rn, mem[rn]);
        end
    end
endtask

task check_mem_val;
    input [15:0] a;
    input [7:0] expected;
    begin
        if (mem[a] !== expected) begin
            $display("FAIL: mem[$%04X] = $%02X, expected $%02X", a, mem[a], expected);
            errors = errors + 1;
        end else begin
            $display("  OK: mem[$%04X] = $%02X", a, mem[a]);
        end
    end
endtask

initial begin
    $dumpfile("rv8r_tb.vcd");
    $dumpvars(0, tb_rv8r);
    errors = 0;

    // Clear memory
    for (i = 0; i < 65536; i = i + 1) mem[i] = 8'h00;

    // === TEST PROGRAM ===
    // Loaded at $8000 (ROM area)
    //
    // Test 1: LI r1, $42
    mem[16'h8000] = 8'h41; // LI rd=1 (01_000_001)
    mem[16'h8001] = 8'h42; // imm = $42
    //
    // Test 2: LI r2, $10
    mem[16'h8002] = 8'h42; // LI rd=2
    mem[16'h8003] = 8'h10; // imm = $10
    //
    // Test 3: ADD r2, r1 → r2 = $10 + $42 = $52
    mem[16'h8004] = 8'h02; // ADD rd=2 (00_000_010)
    mem[16'h8005] = 8'h20; // rs=1 (001_00000)
    //
    // Test 4: SUBI r2, $02 → r2 = $52 - $02 = $50
    mem[16'h8006] = 8'h52; // SUBI rd=2 (01_010_010)
    mem[16'h8007] = 8'h02; // imm = $02
    //
    // Test 5: ADDI r3, $05 → r3 = $00 + $05 = $05
    mem[16'h8008] = 8'h4B; // ADDI rd=3 (01_001_011)
    mem[16'h8009] = 8'h05; // imm = $05
    //
    // Test 6: SB r2, [$20] (zero-page) → mem[$20] = $50
    mem[16'h800A] = 8'h9A; // SB zp rd=2 (10_011_010)
    mem[16'h800B] = 8'h20; // addr = $20
    //
    // Test 7: LB r4, [$20] → r4 = $50
    mem[16'h800C] = 8'h94; // LB zp rd=4 (10_010_100)
    mem[16'h800D] = 8'h20; // addr = $20
    //
    // Test 8: XOR r4, r4 → r4 = 0 (clear)
    mem[16'h800E] = 8'h24; // XOR rd=4 (00_100_100)
    mem[16'h800F] = 8'h80; // rs=4 (100_00000)
    //
    // Test 9: XORI r1, $FF → r1 = $42 ^ $FF = $BD
    mem[16'h8010] = 8'h69; // XORI rd=1 (01_101_001)
    mem[16'h8011] = 8'hFF; // imm = $FF
    //
    // Test 10: SLL r3 → r3 = $05 << 1 = $0A
    // SLL encodes as class00, op=110, rd=3, rs=3 (assembler sets rs=rd)
    mem[16'h8012] = 8'h33; // SLL rd=3 (00_110_011)
    mem[16'h8013] = 8'h60; // rs=3 (011_00000)
    //
    // Test 11: J +2 (skip next instruction)
    mem[16'h8014] = 8'hF0; // J (11_110_000)
    mem[16'h8015] = 8'h02; // off8 = +2
    // This skipped instruction:
    mem[16'h8016] = 8'h41; // LI r1, $FF (should NOT execute)
    mem[16'h8017] = 8'hFF;
    //
    // Test 12: BEQ r0, r0, +2 (r0==r0, always taken)
    mem[16'h8018] = 8'hC0; // BEQ rs1=r0 (11_000_000)
    mem[16'h8019] = 8'h02; // rs2=r0(000), off5=00010 → +2
    // Skipped:
    mem[16'h801A] = 8'h41; // LI r1, $EE (should NOT execute)
    mem[16'h801B] = 8'hEE;
    //
    // Test 13: BNE r1, r0, +2 (r1=$BD ≠ r0=0, taken)
    mem[16'h801C] = 8'hC9; // BNE rs1=r1 (11_001_001)
    mem[16'h801D] = 8'h02; // rs2=r0(000), off5=00010 → +2
    // Skipped:
    mem[16'h801E] = 8'h41; // LI r1, $DD (should NOT execute)
    mem[16'h801F] = 8'hDD;
    //
    // Test 14: LI r5, $03; loop: SUBI r5,$01; BNE r5,r0,loop
    mem[16'h8020] = 8'h45; // LI rd=5 (01_000_101)
    mem[16'h8021] = 8'h03; // imm = 3
    // loop ($8022):
    mem[16'h8022] = 8'h55; // SUBI rd=5 (01_010_101)
    mem[16'h8023] = 8'h01; // imm = 1
    mem[16'h8024] = 8'hCD; // BNE rs1=r5 (11_001_101)
    mem[16'h8025] = 8'h1C; // rs2=r0(000), off5=11100 = -4 (signed 5-bit)
    // After loop: r5 = 0
    //
    // Test 15: PUSH/POP
    // Set SP (r7) to $80 first
    mem[16'h8026] = 8'h47; // LI rd=7 (01_000_111) — set SP
    mem[16'h8027] = 8'h80; // SP = $80
    // LI r6, $AA
    mem[16'h8028] = 8'h46; // LI rd=6
    mem[16'h8029] = 8'hAA;
    // PUSH r6
    mem[16'h802A] = 8'hA6; // PUSH rd=6 (10_100_110)
    mem[16'h802B] = 8'hE0; // rs=7(sp), unused
    // LI r6, $00 (clear r6)
    mem[16'h802C] = 8'h46; // LI rd=6
    mem[16'h802D] = 8'h00;
    // POP r6 — should restore $AA
    mem[16'h802E] = 8'hAE; // POP rd=6 (10_101_110)
    mem[16'h802F] = 8'hE0; // rs=7(sp)
    //
    // HLT
    mem[16'h8030] = 8'hF8; // SYS (11_111_000)
    mem[16'h8031] = 8'h01; // HLT

    // --- RUN ---
    rst_n = 0;
    repeat(3) @(posedge clk);
    rst_n = 1;

    wait_halt(2000);

    $display("");
    $display("═══════════════════════════════════════");
    $display("RV8-R CPU Test Results (%0d cycles)", cycle_count);
    $display("═══════════════════════════════════════");

    // Check results
    $display("Test 1: LI r1, $42");
    check_reg(1, 8'hBD); // After XORI $FF: $42^$FF=$BD

    $display("Test 2-4: ADD/SUBI → r2 = $50");
    check_reg(2, 8'h50);

    $display("Test 5: ADDI r3, $05 then SLL → r3 = $0A");
    check_reg(3, 8'h0A);

    $display("Test 6: SB [$20] = $50");
    check_mem_val(16'h0020, 8'h50);

    $display("Test 8: XOR r4, r4 → 0");
    check_reg(4, 8'h00);

    $display("Test 9: r1 = $42 ^ $FF = $BD");
    // r1 was $42, then XORI $FF = $BD. J and BEQ/BNE should NOT have changed it.
    check_reg(1, 8'hBD);

    $display("Test 14: loop SUBI → r5 = 0");
    check_reg(5, 8'h00);

    $display("Test 15: PUSH/POP r6 = $AA");
    check_reg(6, 8'hAA);

    $display("SP after PUSH+POP:");
    check_reg(7, 8'h80); // SP should be back to $80

    $display("");
    if (errors == 0)
        $display("ALL TESTS PASSED (%0d cycles)", cycle_count);
    else
        $display("FAILED: %0d errors", errors);
    $display("═══════════════════════════════════════");

    $finish;
end

endmodule
