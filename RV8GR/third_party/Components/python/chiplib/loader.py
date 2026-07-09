"""Program image loaders for ROM/RAM chip models."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

ImageFormat = Literal["auto", "bin", "hex", "ihex"]


class ImageLoadError(ValueError):
    """Raised when a program/data image cannot be parsed or loaded."""


def load_image(path: str | Path, fmt: ImageFormat = "auto") -> bytes:
    """Read a .bin, Intel HEX, or simple hex text file as bytes."""
    image_path = Path(path)
    actual_fmt = _detect_format(image_path, fmt)
    if actual_fmt == "bin":
        return image_path.read_bytes()

    text = image_path.read_text()
    if actual_fmt == "ihex" or _looks_like_ihex(text):
        return parse_ihex(text)
    return parse_hex_text(text)


def load_memory(
    chip,
    path: str | Path,
    *,
    offset: int = 0,
    fmt: ImageFormat = "auto",
    clear: int | None = None,
) -> int:
    """Load an image into a memory chip's ``data`` bytearray.

    Returns the number of bytes copied. ``chip`` may be any Components memory
    model exposing a mutable ``data`` bytearray.
    """
    if not hasattr(chip, "data"):
        raise TypeError(f"{chip!r} does not expose a data bytearray")
    if offset < 0:
        raise ImageLoadError("offset must be non-negative")
    if clear is not None:
        chip.data[:] = bytes([clear & 0xFF]) * len(chip.data)

    payload = load_image(path, fmt)
    end = offset + len(payload)
    if end > len(chip.data):
        raise ImageLoadError(
            f"image does not fit: {len(payload)} bytes at offset {offset} "
            f"for memory size {len(chip.data)}"
        )
    chip.data[offset:end] = payload
    return len(payload)


def parse_hex_text(text: str) -> bytes:
    """Parse simple text hex: ``30 42 01 02`` or ``0x30,0x42``."""
    cleaned = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].split(";", 1)[0]
        line = re.sub(r"//.*$", "", line)
        cleaned.append(line)
    tokens = re.findall(r"(?:0x)?[0-9a-fA-F]{1,2}", " ".join(cleaned))
    if not tokens:
        raise ImageLoadError("no hex bytes found")
    try:
        return bytes(int(tok.replace("0x", "").replace("0X", ""), 16) for tok in tokens)
    except ValueError as exc:
        raise ImageLoadError(str(exc)) from exc


def parse_ihex(text: str) -> bytes:
    """Parse Intel HEX data records into a dense byte image."""
    memory: dict[int, int] = {}
    base = 0
    eof_seen = False
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(":"):
            raise ImageLoadError(f"line {lineno}: Intel HEX record must start with ':'")
        try:
            count = int(line[1:3], 16)
            addr = int(line[3:7], 16)
            rectype = int(line[7:9], 16)
            data = bytes.fromhex(line[9:9 + count * 2])
            checksum = int(line[9 + count * 2:11 + count * 2], 16)
        except ValueError as exc:
            raise ImageLoadError(f"line {lineno}: malformed Intel HEX record") from exc
        values = [count, (addr >> 8) & 0xFF, addr & 0xFF, rectype, *data, checksum]
        if sum(values) & 0xFF:
            raise ImageLoadError(f"line {lineno}: checksum mismatch")
        if rectype == 0x00:
            absolute = base + addr
            for i, byte in enumerate(data):
                memory[absolute + i] = byte
        elif rectype == 0x01:
            eof_seen = True
            break
        elif rectype == 0x02:
            if count != 2:
                raise ImageLoadError(f"line {lineno}: bad extended segment address")
            base = int.from_bytes(data, "big") << 4
        elif rectype == 0x04:
            if count != 2:
                raise ImageLoadError(f"line {lineno}: bad extended linear address")
            base = int.from_bytes(data, "big") << 16
        else:
            continue
    if not eof_seen and not memory:
        raise ImageLoadError("no Intel HEX data records found")
    if not memory:
        return b""
    max_addr = max(memory)
    image = bytearray(max_addr + 1)
    for addr, byte in memory.items():
        image[addr] = byte
    return bytes(image)


def _detect_format(path: Path, fmt: ImageFormat) -> str:
    if fmt != "auto":
        return fmt
    suffix = path.suffix.lower()
    if suffix == ".bin":
        return "bin"
    if suffix in (".hex", ".ihex", ".ihx"):
        return "hex"
    return "bin"


def _looks_like_ihex(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.startswith(":")
    return False
