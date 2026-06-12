import inspect

from ubcpdk import PDK
from ubcpdk.config import PATH

filepath = PATH.repo / "docs" / "components.md"

skip = {
    "LIBRARY",
    "circuit_names",
    "cells",
    "component_names",
    "container_names",
    "component_names_test_ports",
    "component_names_skip_test",
    "component_names_skip_test_ports",
    "dataclasses",
    "library",
    "waveguide_template",
    "add_ports_m1",
    "add_ports_m2",
    "add_ports",
    "import_gds",
}

skip_plot = {}
skip_settings = {"flatten", "safe_cell_names"}
cells = PDK.cells


with open(filepath, "w+") as f:
    f.write("# Cells\n\n")
    f.write("| Name | Description |\n")
    f.write("|------|-------------|\n")

    cell_entries = []
    for name in sorted(cells.keys()):
        if name in skip or name.startswith("_"):
            continue
        print(name)
        sig = inspect.signature(cells[name])
        kwargs = ", ".join(
            [
                f"{p}={repr(sig.parameters[p].default)}"
                for p in sig.parameters
                if isinstance(sig.parameters[p].default, int | float | str | tuple)
                and p not in skip_settings
            ]
        )
        doc = inspect.getdoc(cells[name]) or ""
        first_line = doc.split("\n")[0] if doc else ""
        f.write(f"| [{name}](#{name}) | {first_line} |\n")
        cell_entries.append(name)

    f.write("\n")

    for name in cell_entries:
        f.write(f"\n## {name}\n\n")
        f.write(f"::: ubcpdk.cells.{name}\n\n")
