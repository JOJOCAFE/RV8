#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPONENTS="${COMPONENTS_ROOT:-$ROOT/third_party/Components}"

iverilog -g2012 -Wall \
  -o "$ROOT/tb/rv8gr_chip_level.vvp" \
  "$COMPONENTS/Verilog/74xx/74hc00.v" \
  "$COMPONENTS/Verilog/74xx/74hc04.v" \
  "$COMPONENTS/Verilog/74xx/74hc21.v" \
  "$COMPONENTS/Verilog/74xx/74hc32.v" \
  "$COMPONENTS/Verilog/74xx/74hc74.v" \
  "$COMPONENTS/Verilog/74xx/74hc86.v" \
  "$COMPONENTS/Verilog/74xx/74hc157.v" \
  "$COMPONENTS/Verilog/74xx/74hc161.v" \
  "$COMPONENTS/Verilog/74xx/74hc164.v" \
  "$COMPONENTS/Verilog/74xx/74hc245.v" \
  "$COMPONENTS/Verilog/74xx/74hc283.v" \
  "$COMPONENTS/Verilog/74xx/74hc541.v" \
  "$COMPONENTS/Verilog/74xx/74hc574.v" \
  "$COMPONENTS/Verilog/74xx/74hc688.v" \
  "$COMPONENTS/Verilog/Memory/62256.v" \
  "$COMPONENTS/Verilog/Memory/at28c256.v" \
  "$ROOT/rtl/rv8gr_chip_level.v" \
  "$ROOT/tb/tb_rv8gr_chip_level.v"

cd "$ROOT"
vvp tb/rv8gr_chip_level.vvp
