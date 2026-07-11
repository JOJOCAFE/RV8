#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPONENTS="${COMPONENTS_ROOT:-$ROOT/third_party/Components}"
OUTDIR="${RV8GR_BUILD_DIR:-/tmp/rv8gr-verilog}"
VERILOG="$COMPONENTS/Verilog"
if [[ -d "$COMPONENTS/verilog" ]]; then
  VERILOG="$COMPONENTS/verilog"
fi
MEMORY="$VERILOG/Memory"
if [[ -d "$VERILOG/memory" ]]; then
  MEMORY="$VERILOG/memory"
fi

mkdir -p "$OUTDIR"

iverilog -g2012 -Wall \
  -o "$OUTDIR/rv8gr_chip_full.vvp" \
  "$VERILOG/74xx/74hc00.v" \
  "$VERILOG/74xx/74hc04.v" \
  "$VERILOG/74xx/74hc21.v" \
  "$VERILOG/74xx/74hc32.v" \
  "$VERILOG/74xx/74hc74.v" \
  "$VERILOG/74xx/74hc86.v" \
  "$VERILOG/74xx/74hc157.v" \
  "$VERILOG/74xx/74hc161.v" \
  "$VERILOG/74xx/74hc164.v" \
  "$VERILOG/74xx/74hc245.v" \
  "$VERILOG/74xx/74hc283.v" \
  "$VERILOG/74xx/74hc541.v" \
  "$VERILOG/74xx/74hc574.v" \
  "$VERILOG/74xx/74hc688.v" \
  "$MEMORY/62256.v" \
  "$MEMORY/at28c256.v" \
  "$ROOT/rtl/rv8gr_chip_level.v" \
  "$ROOT/tb/tb_rv8gr_chip_full.v"

cd "$OUTDIR"
vvp "$OUTDIR/rv8gr_chip_full.vvp" "+dumpfile=$OUTDIR/rv8gr_chip_full.vcd"
