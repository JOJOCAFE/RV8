// RV8-GR CPU — Behavioral Verilog Model
// Matches Construct.md: 29 logic chips, A15-based chip select
// Memory: ROM $8000-$FFFF, RAM $0000-$7FFF, PC starts $8000
// 3-cycle: T0=fetch ctrl, T1=fetch operand, T2=execute

module rv8gr_cpu (
    input  wire clk,
    input  wire rst_n,
    output wire halted
);
    localparam T0 = 2'd0, T1 = 2'd1, T2 = 2'd2;

    reg [1:0]  state;
    reg [15:0] pc;
    reg [7:0]  ac, ir_high, ir_low, page_reg;
    reg        z_flag, halt;

    // Memory: ROM at $8000-$FFFF, RAM at $0000-$7FFF
    reg [7:0] rom [0:32767];
    reg [7:0] ram [0:32767];

    // Control decode
    wire alu_sub = ir_high[7];
    wire xor_mode = ir_high[6];
    wire mux_sel = ir_high[5];
    wire ac_wr = ir_high[4];
    wire source_type = ir_high[3];
    wire store = ir_high[2];
    wire branch = ir_high[1];
    wire jump = ir_high[0];

    // Derived
    wire z_match = z_flag ^ alu_sub;
    wire br_taken = branch & z_match;
    wire pc_load = jump | br_taken;
    wire pg_load = mux_sel & ~ac_wr;

    // Memory read (fetch): A15 selects ROM or RAM
    wire [7:0] mem_read = pc[15] ? rom[pc[14:0]] : ram[pc[14:0]];

    // IBUS during T2: data access always at $00xx (RAM low page)
    wire [7:0] ibus = source_type ? ram[{7'b0, ir_low}] : ir_low;

    // ALU
    wire [7:0] xor_b = xor_mode ? ac : {8{alu_sub}};
    wire [7:0] xor_out = ibus ^ xor_b;
    wire [8:0] adder_full = {1'b0, ac} + {1'b0, xor_out} + {8'b0, alu_sub};
    wire [7:0] adder_sum = adder_full[7:0];
    wire [7:0] ac_mux = mux_sel ? xor_out : adder_sum;

    // Halt: J to self
    wire is_halt = jump & ~branch & ~store & ~ac_wr &
                   (ir_low == (pc[7:0] - 8'd2)) & (page_reg == pc[15:8]);

    assign halted = halt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= T0;
            pc <= 16'h8000;
            ac <= 8'h00;
            ir_high <= 8'h00;
            ir_low <= 8'h00;
            page_reg <= 8'h80;  // start in ROM page
            z_flag <= 1'b1;
            halt <= 1'b0;
        end else if (!halt) begin
            case (state)
                T0: begin
                    ir_high <= mem_read;
                    pc <= pc + 1;
                    state <= T1;
                end
                T1: begin
                    ir_low <= mem_read;
                    pc <= pc + 1;
                    state <= T2;
                end
                T2: begin
                    if (store)
                        ram[{7'b0, ir_low}] <= ac;
                    if (ac_wr) begin
                        ac <= ac_mux;
                        z_flag <= (ac_mux == 8'h00);
                    end
                    if (pg_load)
                        page_reg <= ibus;
                    if (pc_load)
                        pc <= {page_reg, ir_low};
                    if (is_halt)
                        halt <= 1'b1;
                    state <= T0;
                end
                default: state <= T0;
            endcase
        end
    end
endmodule
