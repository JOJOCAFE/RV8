
"""Catalog chip models for the full Components 74HC and memory set.

These models use repository pinout documentation as the pin-number/name source:
embedded Verilog comments in the 74xx and Memory Verilog model files.
They mirror the behavior of the companion Verilog models. The older
hand-written classes in chips.py remain for the RV8GR-V2 starter set; this file
covers the rest of the shared Components catalog.
"""

from __future__ import annotations

from pathlib import Path
import re

from .core import Chip, Delay, PinSpec, Z, bit

ROOT = Path(__file__).resolve().parents[2]


def _parse_pinout(folder: str, part: str) -> dict[int, str]:
    base = _folder_path(folder)
    path = base / f"{part.lower()}.v"
    pins: dict[int, str] = {}
    if path.exists():
        for line in _pinout_lines(path, embedded=True):
            m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", line)
            if m:
                pins[int(m.group(1))] = m.group(2).strip()
    return pins


def _pinout_lines(path: Path, *, embedded: bool) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not embedded:
        return lines
    result: list[str] = []
    inside = False
    for line in lines:
        if line.strip() == "// Embedded pinout documentation.":
            inside = True
            continue
        if inside and line.startswith("`timescale"):
            break
        if inside and line.startswith("//"):
            result.append(line[2:].strip())
    return result


def _folder_path(folder: str) -> Path:
    if folder == "74HC":
        return ROOT / "Verilog" / "74xx"
    if folder == "Memory":
        return ROOT / "Verilog" / "Memory"
    return ROOT / folder


OUTPUT_PATTERNS = (
    r"^/?\d*Y\d*$", r"^Y\d+$", r"^\d*Q(_bar|_BAR|')?$", r"^/?QH$", r"^QH'$",
    r"^QA$", r"^QB$", r"^QC$", r"^QD$", r"^QE$", r"^QF$", r"^QG$", r"^QH$",
    r"^/QH$", r"^/\dQ$", r"^\dQ_bar$", r"^\dQ$", r"^Q\d+$", r"^S\d+$",
    r"^F\d+$", r"^C4$", r"^Cout$", r"^RCO$", r"^TC$", r"^/CO$", r"^/BO$",
    r"^EO$", r"^GS$", r"^A_eq_B$", r"^P$", r"^G$", r"^Cn\+4$",
    r"^QA_GT_B$", r"^QA_EQ_B$", r"^QA_LT_B$", r"^DATA AVAILABLE$", r"^DATA OUT [ABCD]$",
    r"^COLUMN X[1-4]$", r"^X$",
)
BIDIR_PATTERNS = (r"^I/O\d+$", r"^DQ\d+$", r"^[A-H]/Q[A-H]$", r"^[AB]\d+$")


def _direction(part: str, name: str) -> str:
    if name in ("GND", "VCC", "VSS", "VDD"):
        return "power"
    if name == "NC":
        return "nc"
    if part == "74HC245" and re.match(r"^[AB]\d+$", name):
        return "bidir"
    if part == "74HC593" and re.match(r"^[A-H]/Q[A-H]$", name):
        return "bidir"
    if part in ("62256", "AS6C62256", "CY7C199", "AT28C256") and re.match(r"^I/O\d+$", name):
        return "bidir"
    if part == "SST39SF010A" and re.match(r"^DQ\d+$", name):
        return "bidir"
    if part == "74HC148" and name in ("A0", "A1", "A2", "EO", "GS"):
        return "out"
    if any(re.match(pat, name) for pat in OUTPUT_PATTERNS):
        return "out"
    return "in"


def _pin_specs(part: str, folder: str) -> list[PinSpec]:
    pinout = _parse_pinout(folder, part) or FALLBACK_PINOUTS.get(part, {})
    if not pinout:
        raise KeyError(f"no pinout for {part}")
    return [PinSpec(num, name, _direction(part, name), name.startswith("/")) for num, name in sorted(pinout.items())]


class CatalogChip(Chip):
    def __init__(self, part: str, name: str, folder: str = "74HC", delay_ns: int = 15):
        self.part = part
        super().__init__(name, _pin_specs(part, folder), Delay(delay_ns))
        self._state = 0
        self._state2 = 0
        self._state_by_block: dict[int, int] = {}
        self._scan_col = 0
        self._prev_we = 1
        self.data = bytearray(1 << (17 if part == "SST39SF010A" else 15))

    def has(self, name: str) -> bool:
        return name in self.pin_names

    def r(self, name: str) -> int:
        return bit(self.read(name)) if self.has(name) else 0

    def z(self, name: str) -> None:
        if self.has(name):
            self.output(name, Z)

    def o(self, name: str, value: int | str) -> None:
        if self.has(name):
            self.output(name, value)

    def clock_edge_for_pin(self, pin: int | str | None = None) -> str:
        if pin is None:
            return "rising"
        name = self.pin(pin).name
        if self.part in ("74HC73", "74HC112") and name.endswith("CP"):
            return "falling"
        return "rising"

    def names(self, pattern: str) -> list[str]:
        rx = re.compile(pattern)
        return sorted((n for n in self.pin_names if rx.match(n)), key=_natural_key)

    def _mux_select(self, names: list[str]) -> int:
        return sum(self.r(n) << i for i, n in enumerate(names))

    def _read_names(self, names: list[str]) -> int:
        return sum(self.r(n) << i for i, n in enumerate(names))

    def _write_names(self, names: list[str], value: int) -> None:
        for i, name in enumerate(names):
            self.o(name, (value >> i) & 1)

    def update(self) -> None:
        p = self.part
        if p in ("74HC02", "74HC08", "74HC266"):
            gates = _numbered_gates(self, 4, ["A", "B"], "Y")
            for ins, out in gates:
                a, b = [self.r(n) for n in ins]
                if p == "74HC02": self.o(out, 1 - (a | b))
                elif p == "74HC08": self.o(out, a & b)
                else: self.o(out, 1 - (a ^ b))
        elif p in ("74HC07", "74HC14"):
            for i in range(1, 7):
                if p == "74HC07": self.o(f"{i}Y", self.r(f"{i}A"))
                else: self.o(f"{i}Y", 1 - self.r(f"{i}A"))
        elif p in ("74HC10", "74HC11", "74HC20", "74HC27"):
            width = {"74HC10": 3, "74HC11": 3, "74HC20": 4, "74HC27": 3}[p]
            blocks = 2 if p == "74HC20" else 3
            op = "and" if p == "74HC11" else ("nand" if p in ("74HC10", "74HC20") else "nor")
            for i in range(1, blocks + 1):
                vals = [self.r(f"{i}{chr(ord('A') + j)}") for j in range(width)]
                val = all(vals) if op == "and" else (1 - int(all(vals)) if op == "nand" else 1 - int(any(vals)))
                self.o(f"{i}Y", int(val))
        elif p == "74HC30":
            vals = [self.r(n) for n in ["A", "B", "C", "D", "E", "F", "G", "H"]]
            self.o("Y", 1 - int(all(vals)))
        elif p == "74HC4078":
            vals = [self.r(n) for n in ["A", "B", "C", "D", "E", "F", "G", "H"]]
            any_high = int(any(vals))
            self.o("X", 1 - any_high); self.o("Y", any_high)
        elif p == "74HC138":
            enabled = self.r("G1") and not self.r("/G2A") and not self.r("/G2B")
            sel = self.r("A") | (self.r("B") << 1) | (self.r("C") << 2)
            for i in range(8): self.o(f"/Y{i}", 0 if enabled and i == sel else 1)
        elif p == "74HC139":
            for block in (1, 2):
                enabled = not self.r(f"/{block}G")
                sel = self.r(f"{block}A") | (self.r(f"{block}B") << 1)
                for i in range(4): self.o(f"/{block}Y{i}", 0 if enabled and i == sel else 1)
        elif p == "74HC238":
            enabled = not self.r("E1") and not self.r("E2") and self.r("E3")
            sel = self.r("A0") | (self.r("A1") << 1) | (self.r("A2") << 2)
            for i in range(8): self.o(f"Y{i}", 1 if enabled and i == sel else 0)
        elif p == "74HC42":
            sel = self.r("0A") | (self.r("1A") << 1) | (self.r("2A") << 2) | (self.r("3A") << 3)
            for i in range(10): self.o(f"{i}Y", 0 if i == sel else 1)
        elif p == "74HC147":
            selected = 0
            for i in range(10):
                if self.has(f"I{i}") and not self.r(f"I{i}"):
                    selected = i
            # Outputs are active-low BCD bits in the Verilog model.
            self.o("Y1", 1 - ((selected >> 0) & 1))
            self.o("Y2", 1 - ((selected >> 1) & 1))
            self.o("Y3", 1 - ((selected >> 2) & 1))
        elif p == "74HC148":
            if self.r("EI"):
                self.o("EO", 0); self.o("GS", 0); self.o("A0", 1); self.o("A1", 1); self.o("A2", 1)
            else:
                selected = None
                for i in range(8):
                    if self.has(f"I{i}") and not self.r(f"I{i}"):
                        selected = i
                if selected is None:
                    self.o("EO", 1); self.o("GS", 0); selected = 0
                else:
                    self.o("EO", 0); self.o("GS", 1)
                self.o("A0", 1 - ((selected >> 0) & 1))
                self.o("A1", 1 - ((selected >> 1) & 1))
                self.o("A2", 1 - ((selected >> 2) & 1))
        elif p == "74HC154":
            enabled = not self.r("E0") and not self.r("E1")
            sel = self.r("A0") | (self.r("A1") << 1) | (self.r("A2") << 2) | (self.r("A3") << 3)
            for i in range(16): self.o(f"Y{i}", 0 if enabled and i == sel else 1)
        elif p == "74HC155":
            sel = self.r("A") | (self.r("B") << 1)
            for i in range(4):
                self.o(f"1Y{i}", 0 if self.r("1C") and not self.r("1G") and i == sel else 1)
                self.o(f"2Y{i}", 0 if not self.r("2C") and not self.r("2G") and i == sel else 1)
        elif p in ("74HC151", "74HC251"):
            sel = self.r("A") | (self.r("B") << 1) | (self.r("C") << 2)
            val = self.r(f"D{sel}")
            oe_name = "/OE" if self.has("/OE") else "/G"
            if self.r(oe_name):
                if p == "74HC251": self.o("Y", Z); self.o("/Y", Z)
                else: self.o("Y", 0); self.o("/Y", 1)
            else:
                self.o("Y", val); self.o("/Y", 1 - val)
        elif p in ("74HC153", "74HC352"):
            sel = self.r("A") | (self.r("B") << 1)
            invert = p == "74HC352"
            for block in (1, 2):
                en = self.r(f"/{block}G") if self.has(f"/{block}G") else self.r(f"{block}G")
                val = 0 if en else self.r(f"{block}C{sel}")
                self.o(f"{block}Y", 1 - val if invert else val)
        elif p in ("74HC158", "74HC257"):
            sel = self.r("S")
            en = self.r("E") if p == "74HC158" else self.r("/OE")
            for i in range(1, 5):
                a0 = f"{i}I0" if p == "74HC158" else f"{i}A"
                a1 = f"{i}I1" if p == "74HC158" else f"{i}B"
                val = self.r(a1 if sel else a0)
                if p == "74HC257" and en: self.o(f"{i}Y", Z)
                else: self.o(f"{i}Y", 1 - val if p == "74HC158" else val)
        elif p in ("74HC240", "74HC244", "74HC541"):
            inv = p == "74HC240"
            for group, oe in [(1, "/1OE" if self.has("/1OE") else "/OE1"), (2, "/2OE" if self.has("/2OE") else "/OE2")]:
                for i in range(1, 5 if p in ("74HC240", "74HC244") else 9):
                    if p in ("74HC240", "74HC244"):
                        a = f"{group}A{i}"; y = f"{group}Y{i}"
                    else:
                        a = f"A{i}"; y = f"Y{i}"
                    if self.has(a) and self.has(y): self.o(y, Z if self.r(oe) else (1 - self.r(a) if inv else self.r(a)))
        elif p == "74HC273":
            if not self.r("/CLR"): self._state = 0
            self._write_names([f"{i}Q" for i in range(1, 9)], self._state)
        elif p in ("74HC374", "74HC377"):
            qnames = [f"{i}Q" for i in range(1, 9)] if p == "74HC374" else [f"Q{i}" for i in range(8)]
            if p == "74HC374" and self.r("/OE"):
                for q in qnames: self.o(q, Z)
            else: self._write_names(qnames, self._state)
        elif p in ("74HC160", "74HC162", "74HC163"):
            clear_async = p == "74HC160"
            if clear_async and not self.r("MR"): self._state = 0
            self._write_names(["Q0", "Q1", "Q2", "Q3"], self._state)
            terminal = 9 if p in ("74HC160", "74HC162") else 15
            self.o("TC", 1 if self._state == terminal and self.r("CET") else 0)
        elif p in ("74HC73", "74HC112"):
            self._update_jk_outputs()
        elif p == "74HC165":
            if not self.r("/SH/LD"): self._state = self._read_names(["A", "B", "C", "D", "E", "F", "G", "H"])
            self.o("QH", (self._state >> 7) & 1); self.o("/QH", 1 - ((self._state >> 7) & 1))
        elif p == "74HC166":
            if not self.r("/CLR"): self._state = 0
            self.o("QH", (self._state >> 7) & 1)
        elif p == "74HC181":
            a = self._read_names(["A0", "A1", "A2", "A3"]); b = self._read_names(["B0", "B1", "B2", "B3"])
            s = self.r("S0") | (self.r("S1") << 1) | (self.r("S2") << 2) | (self.r("S3") << 3)
            f = (a + b + self.r("Cn")) & 0xF if not self.r("M") else _alu_logic(a, b, s)
            self._write_names(["F0", "F1", "F2", "F3"], f)
            self.o("A_eq_B", 1 if f == 0xF else 0); self.o("Cn+4", 1 if a + b + self.r("Cn") > 0xF else 0)
            self.o("P", 0); self.o("G", 0)
        elif p == "74HC193":
            if self.r("CLR"): self._state = 0
            elif not self.r("/LOAD"): self._state = self._read_names(["A", "B", "C", "D"])
            self._write_names(["QA", "QB", "QC", "QD"], self._state)
            self.o("/CO", 0 if self._state == 0xF else 1); self.o("/BO", 0 if self._state == 0 else 1)
        elif p == "74HC593":
            if not self.r("CCLR"): self._state = 0
            elif not self.r("CLOAD"): self._state = self._state2
            out_en = self.r("G") or not self.r("/G")
            for i, name in enumerate(["A/QA", "B/QB", "C/QC", "D/QD", "E/QE", "F/QF", "G/QG", "H/QH"]):
                self.o(name, (self._state >> i) & 1 if out_en else Z)
            self.o("RCO", 1 if self._state == 0 else 0)
        elif p == "74HC595":
            qnames = ["QA", "QB", "QC", "QD", "QE", "QF", "QG", "QH"]
            if self.r("/OE"):
                for q in qnames: self.o(q, Z)
            else: self._write_names(qnames, self._state2)
            self.o("QH'", (self._state >> 7) & 1)
        elif p == "74HC688":
            a = self._read_names(["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"])
            b = self._read_names(["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7"])
            self.o("Y", 1 if self.r("/E") or a != b else 0)
        elif p == "74HC85":
            a = self._read_names(["A0", "A1", "A2", "A3"]); b = self._read_names(["B0", "B1", "B2", "B3"])
            eq = a == b and self.r("IA_EQ_B")
            self.o("QA_EQ_B", 1 if eq else 0); self.o("QA_LT_B", 1 if (a < b or (a == b and self.r("IA_LT_B"))) and not eq else 0)
            self.o("QA_GT_B", 1 if (a > b or (a == b and self.r("IA_GT_B"))) and not eq else 0)
        elif p == "74HC922":
            col_names = ["COLUMN X1", "COLUMN X2", "COLUMN X3", "COLUMN X4"]
            for i, n in enumerate(col_names): self.o(n, 0 if i == self._scan_col else 1)
            code = self._scan_col; avail = 0
            for row in range(4):
                if not self.r(f"ROW Y{row+1}"):
                    code = (row << 2) | self._scan_col; avail = 1
            self.o("DATA AVAILABLE", avail & self.r("KEYBOUNCE MASK"))
            for i, n in enumerate(["DATA OUT A", "DATA OUT B", "DATA OUT C", "DATA OUT D"]):
                self.o(n, Z if self.r("OUTPUT ENABLE") else ((code >> i) & 1))
        elif p in ("AT28C256", "62256", "AS6C62256", "CY7C199", "SST39SF010A"):
            self._update_memory()

    def clock_edge(self, pin: int | str | None = None) -> None:
        p = self.part
        pin_name = self.pin(pin).name if pin is not None else None
        if p in ("74HC160", "74HC162", "74HC163"):
            if not self.r("MR"): self._state = 0
            elif not self.r("PE"): self._state = self._read_names(["D0", "D1", "D2", "D3"])
            elif self.r("CEP") and self.r("CET"):
                if p in ("74HC160", "74HC162"): self._state = 0 if self._state == 9 else (self._state + 1) & 0xF
                else: self._state = (self._state + 1) & 0xF
        elif p == "74HC273":
            if not self.r("/CLR"): self._state = 0
            else: self._state = self._read_names([f"{i}D" for i in range(1, 9)])
        elif p == "74HC374":
            self._state = self._read_names([f"{i}D" for i in range(1, 9)])
        elif p == "74HC377":
            if not self.r("E"): self._state = self._read_names([f"D{i}" for i in range(8)])
        elif p in ("74HC73", "74HC112"):
            self._clock_jk(pin_name)
        elif p == "74HC165":
            if not self.r("/SH/LD"): self._state = self._read_names(["A", "B", "C", "D", "E", "F", "G", "H"])
            elif not self.r("CLK INH"): self._state = ((self._state << 1) & 0xFF) | self.r("SER")
        elif p == "74HC166":
            if not self.r("/CLR"): self._state = 0
            elif not self.r("/SH/LD"): self._state = self._read_names(["A", "B", "C", "D", "E", "F", "G", "H"])
            elif not self.r("CLK INH"): self._state = ((self._state << 1) & 0xFF) | self.r("SER")
        elif p == "74HC193":
            if self.r("CLR"): self._state = 0
            elif not self.r("/LOAD"): self._state = self._read_names(["A", "B", "C", "D"])
            elif pin_name == "UP" and self.r("DOWN"): self._state = (self._state + 1) & 0xF
            elif pin_name == "DOWN" and self.r("UP"): self._state = (self._state - 1) & 0xF
            elif pin_name is None:
                if self.r("UP") and not self.r("DOWN"): self._state = (self._state + 1) & 0xF
                elif self.r("DOWN") and not self.r("UP"): self._state = (self._state - 1) & 0xF
        elif p == "74HC593":
            if pin_name == "RCK" and not self.r("RCKEN"):
                self._state2 = self._read_names(["A/QA", "B/QB", "C/QC", "D/QD", "E/QE", "F/QF", "G/QG", "H/QH"])
            elif pin_name in ("CCK", None):
                if not self.r("CCLR"): self._state = 0
                elif not self.r("CLOAD"): self._state = self._state2
                elif self.r("CCKEN") or not self.r("/CCKEN"): self._state = (self._state + 1) & 0xFF
        elif p == "74HC595":
            if pin_name in ("SRCLK", None):
                if not self.r("/SRCLR"): self._state = 0
                else: self._state = ((self._state << 1) & 0xFF) | self.r("SER")
            if pin_name in ("RCLK", None):
                self._state2 = self._state
        elif p == "74HC922":
            self._scan_col = (self._scan_col + 1) & 3
        self.update()

    def _clock_jk(self, pin_name: str | None = None) -> None:
        blocks = [1, 2]
        if pin_name is not None:
            blocks = [int(pin_name[0])] if pin_name[:1] in ("1", "2") else []
        for b in blocks:
            clear = f"{b}R" if self.has(f"{b}R") else f"{b}RD"
            preset = f"{b}SD"
            q = self._state_by_block.get(b, 0)
            if self.has(clear) and not self.r(clear): q = 0
            elif self.has(preset) and not self.r(preset): q = 1
            else:
                j = self.r(f"{b}J"); k = self.r(f"{b}K")
                if j and not k: q = 1
                elif k and not j: q = 0
                elif j and k: q = 1 - q
            self._state_by_block[b] = q

    def _update_jk_outputs(self) -> None:
        for b in (1, 2):
            q = self._state_by_block.get(b, 0)
            clear = f"{b}R" if self.has(f"{b}R") else f"{b}RD"
            preset = f"{b}SD"
            if self.has(clear) and not self.r(clear): q = 0
            elif self.has(preset) and not self.r(preset): q = 1
            self._state_by_block[b] = q
            self.o(f"{b}Q", q); self.o(f"{b}Q_bar", 1 - q); self.o(f"{b}Q_bar", 1 - q)
            self.o(f"{b}Q_bar", 1 - q)
            # Some pinout docs use a slash instead of the Verilog-style suffix.
            self.o(f"/{b}Q", 1 - q)

    def _update_memory(self) -> None:
        if self.part == "SST39SF010A":
            addr_names = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12", "A13", "A14", "A15", "A16"]
            dq_names = [f"DQ{i}" for i in range(8)]
        else:
            addr_names = [f"A{i}" for i in range(15)]
            dq_names = [f"I/O{i}" for i in range(8)]
        addr = self._read_names(addr_names) % len(self.data)
        selected = not self.r("/CE")
        we = self.r("/WE")
        oe = self.r("/OE")
        if self.part == "SST39SF010A":
            if selected and oe and self._prev_we and not we:
                self.data[addr] = self._read_names(dq_names)
        elif selected and not we:
            self.data[addr] = self._read_names(dq_names)
        self._prev_we = we
        read_enabled = selected and we and not oe
        if read_enabled: self._write_names(dq_names, self.data[addr])
        else:
            for n in dq_names: self.o(n, Z)


def _natural_key(name: str):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", name)]


def _numbered_gates(chip: CatalogChip, blocks: int, inputs: list[str], output_suffix: str):
    gates = []
    for i in range(1, blocks + 1):
        ins = [f"{i}{s}" for s in inputs]
        out = f"{i}{output_suffix}"
        if all(chip.has(n) for n in ins) and chip.has(out): gates.append((ins, out))
    return gates


def _alu_logic(a: int, b: int, s: int) -> int:
    table = {
        0x0: (~a) & 0xF, 0x1: (~(a | b)) & 0xF, 0x2: ((~a) & b) & 0xF, 0x3: 0,
        0x4: (~(a & b)) & 0xF, 0x5: (~b) & 0xF, 0x6: (a ^ b) & 0xF, 0x7: (a & (~b)) & 0xF,
        0x8: ((~a) | b) & 0xF, 0x9: (~(a ^ b)) & 0xF, 0xA: b, 0xB: (a & b) & 0xF,
        0xC: 0xF, 0xD: (a | (~b)) & 0xF, 0xE: (a | b) & 0xF, 0xF: a,
    }
    return table.get(s, 0) & 0xF


CATALOG_PARTS = {
    "74HC02", "74HC07", "74HC08", "74HC10", "74HC11", "74HC112", "74HC138", "74HC139",
    "74HC14", "74HC147", "74HC148", "74HC151", "74HC153", "74HC154", "74HC155",
    "74HC158", "74HC160", "74HC162", "74HC163", "74HC165", "74HC166", "74HC181", "74HC193",
    "74HC20", "74HC238", "74HC240", "74HC244", "74HC251", "74HC257", "74HC266",
    "74HC27", "74HC273", "74HC30", "74HC352", "74HC374", "74HC377", "74HC4078", "74HC42",
    "74HC593", "74HC595", "74HC73", "74HC85", "74HC922",
}
MEMORY_CATALOG_PARTS = {"AS6C62256", "CY7C199", "SST39SF010A"}


def create_catalog_chip(part: str, name: str) -> Chip:
    key = part.upper().replace("-", "")
    if key in CATALOG_PARTS:
        return CatalogChip(key, name, "74HC")
    if key in MEMORY_CATALOG_PARTS:
        return CatalogChip(key, name, "Memory", delay_ns=70)
    raise KeyError(part)
