"""Write components_plot.md with kwasm viewers."""

import base64
import inspect
import shutil
import traceback
from enum import Enum

import kwasm.embed
import matplotlib as mpl
import matplotlib.pyplot as plt
from gdsfactory.serialization import clean_value_json

mpl.use("Agg")

from ubcpdk import PDK
from ubcpdk.config import PATH

PDK.activate()
cells = PDK.cells

filepath = PATH.repo / "docs" / "components_plot.md"
kwasm_dir = PATH.repo / "docs" / "kwasm"
gds_dir = kwasm_dir / "gds"

skip = {
    "LIBRARY",
    "circuit_names",
    "component_factory",
    "component_names",
    "container_names",
    "component_names_test_ports",
    "component_names_skip_test",
    "component_names_skip_test_ports",
    "dataclasses",
    "library",
    "waveguide_template",
}

skip_plot: tuple[str, ...] = ("add_fiber_array_siepic",)
skip_settings: tuple[str, ...] = ("flatten", "safe_cell_names")


def _setup_kwasm_viewer() -> None:
    """Write the shared kwasm viewer HTML (with empty GDS slot)."""
    if kwasm_dir.exists():
        shutil.rmtree(kwasm_dir)
    gds_dir.mkdir(parents=True)
    template = kwasm.embed._read_artifacts()
    template = template.replace("KWASM_GDS_B64", "")
    lyp_path = PATH.lyp
    if lyp_path.exists():
        lyp_b64 = base64.b64encode(lyp_path.read_bytes()).decode("ascii")
        template = template.replace("KWASM_LYP_B64", lyp_b64)
    else:
        template = template.replace("KWASM_LYP_B64", "")
    template = template.replace("KWASM_LYRDB_B64", "")
    template = template.replace("KWASM_NETLIST_B64", "")
    (kwasm_dir / "viewer.html").write_text(template)


def _write_gds(name: str, kwargs: str) -> bool:
    """Instantiate cell and write GDS + PNG. Returns True on success."""
    try:
        sig = inspect.signature(cells[name])
        defaults = {}
        for p in sig.parameters:
            v = sig.parameters[p].default
            if isinstance(v, int | float | str | tuple):
                defaults[p] = v
        c = cells[name](**defaults)
        c.write(str(gds_dir / f"{name}.gds"))
        c.plot()
        plt.savefig(str(gds_dir / f"{name}.png"), dpi=150, bbox_inches="tight")
        plt.close("all")
    except Exception:
        traceback.print_exc()
        plt.close("all")
        return False
    else:
        return True


_setup_kwasm_viewer()

with open(filepath, "w+") as f:
    f.write(
        """

Here are the components available in the PDK


Cells
=============================
"""
    )

    for name in sorted(cells.keys()):
        if name in skip or name.startswith("_"):
            continue
        print(name)
        sig = inspect.signature(cells[name])

        # Check if function has required parameters (no default value)
        has_required_params = any(
            param.default == inspect.Parameter.empty
            for param in sig.parameters.values()
        )

        kwargs_list = []
        for p in sig.parameters:
            default = sig.parameters[p].default
            if p in skip_settings:
                continue
            # Handle enum types
            if isinstance(default, Enum):
                enum_class = type(default).__name__
                enum_value = default.name
                kwargs_list.append(f"{p}={enum_class}.{enum_value}")
            # Handle basic types
            elif isinstance(default, int | float | str | tuple):
                kwargs_list.append(f"{p}={clean_value_json(default)!r}")
        kwargs = ", ".join(kwargs_list)

        # Skip plotting if function has required params or is in skip_plot list
        if name in skip_plot or has_required_params:
            f.write(
                f"""

## {name}


::: ubcpdk.cells.{name}

"""
            )
        else:
            has_gds = _write_gds(name, kwargs)

            f.write(
                f"""

## {name}


::: ubcpdk.cells.{name}

"""
            )

            if has_gds:
                f.write('=== "Static"\n\n')
                f.write(f"    ![{name}](kwasm/gds/{name}.png)\n\n")
                f.write('=== "Dynamic"\n\n')
                f.write(
                    f'    <iframe src="kwasm/viewer.html?url=gds/{name}.gds"'
                    f' loading="lazy" width="100%" height="400"'
                    f' style="border:none"></iframe>\n\n'
                )

            f.write(
                f"""```python
from ubcpdk import PDK, cells
from ubcpdk.tech import LayerMapUbc

PDK.activate()

c = cells.{name}({kwargs})
c.plot()
```
"""
            )

print(f"Wrote {filepath}")
