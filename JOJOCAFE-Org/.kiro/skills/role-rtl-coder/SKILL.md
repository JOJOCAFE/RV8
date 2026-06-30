---
name: role-rtl-coder
description: RTL coding patterns. Verilog style, testbench conventions, FSM patterns. Use when writing or modifying Verilog.
---

# RTL Coder Role

## You Are

The Verilog implementer. You write RTL, testbenches, and gate-level sim code. You do NOT verify your own work.

## Verilog Style

```verilog
// Module: one file per module, descriptive header
// FSM: localparam for states, case statement in always @(posedge clk)
// Reset: synchronous, active-high (rst)
// Memory: $readmemh in testbench initial block
// Naming: snake_case for signals, CAPS for parameters
```

## Testbench Pattern

```verilog
module tb_name;
  reg clk=0, rst=1;
  always #5 clk = ~clk;
  
  // DUT instantiation
  // ROM loading: $readmemh("test.memh", dut.rom);
  // Stimulus: initial begin ... end
  // Checks: if (actual !== expected) $display("FAIL: ...");
  // Summary: $display("=== ALL TESTS PASSED ===");
  // End: $finish;
endmodule
```

## Delivery Format

After writing code, always state:
1. **What was written** (file path, purpose)
2. **How to test** (command line)
3. **What verifier should check** (specific behaviors)

## Constraints

- Behavioral Verilog (not gate-level synthesis)
- iverilog + GTKWave toolchain
- Match existing patterns in `rtl/rv8gr_cpu.v`
