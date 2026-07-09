`timescale 1ns/1ps

module tb_74xx_smoke;
  integer failures = 0;

  task check;
    input condition;
    input [255:0] message;
    begin
      if (!condition) begin
        $display("FAIL: %0s", message);
        failures = failures + 1;
      end
    end
  endtask

  reg [3:0] gate_a4;
  reg [3:0] gate_b4;
  wire [3:0] nand_y;
  wire [3:0] or_y;
  wire [3:0] xor_y;
  wire [3:0] nor_y;
  wire [3:0] and2_y;

  ttl_74hc00 u00(.A(gate_a4), .B(gate_b4), .Y(nand_y));
  ttl_74hc02 u02(.A(gate_a4), .B(gate_b4), .Y(nor_y));
  ttl_74hc08 u08(.A(gate_a4), .B(gate_b4), .Y(and2_y));
  ttl_74hc32 u32(.A(gate_a4), .B(gate_b4), .Y(or_y));
  ttl_74hc86 u86(.A(gate_a4), .B(gate_b4), .Y(xor_y));

  reg [5:0] inv_a;
  wire [5:0] inv_y;
  wire [5:0] schmitt_y;
  ttl_74hc04 u04(.A(inv_a), .Y(inv_y));
  ttl_74hc14 u14(.A(inv_a), .Y(schmitt_y));

  reg [7:0] nand8_a;
  wire nand8_y;
  ttl_74hc30 u30(.A(nand8_a), .Y(nand8_y));

  reg [7:0] noror8_a;
  wire noror8_x;
  wire noror8_y;
  ttl_74hc4078 u4078(.A(noror8_a), .X(noror8_x), .Y(noror8_y));

  reg [1:0] and_a;
  reg [1:0] and_b;
  reg [1:0] and_c;
  reg [1:0] and_d;
  wire [1:0] and_y;
  ttl_74hc21 u21(.A(and_a), .B(and_b), .C(and_c), .D(and_d), .Y(and_y));

  reg mux_en_bar;
  reg mux_sel;
  reg [3:0] mux_a;
  reg [3:0] mux_b;
  wire [3:0] mux_y;
  ttl_74hc157 u157(.Enable_bar(mux_en_bar), .Select(mux_sel), .A(mux_a), .B(mux_b), .Y(mux_y));

  reg dec_g1;
  reg dec_g2a_bar;
  reg dec_g2b_bar;
  reg dec_a;
  reg dec_b;
  reg dec_c;
  wire [7:0] dec_y_bar;
  ttl_74hc138 u138(.A(dec_a), .B(dec_b), .C(dec_c), .G1(dec_g1), .G2A_bar(dec_g2a_bar), .G2B_bar(dec_g2b_bar), .Y_bar(dec_y_bar));

  reg [1:0] dec2_en_bar;
  reg [1:0] dec2_a;
  reg [1:0] dec2_b;
  wire [3:0] dec2_y1_bar;
  wire [3:0] dec2_y2_bar;
  ttl_74hc139 u139(.Enable_bar(dec2_en_bar), .A(dec2_a), .B(dec2_b), .Y1_bar(dec2_y1_bar), .Y2_bar(dec2_y2_bar));

  reg sel8_en_bar;
  reg [2:0] sel8_sel;
  reg [7:0] sel8_d;
  wire sel8_y;
  wire sel8_y_bar;
  ttl_74hc151 u151(.Enable_bar(sel8_en_bar), .Select(sel8_sel), .D(sel8_d), .Y(sel8_y), .Y_bar(sel8_y_bar));

  reg [1:0] mux4_en_bar;
  reg [1:0] mux4_sel;
  reg [3:0] mux4_c1;
  reg [3:0] mux4_c2;
  wire mux4_y1;
  wire mux4_y2;
  ttl_74hc153 u153(.Enable_bar(mux4_en_bar), .Select(mux4_sel), .C1(mux4_c1), .C2(mux4_c2), .Y1(mux4_y1), .Y2(mux4_y2));

  reg ctr_clear_bar;
  reg ctr_load_bar;
  reg ctr_ent;
  reg ctr_enp;
  reg [3:0] ctr_d;
  reg ctr_clk;
  wire ctr_rco;
  wire [3:0] ctr_q;
  ttl_74hc161 u161(
    .Clear_bar(ctr_clear_bar), .Load_bar(ctr_load_bar), .ENT(ctr_ent), .ENP(ctr_enp),
    .D(ctr_d), .Clk(ctr_clk), .RCO(ctr_rco), .Q(ctr_q)
  );

  reg sr_clear_bar;
  reg sr_clk;
  reg sr_a;
  reg sr_b;
  wire [7:0] sr_q;
  ttl_74hc164 u164(.Clear_bar(sr_clear_bar), .Clk(sr_clk), .A(sr_a), .B(sr_b), .Q(sr_q));

  reg pls_load_bar;
  reg pls_clk;
  reg pls_inhibit;
  reg pls_serial;
  reg [7:0] pls_d;
  wire pls_qh;
  wire pls_qh_bar;
  ttl_74hc165 u165(.ShiftLoad_bar(pls_load_bar), .Clk(pls_clk), .ClkInhibit(pls_inhibit), .Serial(pls_serial), .D(pls_d), .QH(pls_qh), .QH_bar(pls_qh_bar));

  reg pso_clear_bar;
  reg pso_load_bar;
  reg pso_clk;
  reg pso_inhibit;
  reg pso_serial;
  reg [7:0] pso_d;
  wire pso_qh;
  ttl_74hc166 u166(.Clear_bar(pso_clear_bar), .ShiftLoad_bar(pso_load_bar), .Clk(pso_clk), .ClkInhibit(pso_inhibit), .Serial(pso_serial), .D(pso_d), .QH(pso_qh));

  reg [3:0] add_a;
  reg [3:0] add_b;
  reg add_cin;
  wire [3:0] add_sum;
  wire add_cout;
  ttl_74hc283 u283(.A(add_a), .B(add_b), .C_in(add_cin), .Sum(add_sum), .C_out(add_cout));

  reg [1:0] ff_preset_bar;
  reg [1:0] ff_clear_bar;
  reg [1:0] ff_d;
  reg [1:0] ff_clk;
  wire [1:0] ff_q;
  wire [1:0] ff_q_bar;
  ttl_74hc74 u74(.Preset_bar(ff_preset_bar), .Clear_bar(ff_clear_bar), .D(ff_d), .Clk(ff_clk), .Q(ff_q), .Q_bar(ff_q_bar));

  reg [1:0] jk112_preset_bar;
  reg [1:0] jk112_clear_bar;
  reg [1:0] jk112_j;
  reg [1:0] jk112_k;
  reg [1:0] jk112_clk;
  wire [1:0] jk112_q;
  wire [1:0] jk112_q_bar;
  ttl_74hc112 u112(.Preset_bar(jk112_preset_bar), .Clear_bar(jk112_clear_bar), .J(jk112_j), .K(jk112_k), .Clk(jk112_clk), .Q(jk112_q), .Q_bar(jk112_q_bar));

  reg buf_oe1_bar;
  reg buf_oe2_bar;
  reg [7:0] buf_a;
  wire [7:0] buf_y;
  ttl_74hc541 u541(.OE1_bar(buf_oe1_bar), .OE2_bar(buf_oe2_bar), .A(buf_a), .Y(buf_y));

  wire [7:0] invbuf_y;
  wire [7:0] buf244_y;
  ttl_74hc240 u240(.OE1_bar(buf_oe1_bar), .OE2_bar(buf_oe2_bar), .A(buf_a), .Y(invbuf_y));
  ttl_74hc244 u244(.OE1_bar(buf_oe1_bar), .OE2_bar(buf_oe2_bar), .A(buf_a), .Y(buf244_y));

  reg reg_oe_bar;
  reg reg_clk;
  reg [7:0] reg_d;
  wire [7:0] reg_q;
  ttl_74hc574 u574(.OE_bar(reg_oe_bar), .Clk(reg_clk), .D(reg_d), .Q(reg_q));

  reg reg_clear_bar;
  wire [7:0] reg273_q;
  wire [7:0] reg374_q;
  ttl_74hc273 u273(.Clear_bar(reg_clear_bar), .Clk(reg_clk), .D(reg_d), .Q(reg273_q));
  ttl_74hc374 u374(.OE_bar(reg_oe_bar), .Clk(reg_clk), .D(reg_d), .Q(reg374_q));

  reg mux_tri_oe_bar;
  wire mux_tri_y;
  wire mux_tri_y_bar;
  ttl_74hc251 u251(.OE_bar(mux_tri_oe_bar), .Select(sel8_sel), .D(sel8_d), .Y(mux_tri_y), .Y_bar(mux_tri_y_bar));

  wire [3:0] mux257_y;
  ttl_74hc257 u257(.OE_bar(mux_tri_oe_bar), .Select(mux_sel), .A(mux_a), .B(mux_b), .Y(mux257_y));

  reg ser;
  reg srclk595;
  reg rclk595;
  reg srclr595_bar;
  reg oe595_bar;
  wire [7:0] q595;
  wire qh595_prime;
  ttl_74hc595 u595(.SER(ser), .SRCLK(srclk595), .RCLK(rclk595), .SRCLR_bar(srclr595_bar), .OE_bar(oe595_bar), .Q(q595), .QH_prime(qh595_prime));

  reg [7:0] cnt593_drv;
  reg cnt593_drive;
  wire [7:0] cnt593_bus;
  reg cnt593_cload;
  reg cnt593_cclr;
  reg cnt593_cck;
  reg cnt593_ccken;
  reg cnt593_ccken_bar;
  reg cnt593_rck;
  reg cnt593_rcken;
  reg cnt593_g;
  reg cnt593_g_bar;
  wire cnt593_rco;
  assign cnt593_bus = cnt593_drive ? cnt593_drv : 8'hzz;
  ttl_74hc593 u593(
    .A_Q(cnt593_bus), .CLOAD(cnt593_cload), .RCO(cnt593_rco), .CCLR(cnt593_cclr), .CCK(cnt593_cck),
    .CCKEN(cnt593_ccken), .CCKEN_bar(cnt593_ccken_bar), .RCK(cnt593_rck), .RCKEN(cnt593_rcken),
    .G(cnt593_g), .G_bar(cnt593_g_bar)
  );

  reg [3:0] key_rows;
  wire [3:0] key_cols;
  reg key_osc;
  reg key_mask;
  reg key_oe;
  wire [3:0] key_data;
  wire key_dav;
  ttl_74hc922 u922(.RowY(key_rows), .ColumnX(key_cols), .Oscillator(key_osc), .KeybounceMask(key_mask), .OutputEnable(key_oe), .DataOut(key_data), .DataAvailable(key_dav));

  reg cmp_en_bar;
  reg [7:0] cmp_a;
  reg [7:0] cmp_b;
  wire cmp_equal_bar;
  ttl_74hc688 u688(.Enable_bar(cmp_en_bar), .A(cmp_a), .B(cmp_b), .Equal_bar(cmp_equal_bar));

  reg xcv_oe_bar;
  reg xcv_dir;
  reg [7:0] xcv_a_drv;
  reg [7:0] xcv_b_drv;
  reg xcv_drive_a;
  reg xcv_drive_b;
  wire [7:0] xcv_a_bus;
  wire [7:0] xcv_b_bus;
  assign xcv_a_bus = xcv_drive_a ? xcv_a_drv : 8'hzz;
  assign xcv_b_bus = xcv_drive_b ? xcv_b_drv : 8'hzz;
  ttl_74hc245 u245(.OE_bar(xcv_oe_bar), .DIR(xcv_dir), .A(xcv_a_bus), .B(xcv_b_bus));

  initial begin
    gate_a4 = 4'b1100;
    gate_b4 = 4'b1010;
    #1;
    check(nand_y == 4'b0111, "74HC00 NAND");
    check(nor_y == 4'b0001, "74HC02 NOR");
    check(and2_y == 4'b1000, "74HC08 AND");
    check(or_y == 4'b1110, "74HC32 OR");
    check(xor_y == 4'b0110, "74HC86 XOR");

    inv_a = 6'b101010;
    #1;
    check(inv_y == 6'b010101, "74HC04 inverter");
    check(schmitt_y == 6'b010101, "74HC14 Schmitt inverter");

    nand8_a = 8'hff;
    #1;
    check(nand8_y == 1'b0, "74HC30 all high");
    nand8_a = 8'h7f;
    #1;
    check(nand8_y == 1'b1, "74HC30 one low");

    noror8_a = 8'h00;
    #1;
    check(noror8_x == 1'b1 && noror8_y == 1'b0, "74HC4078 all low");
    noror8_a = 8'h10;
    #1;
    check(noror8_x == 1'b0 && noror8_y == 1'b1, "74HC4078 one high");

    and_a = 2'b11;
    and_b = 2'b10;
    and_c = 2'b11;
    and_d = 2'b11;
    #1;
    check(and_y == 2'b10, "74HC21 4-input AND");

    mux_en_bar = 1'b0;
    mux_sel = 1'b0;
    mux_a = 4'ha;
    mux_b = 4'h5;
    #1;
    check(mux_y == 4'ha, "74HC157 select A");
    mux_sel = 1'b1;
    #1;
    check(mux_y == 4'h5, "74HC157 select B");
    mux_en_bar = 1'b1;
    #1;
    check(mux_y == 4'h0, "74HC157 disabled output low");

    dec_g1 = 1'b1;
    dec_g2a_bar = 1'b0;
    dec_g2b_bar = 1'b0;
    dec_a = 1'b1;
    dec_b = 1'b0;
    dec_c = 1'b1;
    #1;
    check(dec_y_bar == 8'b11011111, "74HC138 decode 5");

    dec2_en_bar = 2'b00;
    dec2_a = 2'b10;
    dec2_b = 2'b01;
    #1;
    check(dec2_y1_bar == 4'b1011 && dec2_y2_bar == 4'b1101, "74HC139 dual decode");

    sel8_en_bar = 1'b0;
    sel8_sel = 3'd6;
    sel8_d = 8'b0100_0000;
    #1;
    check(sel8_y == 1'b1 && sel8_y_bar == 1'b0, "74HC151 select");

    mux4_en_bar = 2'b00;
    mux4_sel = 2'd2;
    mux4_c1 = 4'b0100;
    mux4_c2 = 4'b1011;
    #1;
    check(mux4_y1 == 1'b1 && mux4_y2 == 1'b0, "74HC153 select");

    ctr_clk = 1'b0;
    ctr_clear_bar = 1'b0;
    ctr_load_bar = 1'b1;
    ctr_ent = 1'b1;
    ctr_enp = 1'b1;
    ctr_d = 4'h9;
    #1;
    check(ctr_q == 4'h0, "74HC161 asynchronous clear");
    ctr_clear_bar = 1'b1;
    ctr_load_bar = 1'b0;
    #1 ctr_clk = 1'b1; #1 ctr_clk = 1'b0;
    check(ctr_q == 4'h9, "74HC161 parallel load");
    ctr_load_bar = 1'b1;
    #1 ctr_clk = 1'b1; #1 ctr_clk = 1'b0;
    check(ctr_q == 4'ha, "74HC161 count");

    sr_clk = 1'b0;
    sr_clear_bar = 1'b0;
    sr_a = 1'b1;
    sr_b = 1'b1;
    #1;
    check(sr_q == 8'h00, "74HC164 asynchronous clear");
    sr_clear_bar = 1'b1;
    #1 sr_clk = 1'b1; #1 sr_clk = 1'b0;
    check(sr_q == 8'h01, "74HC164 shift in one");

    pls_clk = 1'b0;
    pls_inhibit = 1'b0;
    pls_serial = 1'b0;
    pls_d = 8'h80;
    pls_load_bar = 1'b0;
    #1 pls_clk = 1'b1; #1 pls_clk = 1'b0;
    check(pls_qh == 1'b1 && pls_qh_bar == 1'b0, "74HC165 parallel load");
    pls_load_bar = 1'b1;
    #1 pls_clk = 1'b1; #1 pls_clk = 1'b0;
    check(pls_qh == 1'b0, "74HC165 shift");

    pso_clk = 1'b0;
    pso_clear_bar = 1'b0;
    pso_load_bar = 1'b1;
    pso_inhibit = 1'b0;
    pso_serial = 1'b0;
    pso_d = 8'h80;
    #1;
    check(pso_qh == 1'b0, "74HC166 clear");
    pso_clear_bar = 1'b1;
    pso_load_bar = 1'b0;
    #1 pso_clk = 1'b1; #1 pso_clk = 1'b0;
    check(pso_qh == 1'b1, "74HC166 parallel load");

    add_a = 4'hf;
    add_b = 4'h1;
    add_cin = 1'b1;
    #1;
    check(add_sum == 4'h1 && add_cout == 1'b1, "74HC283 add with carry");

    ff_clk = 2'b00;
    ff_preset_bar = 2'b11;
    ff_clear_bar = 2'b00;
    ff_d = 2'b10;
    #1;
    check(ff_q == 2'b00 && ff_q_bar == 2'b11, "74HC74 asynchronous clear");
    ff_clear_bar = 2'b11;
    #1 ff_clk = 2'b11; #1 ff_clk = 2'b00;
    check(ff_q == 2'b10 && ff_q_bar == 2'b01, "74HC74 clocked D");
    ff_preset_bar = 2'b10;
    #1;
    check(ff_q[0] == 1'b1, "74HC74 asynchronous preset");

    jk112_clk = 2'b00;
    jk112_preset_bar = 2'b11;
    jk112_clear_bar = 2'b00;
    jk112_j = 2'b01;
    jk112_k = 2'b00;
    #1;
    check(jk112_q == 2'b00 && jk112_q_bar == 2'b11, "74HC112 asynchronous clear");
    jk112_clear_bar = 2'b11;
    #1 jk112_clk[0] = 1'b1; #1;
    check(jk112_q[0] == 1'b0, "74HC112 ignores rising clock edge");
    jk112_clk[0] = 1'b0; #1;
    check(jk112_q[0] == 1'b1, "74HC112 negative-edge clock");
    jk112_preset_bar[1] = 1'b0;
    #1;
    check(jk112_q[1] == 1'b1 && jk112_q_bar[1] == 1'b0, "74HC112 asynchronous preset");

    buf_oe1_bar = 1'b0;
    buf_oe2_bar = 1'b0;
    buf_a = 8'ha5;
    #1;
    check(buf_y == 8'ha5, "74HC541 enabled buffer");
    check(invbuf_y == 8'h5a, "74HC240 enabled inverting buffer");
    check(buf244_y == 8'ha5, "74HC244 enabled buffer");
    buf_oe1_bar = 1'b1;
    #1;
    check(buf_y === 8'hzz, "74HC541 disabled high-Z");

    reg_clk = 1'b0;
    reg_oe_bar = 1'b0;
    reg_clear_bar = 1'b0;
    reg_d = 8'h3c;
    #1;
    check(reg273_q == 8'h00, "74HC273 clear");
    reg_clear_bar = 1'b1;
    #1 reg_clk = 1'b1; #1 reg_clk = 1'b0;
    check(reg_q == 8'h3c, "74HC574 clocked D");
    check(reg273_q == 8'h3c, "74HC273 clocked D");
    check(reg374_q == 8'h3c, "74HC374 clocked D");
    reg_oe_bar = 1'b1;
    #1;
    check(reg_q === 8'hzz, "74HC574 disabled high-Z");
    check(reg374_q === 8'hzz, "74HC374 disabled high-Z");

    mux_tri_oe_bar = 1'b0;
    #1;
    check(mux_tri_y == 1'b1 && mux_tri_y_bar == 1'b0, "74HC251 select");
    mux_sel = 1'b1;
    mux_a = 4'h1;
    mux_b = 4'hc;
    #1;
    check(mux257_y == 4'hc, "74HC257 select B");
    mux_tri_oe_bar = 1'b1;
    #1;
    check(mux_tri_y === 1'bz && mux257_y === 4'hz, "74HC251/257 disabled high-Z");

    ser = 1'b1;
    srclk595 = 1'b0;
    rclk595 = 1'b0;
    srclr595_bar = 1'b0;
    oe595_bar = 1'b0;
    #1;
    srclr595_bar = 1'b1;
    #1 srclk595 = 1'b1; #1 srclk595 = 1'b0;
    #1 rclk595 = 1'b1; #1 rclk595 = 1'b0;
    check(q595 == 8'h01, "74HC595 shift and latch");

    cnt593_cck = 1'b0;
    cnt593_rck = 1'b0;
    cnt593_cclr = 1'b0;
    cnt593_cload = 1'b1;
    cnt593_ccken = 1'b1;
    cnt593_ccken_bar = 1'b1;
    cnt593_rcken = 1'b1;
    cnt593_g = 1'b1;
    cnt593_g_bar = 1'b0;
    cnt593_drive = 1'b0;
    cnt593_drv = 8'h00;
    #1;
    check(cnt593_bus == 8'h00 && cnt593_rco == 1'b1, "74HC593 clear and RCO");
    cnt593_cclr = 1'b1;
    #1 cnt593_cck = 1'b1; #1 cnt593_cck = 1'b0;
    check(cnt593_bus == 8'h01, "74HC593 count");
    cnt593_g = 1'b0;
    cnt593_g_bar = 1'b1;
    #1;
    check(cnt593_bus === 8'hzz, "74HC593 disabled high-Z");

    key_osc = 1'b0;
    key_mask = 1'b1;
    key_oe = 1'b0;
    key_rows = 4'b1110;
    #1;
    check(key_dav == 1'b1 && key_data == 4'h0, "74HC922 key encode row 1 column 1");
    key_oe = 1'b1;
    #1;
    check(key_data === 4'hz, "74HC922 disabled high-Z");

    cmp_en_bar = 1'b0;
    cmp_a = 8'hc3;
    cmp_b = 8'hc3;
    #1;
    check(cmp_equal_bar == 1'b0, "74HC688 equal active-low");
    cmp_b = 8'hc2;
    #1;
    check(cmp_equal_bar == 1'b1, "74HC688 not equal");

    xcv_oe_bar = 1'b0;
    xcv_dir = 1'b1;
    xcv_a_drv = 8'h5a;
    xcv_b_drv = 8'h00;
    xcv_drive_a = 1'b1;
    xcv_drive_b = 1'b0;
    #1;
    check(xcv_b_bus == 8'h5a, "74HC245 A to B");
    xcv_dir = 1'b0;
    xcv_a_drv = 8'h00;
    xcv_b_drv = 8'ha6;
    xcv_drive_a = 1'b0;
    xcv_drive_b = 1'b1;
    #1;
    check(xcv_a_bus == 8'ha6, "74HC245 B to A");
    xcv_oe_bar = 1'b1;
    xcv_drive_a = 1'b0;
    xcv_drive_b = 1'b0;
    #1;
    check(xcv_a_bus === 8'hzz && xcv_b_bus === 8'hzz, "74HC245 disabled high-Z");

    if (failures == 0) begin
      $display("74xx SMOKE TEST PASSED");
      $finish;
    end

    $display("74xx SMOKE TEST FAILED: %0d failures", failures);
    $fatal(1);
  end
endmodule
