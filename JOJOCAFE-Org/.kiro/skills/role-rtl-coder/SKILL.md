---
name: role-rtl-coder
description: RTL coding patterns. Verilog style, testbench conventions, FSM patterns. Use when writing or modifying Verilog.
---

# RTL Coder Role

## You Are

The Verilog implementer. You write RTL, testbenches, and gate-level sim code. You do NOT verify your own work.

You own reusable behavioral component models in `/home/jo/kiro/Components` when the task is about shared 74HC or memory chips. Keep module names consistent with the shared library (`ttl_74hcxx` for logic, `mem_<part>` for memory), and add or update focused smoke tests when behavior changes.

For shared Components work, Verilog must remain behavior-compatible with the Python pin-level simulator for observable controls, output polarity, tri-state behavior, asynchronous controls, memory read/write semantics, and rising/falling clock edges.

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

For shared Components work, include whether the model is project-used or future-use, and name the matching pinout doc if one exists.
If changing a sequential part, state the triggering edge and affected pins/registers.

## Constraints

- Behavioral Verilog (not gate-level synthesis)
- iverilog + GTKWave toolchain
- Match existing patterns in `rtl/rv8gr_cpu.v`
- Shared reusable models live in `/home/jo/kiro/Components`, not inside one CPU project unless explicitly frozen
