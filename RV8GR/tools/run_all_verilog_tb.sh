#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run_behavioral_tb() {
  local tb="$1"
  local name
  name="$(basename "$tb" .v)"
  echo "=== $name ==="
  iverilog -g2012 -Wall \
    -o "$ROOT/tb/${name}.vvp" \
    "$ROOT/rtl/rv8gr_cpu.v" \
    "$ROOT/$tb"
  (cd "$ROOT" && vvp "tb/${name}.vvp")
}

run_behavioral_tb tb/tb_rv8gr_asm.v
run_behavioral_tb tb/tb_rv8gr_full.v
run_behavioral_tb tb/tb_rv8gr_irq.v
run_behavioral_tb tb/tb_rv8gr_opcode_sweep.v
run_behavioral_tb tb/tb_rv8gr_setdp.v
run_behavioral_tb tb/tb_rv8gr_tasks.v

echo "=== tb_rv8gr_chip_level ==="
"$ROOT/tools/run_chip_level_verilog.sh"

echo "=== tb_rv8gr_chip_full ==="
"$ROOT/tools/run_chip_level_full_verilog.sh"
