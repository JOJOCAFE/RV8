// RV8-GR exhaustive horizontal-control opcode sweep.
//
// Tests all 256 opcodes × Z={0,1} by directly setting internal state to T2
// and clocking once. Expected results are calculated from the physical
// control equations in doc/00_design_isa.md.
//
// NOTE: This test bypasses fetch (T0/T1) and tests pure T2 execution logic.
`timescale 1ns/1ps

module tb_rv8gr_opcode_sweep;
    reg clk, rst_n;
    wire halted;

    rv8gr_cpu cpu(.clk(clk), .rst_n(rst_n), .irq_n(1'b1), .halted(halted));

    // Test constants
    localparam [7:0]  INIT_AC  = 8'h3C;
    localparam [7:0]  INIT_PG  = 8'h12;
    localparam [7:0]  INIT_DP  = 8'h80;  // data page → RAM $8000+
    localparam [7:0]  OPERAND  = 8'h5A;
    localparam [7:0]  RAM_VAL  = 8'hA6;  // pre-loaded at RAM[$805A]
    localparam [15:0] INIT_PC  = 16'h1234;
    localparam [15:0] TARGET   = {INIT_PG, OPERAND};  // $125A

    integer i, z;
    integer errors, cases;

    reg [7:0] op;
    reg init_z;

    // Expected values
    reg [7:0] exp_ibus, exp_xor_b, exp_xor, exp_ac;
    reg [8:0] exp_sum;
    reg exp_z, exp_pc_load;
    reg [7:0] exp_pg, exp_dp;
    reg exp_ie;
    reg [15:0] exp_pc;
    reg [7:0] exp_ram;
    reg [7:0] exp_ac_mux;

    task setup;
    begin
        clk = 0;
        rst_n = 1;
        // Force CPU to T2 with known state
        cpu.state = 2'd2;
        cpu.pc = INIT_PC;
        cpu.ac = INIT_AC;
        cpu.ir_high = op;
        cpu.ir_low = OPERAND;
        cpu.page_reg = INIT_PG;
        cpu.data_page_reg = INIT_DP;
        cpu.z_flag = init_z;
        cpu.halt = 0;
        cpu.ie = 1'b0;  // IRQ disabled
        cpu.irq_ff = 0;
        // Pre-load RAM at data address {DP, OPERAND} = {$80, $5A} → ram[14:0] = $005A
        cpu.ram[15'h005A] = RAM_VAL;
    end
    endtask

    task calc_expected;
    begin
        // IBUS: SRC=1 → RAM[{DP,operand}], SRC=0 → operand
        exp_ibus = op[3] ? RAM_VAL : OPERAND;

        // XOR B-input: XOR_MODE=1 → AC, XOR_MODE=0 → {8{SUB}}
        exp_xor_b = op[6] ? INIT_AC : {8{op[7]}};
        exp_xor = exp_ibus ^ exp_xor_b;
        exp_sum = {1'b0, INIT_AC} + {1'b0, exp_xor} + {8'b0, op[7]};
        exp_ac_mux = op[5] ? exp_xor : exp_sum[7:0];

        // AC write
        exp_ac = op[4] ? exp_ac_mux : INIT_AC;

        // Z flag
        exp_z = op[4] ? (exp_ac == 8'h00) : init_z;

        // Page register: pg_load = MUX_SEL & ~AC_WR & ~XOR_MODE
        if (op[5] && !op[4] && !op[6])
            exp_pg = exp_ibus;
        else
            exp_pg = INIT_PG;

        // Data page: SETDP = ir_high == $40 (XOR=1, MUX=0, AC_WR=0, rest=0)
        if (op == 8'h40)
            exp_dp = OPERAND;
        else
            exp_dp = INIT_DP;

        // IE: EI ($08) sets, DI ($48) clears
        if (op == 8'h08)
            exp_ie = 1'b1;
        else if (op == 8'h48)
            exp_ie = 1'b0;
        else
            exp_ie = 1'b0;  // started disabled

        // PC load: jump | (branch & z_match)
        // z_match = z_flag ^ alu_sub
        exp_pc_load = op[0] | (op[1] & (init_z ^ op[7]));
        exp_pc = exp_pc_load ? TARGET : INIT_PC;

        // Store: writes AC to RAM if store=1 and data_addr[15]=1
        // data_addr = {DP, operand} = {$80, $5A} → A15=1 → RAM write
        exp_ram = op[2] ? INIT_AC : RAM_VAL;
    end
    endtask

    task check;
    begin
        if (cpu.ac !== exp_ac ||
            cpu.z_flag !== exp_z ||
            cpu.page_reg !== exp_pg ||
            cpu.data_page_reg !== exp_dp ||
            cpu.ie !== exp_ie ||
            cpu.pc !== exp_pc ||
            cpu.ram[15'h005A] !== exp_ram) begin
            errors = errors + 1;
            $display("FAIL op=$%02X Z=%b: AC=%02X(exp %02X) Z=%b(%b) PG=%02X(%02X) DP=%02X(%02X) IE=%b(%b) PC=%04X(%04X) RAM=%02X(%02X)",
                op, init_z,
                cpu.ac, exp_ac,
                cpu.z_flag, exp_z,
                cpu.page_reg, exp_pg,
                cpu.data_page_reg, exp_dp,
                cpu.ie, exp_ie,
                cpu.pc, exp_pc,
                cpu.ram[15'h005A], exp_ram);
        end
    end
    endtask

    initial begin
        errors = 0;
        cases = 0;
        clk = 0;
        rst_n = 0;
        #2 rst_n = 1;

        for (i = 0; i < 256; i = i + 1) begin
            for (z = 0; z < 2; z = z + 1) begin
                op = i[7:0];
                init_z = z[0];

                setup;
                calc_expected;

                #2 clk = 1;
                #2 clk = 0;

                check;
                cases = cases + 1;
            end
        end

        if (errors != 0) begin
            $display("=== OPCODE SWEEP FAILED: %0d errors in %0d cases ===", errors, cases);
            $fatal(1);
        end

        $display("=== OPCODE SWEEP PASSED: %0d cases (256 opcodes x Z=0/1) ===", cases);
        $finish;
    end
endmodule
