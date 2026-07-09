# Student Catalog View

The student catalog is a smaller DB view for learner-facing tools. It keeps the
same component facts as the main DB catalog, but shows the fields a student or
teacher needs first:

- what the component is
- whether it can simulate
- whether it can export to Verilog
- whether the pinout and datasheet are verified
- a short pin preview
- visible warnings for missing information

The main audience is students around ages 10-15, while still being useful for
older learners.

## CLI

List all components in the student view:

```sh
cd python
python3 -m chiplib.cli db --student
```

List one group:

```sh
python3 -m chiplib.cli db --student --group virtual
python3 -m chiplib.cli db --student --group 74xx
python3 -m chiplib.cli db --student --group memory
```

## Python

```python
from chiplib.db import student_component_catalog

catalog = student_component_catalog(group="74xx")
first = catalog["components"][0]
print(first["part"], first["readiness"], first["capabilities"])
```

## Frontend API

HTTP and stdio adapters use the same service command:

```json
{"command": "student-component-catalog", "options": {"group": "virtual"}}
```

The response has `format: components.db.student_catalog` and component cards
like:

```json
{
  "part": "Probe",
  "title": "Single logic probe",
  "group": "virtual",
  "readiness": "usable",
  "capabilities": {
    "can_simulate": true,
    "can_export_verilog": false,
    "has_verified_pinout": false,
    "has_datasheet": false
  },
  "pins": {
    "count": 1,
    "preview": [{"number": 1, "name": "IN", "direction": "input"}]
  },
  "warnings": []
}
```

## Readiness

- `ready`: good for building and simulation examples.
- `usable`: usable, but some advanced output or evidence may be missing.
- `needs_info`: visible in the catalog, but show what is missing before
  students build with it.

## Boundary

This is only a view of DB metadata. It does not move chip behavior, Verilog
models, or pinout documentation into new places. Those implementation files stay
behind the existing service boundaries until a real UI or downstream project
needs a physical move.
