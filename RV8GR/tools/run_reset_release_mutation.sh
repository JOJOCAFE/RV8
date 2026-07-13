#!/usr/bin/env bash
set -euo pipefail

# Compile one bench-only reset-release protocol test.  Baseline must pass;
# the deliberate fault must exit nonzero.  All generated artifacts stay in
# RV8GR_BUILD_DIR (default /tmp/rv8gr-verilog).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPONENTS="${COMPONENTS_ROOT:-$ROOT/third_party/Components}"
OUTDIR="${RV8GR_BUILD_DIR:-/tmp/rv8gr-verilog}"
VERILOG="$COMPONENTS/Verilog"
if [[ -d "$COMPONENTS/verilog" ]]; then VERILOG="$COMPONENTS/verilog"; fi
MEMORY="$VERILOG/Memory"
if [[ -d "$VERILOG/memory" ]]; then MEMORY="$VERILOG/memory"; fi

mkdir -p "$OUTDIR"
VVP="$OUTDIR/rv8gr_reset_release_mutation.vvp"
BASELINE_LOG="$OUTDIR/rv8gr_reset_release_baseline.log"
MUTATION_LOG="$OUTDIR/rv8gr_reset_release_mutation.log"

iverilog -g2012 -Wall -s tb_rv8gr_reset_release_mutation -o "$VVP" \
  "$VERILOG/74xx/74hc00.v" "$VERILOG/74xx/74hc04.v" \
  "$VERILOG/74xx/74hc21.v" "$VERILOG/74xx/74hc32.v" \
  "$VERILOG/74xx/74hc74.v" "$VERILOG/74xx/74hc86.v" \
  "$VERILOG/74xx/74hc157.v" "$VERILOG/74xx/74hc161.v" \
  "$VERILOG/74xx/74hc164.v" "$VERILOG/74xx/74hc245.v" \
  "$VERILOG/74xx/74hc283.v" "$VERILOG/74xx/74hc541.v" \
  "$VERILOG/74xx/74hc574.v" "$VERILOG/74xx/74hc688.v" \
  "$MEMORY/62256.v" "$MEMORY/at28c256.v" \
  "$ROOT/rtl/rv8gr_chip_level.v" \
  "$ROOT/tb/tb_rv8gr_reset_release_mutation.v"

vvp "$VVP" >"$BASELINE_LOG" 2>&1
if vvp "$VVP" +mutate_bad_reset_release >"$MUTATION_LOG" 2>&1; then
  echo "ERROR: reset-release mutation unexpectedly passed; see $MUTATION_LOG" >&2
  exit 1
fi
if ! grep -q "RESET RELEASE MUTATION KILLED" "$MUTATION_LOG"; then
  echo "ERROR: mutation exited nonzero without the expected protocol kill; see $MUTATION_LOG" >&2
  exit 1
fi

cat "$BASELINE_LOG"
echo "RV8GR reset-release mutation PASS: baseline passed; deliberate bad release was killed."
echo "Artifacts: $VVP $BASELINE_LOG $MUTATION_LOG"
