`timescale 1ns / 1ps
// RV8-R — 18-chip RISC-V style 8-bit CPU (behavioral model)
// Registers in RAM ($0000-$0007), microcode-driven, register cache

module rv8r_cpu (
    input  wire        clk,
    input  wire        rst_n,
    output reg  [15:0] addr,
    output reg  [7:0]  data_out,
    input  wire [7:0]  data_in,
    output reg         mem_rd,
    output reg         mem_wr
);

// --- Internal state ---
reg [15:0] pc;
reg [7:0]  ir;
reg [7:0]  opr;
reg [7:0]  reg_a, reg_b;
reg [7:0]  addr_lo;
reg        flag_z, flag_c;
reg [2:0]  step;
reg        halt;

// --- Decode ---
wire [1:0] iclass = ir[7:6];
wire [2:0] op     = ir[5:3];
wire [2:0] rd     = ir[2:0];
wire [2:0] rs     = opr[7:5];
wire [4:0] off5   = opr[4:0];

// Sign-extend
wire [15:0] sext8  = {{8{opr[7]}}, opr};
wire [7:0]  sext5  = {{3{off5[4]}}, off5};
wire [15:0] sext5_16 = {{11{off5[4]}}, off5};  // 5-bit sign-ext to 16

// --- ALU ---
function [8:0] alu;
    input [7:0] a, b;
    input [2:0] op;
    begin
        case (op)
            3'd0: alu = {1'b0, a} + {1'b0, b};   // ADD
            3'd1: alu = {1'b0, a} - {1'b0, b};   // SUB
            3'd2: alu = {1'b0, a ^ b};            // XOR
            3'd3: alu = {1'b0, a & b};            // AND
            3'd4: alu = {1'b0, a | b};            // OR
            3'd5: alu = {1'b0, a};                // PASS A
            3'd6: alu = {1'b0, b};                // PASS B
            3'd7: alu = {1'b0, ~a};               // NOT
            default: alu = 9'd0;
        endcase
    end
endfunction

// --- Main FSM ---
reg [8:0] result;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc <= 16'h8000;
        ir <= 0; opr <= 0;
        reg_a <= 0; reg_b <= 0;
        addr_lo <= 0;
        flag_z <= 0; flag_c <= 0;
        step <= 0;
        halt <= 0;
        addr <= 0; data_out <= 0;
        mem_rd <= 0; mem_wr <= 0;
    end else if (!halt) begin
        mem_rd <= 0;
        mem_wr <= 0;

        case (step)
        // ═══ FETCH ═══
        3'd0: begin
            addr <= pc;
            mem_rd <= 1;
            step <= 1;
        end
        3'd1: begin
            ir <= data_in;
            pc <= pc + 1;
            addr <= pc + 1;
            mem_rd <= 1;
            step <= 2;
        end
        3'd2: begin
            opr <= data_in;
            pc <= pc + 1;
            step <= 3;
        end

        // ═══ EXECUTE step 3 ═══
        3'd3: begin
            case (iclass)
            // ─── Class 01: Immediate ───
            2'b01: begin
                if (op == 3'd0) begin
                    // LI rd, imm → write imm to RAM[rd]
                    addr <= {13'd0, ir[2:0]};
                    data_out <= opr;
                    mem_wr <= 1;
                    step <= 0;
                end else begin
                    // Other imm ops: load immediate into REG_B, read rd
                    reg_b <= opr;
                    addr <= {13'd0, ir[2:0]};
                    mem_rd <= 1;
                    step <= 4;
                end
            end
            // ─── Class 00: Register-Register ───
            2'b00: begin
                // Read rs from RAM
                addr <= {13'd0, opr[7:5]};
                mem_rd <= 1;
                step <= 4;
            end
            // ─── Class 10: Memory ───
            2'b10: begin
                case (op)
                3'd0, 3'd1: begin // LB/SB off(rs) — read rs
                    addr <= {13'd0, opr[7:5]};
                    mem_rd <= 1;
                    step <= 4;
                end
                3'd2: begin // LB zp — read from {0, imm8}
                    addr <= {8'h00, opr};
                    mem_rd <= 1;
                    step <= 6;
                end
                3'd3: begin // SB zp — read rd value
                    addr <= {13'd0, ir[2:0]};
                    mem_rd <= 1;
                    step <= 4;
                end
                3'd4, 3'd5: begin // PUSH/POP — read SP (r7)
                    addr <= 16'h0007;
                    mem_rd <= 1;
                    step <= 4;
                end
                3'd6, 3'd7: begin // LB/SB off(sp) — read SP
                    addr <= 16'h0007;
                    mem_rd <= 1;
                    step <= 4;
                end
                endcase
            end
            // ─── Class 11: Branch/Jump ───
            2'b11: begin
                case (op)
                3'd0, 3'd1, 3'd2, 3'd3: begin // BEQ/BNE/BLT/BGE — read rs1
                    addr <= {13'd0, ir[2:0]};
                    mem_rd <= 1;
                    step <= 4;
                end
                3'd4: begin // JAL rd, off8 — save PC, jump
                    addr <= {13'd0, ir[2:0]};
                    data_out <= pc[7:0];
                    mem_wr <= 1;
                    pc <= pc + sext8;
                    step <= 0;
                end
                3'd5: begin // JALR — save PC first
                    addr <= {13'd0, ir[2:0]};
                    data_out <= pc[7:0];
                    mem_wr <= 1;
                    step <= 4;
                end
                3'd6: begin // J off8
                    pc <= pc + sext8;
                    step <= 0;
                end
                3'd7: begin // SYS
                    if (opr == 8'h01) halt <= 1;
                    step <= 0;
                end
                endcase
            end
            endcase
        end

        // ═══ EXECUTE step 4 ═══
        3'd4: begin
            case (iclass)
            2'b01: begin // Immediate ALU — rd value arrived
                reg_a <= data_in;
                step <= 5;
            end
            2'b00: begin // Reg-Reg — rs value arrived, now read rd
                reg_b <= data_in;
                addr <= {13'd0, ir[2:0]};
                mem_rd <= 1;
                step <= 5;
            end
            2'b10: begin
                case (op)
                3'd0: begin // LB off(rs) — rs val arrived, compute addr, read mem
                    addr <= {8'h00, data_in + sext5};
                    mem_rd <= 1;
                    step <= 6;
                end
                3'd1: begin // SB off(rs) — rs val arrived, compute addr, read rd
                    addr_lo <= data_in + sext5;
                    addr <= {13'd0, ir[2:0]};
                    mem_rd <= 1;
                    step <= 5;
                end
                3'd3: begin // SB zp — rd value arrived, write to addr
                    addr <= {8'h00, opr};
                    data_out <= data_in;
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd4: begin // PUSH — SP arrived, dec SP, save new SP
                    reg_a <= data_in;
                    addr_lo <= data_in - 8'd1;
                    addr <= 16'h0007;
                    data_out <= data_in - 8'd1;
                    mem_wr <= 1;
                    step <= 5;
                end
                3'd5: begin // POP — SP arrived, read stack[SP]
                    reg_a <= data_in;
                    addr <= {8'h00, data_in};
                    mem_rd <= 1;
                    step <= 6;
                end
                3'd6: begin // LB off(sp) — SP arrived, compute addr
                    addr <= {8'h00, data_in + sext5};
                    mem_rd <= 1;
                    step <= 6;
                end
                3'd7: begin // SB off(sp) — SP arrived, read rd
                    addr_lo <= data_in + sext5;
                    addr <= {13'd0, ir[2:0]};
                    mem_rd <= 1;
                    step <= 5;
                end
                endcase
            end
            2'b11: begin
                case (op)
                3'd0, 3'd1, 3'd2, 3'd3: begin // Branch — rs1 arrived, read rs2
                    reg_a <= data_in;
                    addr <= {13'd0, opr[7:5]};
                    mem_rd <= 1;
                    step <= 5;
                end
                3'd5: begin // JALR — PC saved, now read rs
                    addr <= {13'd0, opr[7:5]};
                    mem_rd <= 1;
                    step <= 5;
                end
                endcase
            end
            endcase
        end

        // ═══ EXECUTE step 5 ═══
        3'd5: begin
            case (iclass)
            2'b01: begin // Immediate ALU — compute and writeback
                case (op)
                3'd1: result = alu(reg_a, reg_b, 3'd0); // ADDI
                3'd2: result = alu(reg_a, reg_b, 3'd1); // SUBI
                3'd3: result = alu(reg_a, reg_b, 3'd3); // ANDI
                3'd4: result = alu(reg_a, reg_b, 3'd4); // ORI
                3'd5: result = alu(reg_a, reg_b, 3'd2); // XORI
                3'd6: begin // SLTI
                    result = alu(reg_a, reg_b, 3'd1);
                    flag_z <= (result[7:0] == 0);
                    flag_c <= result[8];
                    addr <= {13'd0, ir[2:0]};
                    data_out <= result[8] ? 8'd1 : 8'd0;
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd7: begin // LUI
                    addr <= {13'd0, ir[2:0]};
                    data_out <= {opr[3:0], 4'b0};
                    mem_wr <= 1;
                    step <= 0;
                end
                default: result = 9'd0;
                endcase
                if (op >= 3'd1 && op <= 3'd5) begin
                    flag_z <= (result[7:0] == 0);
                    flag_c <= result[8];
                    addr <= {13'd0, ir[2:0]};
                    data_out <= result[7:0];
                    mem_wr <= 1;
                    step <= 0;
                end
            end
            2'b00: begin // Reg-Reg — rd value arrived, compute
                reg_a <= data_in;
                case (op)
                3'd0: result = alu(data_in, reg_b, 3'd0); // ADD
                3'd1: result = alu(data_in, reg_b, 3'd1); // SUB
                3'd2: result = alu(data_in, reg_b, 3'd3); // AND
                3'd3: result = alu(data_in, reg_b, 3'd4); // OR
                3'd4: result = alu(data_in, reg_b, 3'd2); // XOR
                3'd5: begin // SLT
                    result = alu(data_in, reg_b, 3'd1);
                    flag_z <= (result[7:0] == 0);
                    flag_c <= result[8];
                    addr <= {13'd0, ir[2:0]};
                    data_out <= result[8] ? 8'd1 : 8'd0;
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd6: begin // SLL = rd + rd
                    result = alu(data_in, data_in, 3'd0);
                    flag_z <= (result[7:0] == 0);
                    flag_c <= result[8];
                    addr <= {13'd0, ir[2:0]};
                    data_out <= result[7:0];
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd7: begin // SRL = shift right
                    result = {data_in[0], 1'b0, data_in[7:1]};
                    flag_z <= (result[7:0] == 0);
                    flag_c <= data_in[0];
                    addr <= {13'd0, ir[2:0]};
                    data_out <= result[7:0];
                    mem_wr <= 1;
                    step <= 0;
                end
                default: result = 9'd0;
                endcase
                if (op <= 3'd4) begin
                    flag_z <= (result[7:0] == 0);
                    flag_c <= result[8];
                    addr <= {13'd0, ir[2:0]};
                    data_out <= result[7:0];
                    mem_wr <= 1;
                    step <= 0;
                end
            end
            2'b10: begin
                case (op)
                3'd1: begin // SB off(rs) — rd val arrived, write to mem
                    addr <= {8'h00, addr_lo};
                    data_out <= data_in;
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd4: begin // PUSH — SP saved, read rd
                    addr <= {13'd0, ir[2:0]};
                    mem_rd <= 1;
                    step <= 6;
                end
                3'd7: begin // SB off(sp) — rd val arrived, write
                    addr <= {8'h00, addr_lo};
                    data_out <= data_in;
                    mem_wr <= 1;
                    step <= 0;
                end
                default: step <= 0;
                endcase
            end
            2'b11: begin
                case (op)
                3'd0, 3'd1, 3'd2, 3'd3: begin // Branch — rs2 arrived, compare
                    reg_b <= data_in;
                    result = alu(reg_a, data_in, 3'd1); // SUB
                    flag_z <= (result[7:0] == 0);
                    flag_c <= result[8];
                    case (op)
                    3'd0: if (result[7:0] == 0) pc <= pc + sext5_16; // BEQ
                    3'd1: if (result[7:0] != 0) pc <= pc + sext5_16; // BNE
                    3'd2: if (result[8])         pc <= pc + sext5_16; // BLT
                    3'd3: if (!result[8])        pc <= pc + sext5_16; // BGE
                    endcase
                    step <= 0;
                end
                3'd5: begin // JALR — rs value arrived, jump
                    pc <= {8'h00, data_in};
                    step <= 0;
                end
                endcase
            end
            endcase
        end

        // ═══ EXECUTE step 6 ═══
        3'd6: begin
            case (iclass)
            2'b10: begin
                case (op)
                3'd0, 3'd2, 3'd6: begin // LB variants — data arrived, write to rd
                    addr <= {13'd0, ir[2:0]};
                    data_out <= data_in;
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd4: begin // PUSH — rd value arrived, write to stack
                    addr <= {8'h00, addr_lo};
                    data_out <= data_in;
                    mem_wr <= 1;
                    step <= 0;
                end
                3'd5: begin // POP — stack data arrived, write to rd
                    reg_a <= reg_a + 8'd1; // new SP
                    addr <= {13'd0, ir[2:0]};
                    data_out <= data_in;
                    mem_wr <= 1;
                    step <= 7;
                end
                default: step <= 0;
                endcase
            end
            default: step <= 0;
            endcase
        end

        // ═══ EXECUTE step 7 ═══
        3'd7: begin
            case (iclass)
            2'b10: begin
                case (op)
                3'd5: begin // POP — write incremented SP back
                    addr <= 16'h0007;
                    data_out <= reg_a;
                    mem_wr <= 1;
                    step <= 0;
                end
                default: step <= 0;
                endcase
            end
            default: step <= 0;
            endcase
        end
        endcase

        // r0 protection: if we just wrote to addr 0, it stays 0
        // (handled by writing 0 back — or gate in hardware)
    end
end

// r0 write protection: override any write to address 0
always @(posedge clk) begin
    if (mem_wr && addr == 16'h0000) begin
        // In real hardware: AND gate blocks WR when addr[2:0]=000 & addr[15:3]=0
        // In simulation: let it happen but the testbench memory can enforce it
    end
end

endmodule
