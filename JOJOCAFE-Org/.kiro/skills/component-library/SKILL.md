---
name: component-library
description: Shared component-library workflow for RV8/RV8GR and future JOJOCAFE hardware projects. Use when creating, updating, verifying, or reusing 74HC logic models, memory models, DIP pinout docs, or local datasheet evidence.
---

# Component Library Workflow

## Source of Truth

The shared reusable component repository is:

- Local path: `/home/jo/kiro/Components`
- GitHub: `git@github.com:JOJOCAFE/Components.git`
- Branch: `main`

Use this repository for reusable 74HC logic chips, memory parts, DIP pinout notes, smoke tests, and local datasheet evidence. Do not copy component models into an RV8 project unless a project intentionally needs a frozen local snapshot.

## Team Responsibility

- Pim routes component-library requests.
- Ohm owns physical package and pinout documentation, including DIP/PDIP evidence.
- Mint owns Verilog component models and smoke-test benches.
- Fern verifies package evidence, pin tables, local source references, and smoke-test results.
- Bank resolves chip-selection questions and approves new component families.

## Folder Rules

- `74HC/`: 74HC-family Verilog models plus `74hcxx-pin.md` files.
- `Memory/`: EEPROM, flash, and SRAM models plus `<part>-pin.md` files.
- `source/`: only local manufacturer PDFs that are cited by pinout docs or needed as durable evidence.

Keep `source/` clean. Remove duplicate downloads, failed PDFs, HTML dumps, temporary files, and `Zone.Identifier` sidecars.

## Pinout Rule

Pinout docs are physical wiring artifacts. Do not create or change pin tables from memory.

For DIP builds, the cited source must explicitly show one of:

- DIP
- PDIP
- P-DIP
- N or P plastic DIP package with package table evidence
- manufacturer package text that clearly says plastic dual-in-line

If a Verilog model exists but no manufacturer-verified DIP source exists, create or keep a blocked placeholder pin doc instead of guessing. Current blocked placeholders:

- `74HC/74hc150-pin.md`
- `74HC/74hc260-pin.md`

## Datasheet Source Policy

Prefer official manufacturer PDFs when they are directly accessible and prove the required DIP/PDIP package. Local PDFs in `source/` are acceptable when they are manufacturer datasheets captured for durable evidence.

AllDatasheet can be used as a locator and download helper, but the pinout doc must still cite the manufacturer represented by the PDF, not memory or an uncited web summary.

## AllDatasheet Access Method

Use this when a manufacturer PDF is hard to find directly:

1. Search by part number:

   ```text
   https://www.alldatasheet.com/view.jsp?Searchword=74HC10
   ```

2. Open an exact manufacturer result page, for example:

   ```text
   https://www.alldatasheet.com/datasheet-pdf/pdf/1687873/NEXPERIA/74HC10.html
   ```

3. Prefer the `PDF` view tab over the `Download` tab. Fetch the view page:

   ```text
   https://www.alldatasheet.com/datasheet-pdf/view/<id>/<maker>/<part>.html
   ```

4. Parse the PDF.js iframe `file=` value. It looks like:

   ```text
   //www.alldatasheet.com/datasheet-pdf/view/<id>/<maker>/<part>/<token>/datasheet.pdf
   ```

5. Download that `datasheet.pdf` URL and confirm it starts with `%PDF`.

Alternative download flow:

1. Open `/datasheet-pdf/download/<id>/<maker>/<part>.html`.
2. Parse the visible five-digit security code.
3. Parse hidden `tmpinfo1aa`.
4. POST `innum=<code>&tmpinfo1aa=<token>` back to the same download URL.
5. Confirm the response is a PDF before saving it.

Do not keep failed one-page PDFs, HTML pages saved as `.pdf`, or duplicate datasheets after the needed evidence file is selected.

## Verification Commands

Run from `/home/jo/kiro`:

```sh
iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v
vvp /tmp/tb_74hc_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```

Expected pass markers:

- `74HC SMOKE TEST PASSED`
- `MEMORY SMOKE TEST PASSED`

## Final Review Checklist

- Every non-blocked local pin doc cites a source.
- Every local PDF citation resolves under `/home/jo/kiro/Components/source`.
- DIP/PDIP package evidence is explicit.
- No duplicate temporary PDFs remain in `source/`.
- Verilog smoke tests pass.
- If pushed, the Components repo status is clean and tracking `origin/main`.
