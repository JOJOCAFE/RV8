# Vendored Components Runtime

This is a small runtime snapshot from `JOJOCAFE/Components`.

Source snapshot:

- Commit: `bb4487a`
- Subject: `Add student DB catalog view`

Included:

- `DB/` component manifests and student catalog docs
- `Verilog/` 74xx and memory models used by RV8GR chip-level tests
- `python/chiplib/` Python runtime used by RV8GR verification/export tools
- `python/tests/` and `CHIP_STATUS.md` so DB audit checks still work

Not included:

- datasheet/source PDFs
- generated caches
- full Components repo history

RV8GR tools use this vendored copy by default. To test against another
Components checkout, set one of these environment variables:

```sh
COMPONENTS_ROOT=/path/to/Components tools/run_chip_level_verilog.sh
COMPONENTS_ROOT=/path/to/Components python3 sim/verify_components.py
COMPONENTS_PYTHON=/path/to/Components/python python3 tools/export_chip_level_verilog.py
```

Refresh rule: copy only `DB/`, `Verilog/`, `python/chiplib/`, `python/tests/`,
and `CHIP_STATUS.md` from the Components repo, then rerun:

```sh
python3 sim/verify_components.py
tools/run_chip_level_verilog.sh
tools/run_chip_level_full_verilog.sh
```
