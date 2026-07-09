"""Python-vs-Verilog equivalence smoke tests for representative chips."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from chiplib import Z, create_chip


ROOT = Path(__file__).resolve().parents[2]


def set_byte(chip, pins, value):
    for i, pin in enumerate(pins):
        chip.set_input(pin, (value >> i) & 1)


def get_byte(chip, pins):
    return sum((1 if chip.read(pin) == 1 else 0) << i for i, pin in enumerate(pins))


def eval_chip(chip):
    chip.update()
    chip.commit()


def run_verilog(module_file: str, testbench: str) -> str | None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        tb = Path(tmp) / "tb_equivalence.v"
        out = Path(tmp) / "tb_equivalence.vvp"
        tb.write_text(testbench, encoding="utf-8")
        compiled = subprocess.run(
            [iverilog, "-g2012", "-Wall", "-o", str(out), str(ROOT / module_file), str(tb)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert compiled.returncode == 0, compiled.stderr
        simulated = subprocess.run([vvp, str(out)], text=True, capture_output=True, check=False)
        assert simulated.returncode == 0, simulated.stderr
        return simulated.stdout


def result_int(output: str, key: str) -> int:
    match = re.search(rf"RESULT {key} ([0-9a-fA-FxzXZ]+)", output)
    assert match is not None, output
    text = match.group(1).lower()
    assert "x" not in text
    assert "z" not in text
    return int(text, 16)


def test_74hc00_python_matches_verilog_vectors():
    vectors = [(0, 0), (0, 1), (1, 0), (1, 1)]
    expected_bits = []
    for a, b in vectors:
        chip = create_chip("74HC00", "U")
        chip.set_input(1, a)
        chip.set_input(2, b)
        eval_chip(chip)
        expected_bits.append(chip.read(3))
    expected = sum(bit << i for i, bit in enumerate(expected_bits))

    output = run_verilog(
        "Verilog/74xx/74hc00.v",
        """
`timescale 1ns/1ps
module tb;
  reg [3:0] a = 4'b1010;
  reg [3:0] b = 4'b1100;
  wire [3:0] y;
  ttl_74hc00 dut(.A(a), .B(b), .Y(y));
  initial begin #1; $display("RESULT NAND %h", y); $finish; end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "NAND") == expected


def test_74hc161_python_matches_verilog_count_sequence():
    chip = create_chip("74HC161", "U")
    for pin, value in [(1, 0), (9, 1), (7, 1), (10, 1)]:
        chip.set_input(pin, value)
    eval_chip(chip)
    chip.set_input(1, 1)
    for _ in range(3):
        chip.clock_edge()
        chip.commit()
    expected_q = get_byte(chip, [14, 13, 12, 11])
    expected_rco = chip.read(15)

    output = run_verilog(
        "Verilog/74xx/74hc161.v",
        """
`timescale 1ns/1ps
module tb;
  reg clear_bar = 0;
  reg load_bar = 1;
  reg ent = 1;
  reg enp = 1;
  reg [3:0] d = 4'h0;
  reg clk = 0;
  wire rco;
  wire [3:0] q;
  ttl_74hc161 dut(.Clear_bar(clear_bar), .Load_bar(load_bar), .ENT(ent), .ENP(enp), .D(d), .Clk(clk), .RCO(rco), .Q(q));
  initial begin
    #1; clear_bar = 1; #1; clear_bar = 0; #1; clear_bar = 1;
    repeat (3) begin #1 clk = 1; #1 clk = 0; end
    #1; $display("RESULT COUNT %h", {rco, q}); $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "COUNT") == ((expected_rco << 4) | expected_q)


def test_74hc245_python_matches_verilog_a_to_b_and_high_z():
    chip = create_chip("74HC245", "U")
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0x3C)
    chip.set_input(1, 1)
    chip.set_input(19, 0)
    eval_chip(chip)
    expected_b = get_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11])
    chip.set_input(19, 1)
    eval_chip(chip)
    assert chip.read(18) == Z

    output = run_verilog(
        "Verilog/74xx/74hc245.v",
        """
`timescale 1ns/1ps
module tb;
  reg oe_bar = 0;
  reg dir = 1;
  reg [7:0] a_drv = 8'h3c;
  reg drive_a = 1;
  wire [7:0] a;
  wire [7:0] b;
  assign a = drive_a ? a_drv : 8'hzz;
  ttl_74hc245 dut(.OE_bar(oe_bar), .DIR(dir), .A(a), .B(b));
  initial begin
    #1; $display("RESULT XCV %h", b);
    oe_bar = 1; drive_a = 0;
    #1; if (b !== 8'hzz) begin $display("FAIL high-z"); $finish(1); end
    $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "XCV") == expected_b

    chip = create_chip("74HC245", "U")
    set_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11], 0x96)
    chip.set_input(1, 0)
    chip.set_input(19, 0)
    eval_chip(chip)
    expected_a = get_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9])
    chip.set_input(19, 1)
    eval_chip(chip)
    assert chip.read(2) == Z
    assert chip.read(18) == Z

    output = run_verilog(
        "Verilog/74xx/74hc245.v",
        """
`timescale 1ns/1ps
module tb;
  reg oe_bar = 0;
  reg dir = 0;
  reg [7:0] b_drv = 8'h96;
  reg drive_b = 1;
  wire [7:0] a;
  wire [7:0] b;
  assign b = drive_b ? b_drv : 8'hzz;
  ttl_74hc245 dut(.OE_bar(oe_bar), .DIR(dir), .A(a), .B(b));
  initial begin
    #1; $display("RESULT XCVB %h", a);
    oe_bar = 1; drive_b = 0;
    #1; if (a !== 8'hzz || b !== 8'hzz) begin $display("FAIL high-z"); $finish(1); end
    $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "XCVB") == expected_a


def test_74hc541_python_matches_verilog_enable_and_high_z():
    chip = create_chip("74HC541", "U")
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0x96)
    chip.set_input(1, 0)
    chip.set_input(19, 0)
    eval_chip(chip)
    expected_y = get_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11])
    chip.set_input(1, 1)
    eval_chip(chip)
    assert chip.read(18) == Z

    output = run_verilog(
        "Verilog/74xx/74hc541.v",
        """
`timescale 1ns/1ps
module tb;
  reg oe1_bar = 0;
  reg oe2_bar = 0;
  reg [7:0] a = 8'h96;
  wire [7:0] y;
  ttl_74hc541 dut(.OE1_bar(oe1_bar), .OE2_bar(oe2_bar), .A(a), .Y(y));
  initial begin
    #1; $display("RESULT BUF %h", y);
    oe1_bar = 1;
    #1; if (y !== 8'hzz) begin $display("FAIL high-z"); $finish(1); end
    $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "BUF") == expected_y


def test_74hc574_python_matches_verilog_latch_hold_and_high_z():
    chip = create_chip("74HC574", "U")
    chip.set_input(1, 0)
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0xA5)
    chip.clock_edge()
    chip.commit()
    expected_q = get_byte(chip, [19, 18, 17, 16, 15, 14, 13, 12])
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0x3C)
    eval_chip(chip)
    assert get_byte(chip, [19, 18, 17, 16, 15, 14, 13, 12]) == expected_q
    chip.set_input(1, 1)
    eval_chip(chip)
    assert chip.read(19) == Z

    output = run_verilog(
        "Verilog/74xx/74hc574.v",
        """
`timescale 1ns/1ps
module tb;
  reg oe_bar = 0;
  reg clk = 0;
  reg [7:0] d = 8'ha5;
  wire [7:0] q;
  ttl_74hc574 dut(.OE_bar(oe_bar), .Clk(clk), .D(d), .Q(q));
  initial begin
    #1; clk = 1; #1; clk = 0;
    #1; $display("RESULT REG %h", q);
    d = 8'h3c; #1; if (q !== 8'ha5) begin $display("FAIL hold"); $finish(1); end
    oe_bar = 1; #1; if (q !== 8'hzz) begin $display("FAIL high-z"); $finish(1); end
    $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "REG") == expected_q


def test_62256_python_matches_verilog_write_read_and_high_z():
    chip = create_chip("62256", "U")
    for pin in [10, 9, 8, 7, 6, 5, 4, 3, 25, 24, 21, 23, 2, 26, 1]:
        chip.set_input(pin, 0)
    set_byte(chip, [11, 12, 13, 15, 16, 17, 18, 19], 0x5A)
    chip.set_input(20, 0)
    chip.set_input(22, 1)
    chip.set_input(27, 0)
    eval_chip(chip)
    chip.set_input(27, 1)
    chip.set_input(22, 0)
    eval_chip(chip)
    expected_dq = get_byte(chip, [11, 12, 13, 15, 16, 17, 18, 19])
    chip.set_input(20, 1)
    eval_chip(chip)
    assert chip.read(11) == Z

    output = run_verilog(
        "Verilog/Memory/62256.v",
        """
`timescale 1ns/1ps
module tb;
  reg [14:0] a = 15'h0000;
  reg [7:0] dq_drv = 8'h5a;
  reg drive_dq = 1;
  wire [7:0] dq;
  reg ce_bar = 0;
  reg oe_bar = 1;
  reg we_bar = 0;
  assign dq = drive_dq ? dq_drv : 8'hzz;
  mem_62256 dut(.A(a), .DQ(dq), .CE_bar(ce_bar), .OE_bar(oe_bar), .WE_bar(we_bar));
  initial begin
    #1; we_bar = 1; drive_dq = 0; oe_bar = 0;
    #1; $display("RESULT SRAM %h", dq);
    ce_bar = 1; #1; if (dq !== 8'hzz) begin $display("FAIL high-z"); $finish(1); end
    $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "SRAM") == expected_dq


def run_all():
    test_74hc00_python_matches_verilog_vectors()
    test_74hc161_python_matches_verilog_count_sequence()
    test_74hc245_python_matches_verilog_a_to_b_and_high_z()
    test_74hc541_python_matches_verilog_enable_and_high_z()
    test_74hc574_python_matches_verilog_latch_hold_and_high_z()
    test_62256_python_matches_verilog_write_read_and_high_z()


if __name__ == "__main__":
    run_all()
    print("Components equivalence tests passed")
