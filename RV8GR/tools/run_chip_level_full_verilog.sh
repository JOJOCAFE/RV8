#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPONENTS="/home/jo/kiro/Components"

iverilog -g2012 -Wall \
  -o "$ROOT/tb/rv8gr_chip_full.vvp" \
  "$COMPONENTS/74HC/74hc00.v" \
  "$COMPONENTS/74HC/74hc04.v" \
  "$COMPONENTS/74HC/74hc21.v" \
  "$COMPONENTS/74HC/74hc32.v" \
  "$COMPONENTS/74HC/74hc74.v" \
  "$COMPONENTS/74HC/74hc86.v" \
  "$COMPONENTS/74HC/74hc157.v" \
  "$COMPONENTS/74HC/74hc161.v" \
  "$COMPONENTS/74HC/74hc164.v" \
  "$COMPONENTS/74HC/74hc245.v" \
  "$COMPONENTS/74HC/74hc283.v" \
  "$COMPONENTS/74HC/74hc541.v" \
  "$COMPONENTS/74HC/74hc574.v" \
  "$COMPONENTS/74HC/74hc688.v" \
  "$COMPONENTS/Memory/62256.v" \
  "$COMPONENTS/Memory/at28c256.v" \
  "$ROOT/rtl/rv8gr_chip_level.v" \
  "$ROOT/tb/tb_rv8gr_chip_full.v"

cd "$ROOT"
vvp tb/rv8gr_chip_full.vvp
