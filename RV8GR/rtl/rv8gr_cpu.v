// RV8-GR CPU — Behavioral Verilog Model
// Matches 03_wiring_guide.md: 31 logic chips (incl. U31 IRQ, U32 Data Page)
// Memory: ROM $8000-$FFFF, RAM $0000-$7FFF, PC starts $8000
// 3-cycle: T0=fetch ctrl, T1=fetch operand, T2=execute
// 18 instructions (17 + SETDP)
// IRQ: fixed vector $FF00, IE flag, auto-save PC to RAM[$0E:$0F]
// Guard: BUF_OE_SAFE = BUF_OE_N OR STR (U25 gate 3 → U7-19)
// Data Page: U32 74HC574, SETDP $40 → full 64KB data access (ROM+RAM)

module rv8gr_cpu (
    input  wire clk,
    input  wire rst_n,
    input  wire irq_n,      // active-low interrupt request
    output wire halted
);
    localparam T0 = 2'd0, T1 = 2'd1, T2 = 2'd2;

    reg [1:0]  state;
    reg [15:0] pc;
    reg [7:0]  ac, ir_high, ir_low, page_reg, data_page_reg;
    reg        z_flag, halt;
    reg        ie, irq_ff;  // interrupt enable, IRQ latch (74HC74)

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

    // EI/DI/SETDP decode
    wire is_ei = (ir_high == 8'h08);    // EI: $08
    wire is_di = (ir_high == 8'h48);    // DI: $48
    wire is_setdp = (ir_high == 8'h40); // SETDP: $40 (XOR_MODE=1 only)

    // Derived
    wire z_match = z_flag ^ alu_sub;
    wire br_taken = branch & z_match;
    wire pc_load = jump | br_taken;
    wire pg_load = mux_sel & ~ac_wr & ~xor_mode; // exclude SETDP ($40 has XOR=1)

    // IRQ condition
    wire irq_pending = irq_ff & ie;

    // Memory read (fetch): A15 selects ROM or RAM
    wire [7:0] mem_read = pc[15] ? rom[pc[14:0]] : ram[pc[14:0]];

    // Data address: {data_page_reg[7:0], ir_low} — full 64KB
    wire [15:0] data_addr_full = {data_page_reg, ir_low};

    // IBUS during T2: data access uses data_page_reg for full 64KB
    wire [7:0] ibus = source_type ? (data_addr_full[15] ? rom[data_addr_full[14:0]] : ram[data_addr_full[14:0]]) : ir_low;

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

    // Latch IRQ on falling edge of irq_n
    reg irq_n_prev;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq_ff <= 1'b0;
            irq_n_prev <= 1'b1;
        end else begin
            irq_n_prev <= irq_n;
            if (irq_n_prev & ~irq_n)
                irq_ff <= 1'b1;
            if (state == T2 && irq_pending && !pc_load)
                irq_ff <= 1'b0;
        end
    end

    // Store uses data_page_reg for address
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= T0;
            pc <= 16'h8000;
            ac <= 8'h00;
            ir_high <= 8'h00;
            ir_low <= 8'h00;
            page_reg <= 8'h80;
            data_page_reg <= 8'h00;  // data page 0 on reset
            z_flag <= 1'b1;
            halt <= 1'b0;
            ie <= 1'b0;
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
                    // Store: RAM write only if address in RAM range (A15=0)
                    if (store && !data_addr_full[15])
                        ram[data_addr_full[14:0]] <= ac;
                    if (ac_wr) begin
                        ac <= ac_mux;
                        z_flag <= (ac_mux == 8'h00);
                    end
                    if (pg_load)
                        page_reg <= ibus;
                    if (is_setdp)
                        data_page_reg <= ir_low;
                    if (pc_load)
                        pc <= {page_reg, ir_low};

                    // EI/DI
                    if (is_ei) ie <= 1'b1;
                    if (is_di) ie <= 1'b0;

                    // IRQ
                    if (irq_pending && !pc_load) begin
                        ram[8'h0E] <= pc[7:0];
                        ram[8'h0F] <= pc[15:8];
                        page_reg <= 8'hFF;
                        pc <= 16'hFF00;
                        ie <= 1'b0;
                    end

                    if (is_halt)
                        halt <= 1'b1;
                    state <= T0;
                end
                default: state <= T0;
            endcase
        end
    end
endmodule