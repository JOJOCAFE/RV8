#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="${RV8GR_BUILD_DIR:-/tmp/rv8gr-verilog}"

mkdir -p "$OUTDIR"
ln -sfn "$ROOT/programs" "$OUTDIR/programs"

run_behavioral_tb() {
  local tb="$1"
  local name
  name="$(basename "$tb" .v)"
  echo "=== $name ==="
  iverilog -g2012 -Wall \
    -o "$OUTDIR/${name}.vvp" \
    "$ROOT/rtl/rv8gr_cpu.v" \
    "$ROOT/$tb"
  (cd "$ROOT" && vvp "$OUTDIR/${name}.vvp" "+dumpfile=$OUTDIR/${name}.vcd")
}

run_behavioral_tb tb/tb_rv8gr_asm.v
run_behavioral_tb tb/tb_rv8gr_full.v
run_behavioral_tb tb/tb_rv8gr_irq.v
run_behavioral_tb tb/tb_rv8gr_opcode_sweep.v
run_behavioral_tb tb/tb_rv8gr_setdp.v
run_behavioral_tb tb/tb_rv8gr_tasks.v

echo "=== tb_rv8gr_chip_level ==="
RV8GR_BUILD_DIR="$OUTDIR" "$ROOT/tools/run_chip_level_verilog.sh"

echo "=== tb_rv8gr_chip_full ==="
RV8GR_BUILD_DIR="$OUTDIR" "$ROOT/tools/run_chip_level_full_verilog.sh"

echo "=== tb_rv8gr_dual_compare ==="
RV8GR_BUILD_DIR="$OUTDIR" "$ROOT/tools/run_dual_verilog_compare.sh"
