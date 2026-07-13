#!/usr/bin/env bash
set -euo pipefail

# Bench-only ROM protection, store-direction and OE-order mutation suite.
# Production RTL is compiled unchanged.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPONENTS="${COMPONENTS_ROOT:-$ROOT/third_party/Components}"
OUTDIR="${RV8GR_BUILD_DIR:-/tmp/rv8gr-verilog}"
VERILOG="$COMPONENTS/Verilog"
if [[ -d "$COMPONENTS/verilog" ]]; then VERILOG="$COMPONENTS/verilog"; fi
MEMORY="$VERILOG/Memory"
if [[ -d "$VERILOG/memory" ]]; then MEMORY="$VERILOG/memory"; fi

mkdir -p "$OUTDIR"
VVP="$OUTDIR/rv8gr_memory_bus_mutation.vvp"
BASELINE_LOG="$OUTDIR/rv8gr_memory_bus_mutation_baseline.log"

iverilog -g2012 -Wall -s tb_rv8gr_memory_bus_mutation -o "$VVP" \
  "$VERILOG/74xx/74hc00.v" "$VERILOG/74xx/74hc04.v" \
  "$VERILOG/74xx/74hc21.v" "$VERILOG/74xx/74hc32.v" \
  "$VERILOG/74xx/74hc74.v" "$VERILOG/74xx/74hc86.v" \
  "$VERILOG/74xx/74hc157.v" "$VERILOG/74xx/74hc161.v" \
  "$VERILOG/74xx/74hc164.v" "$VERILOG/74xx/74hc245.v" \
  "$VERILOG/74xx/74hc283.v" "$VERILOG/74xx/74hc541.v" \
  "$VERILOG/74xx/74hc574.v" "$VERILOG/74xx/74hc688.v" \
  "$MEMORY/62256.v" "$MEMORY/at28c256.v" \
  "$ROOT/rtl/rv8gr_chip_level.v" \
  "$ROOT/tb/tb_rv8gr_memory_bus_mutation.v"

vvp "$VVP" >"$BASELINE_LOG" 2>&1
for mutation in rom_we store_direction oe_order; do
  log="$OUTDIR/rv8gr_${mutation}_mutation.log"
  if vvp "$VVP" "+mutate_${mutation}" >"$log" 2>&1; then
    echo "ERROR: ${mutation} mutation unexpectedly passed; see $log" >&2
    exit 1
  fi
  case "$mutation" in
    rom_we) expected="ROM /WE MUTATION KILLED" ;;
    store_direction) expected="STORE DIRECTION MUTATION KILLED" ;;
    oe_order) expected="OUTPUT-ENABLE ORDER MUTATION KILLED" ;;
  esac
  if ! grep -q "$expected" "$log"; then
    echo "ERROR: ${mutation} exited without the expected kill marker; see $log" >&2
    exit 1
  fi
done

cat "$BASELINE_LOG"
echo "RV8GR memory/bus mutation PASS: all three deliberate faults were killed."
echo "Artifacts: $VVP $BASELINE_LOG $OUTDIR/rv8gr_{rom_we,store_direction,oe_order}_mutation.log"
