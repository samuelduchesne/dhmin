# Researcher Experience Report: dhmin

Tested on: 2026-02-09
Python: 3.11
OS: Linux

## Summary

I approached `dhmin` as a researcher wanting to optimize a district heating
network. **Neither example script runs successfully.** The core function
`create_model` has a fatal bug that prevents any model from being created. The
package is effectively non-functional in its current state.

---

## Step-by-step experience

### 1. Discovery & first impressions

- `import dhmin` works; `dir(dhmin)` shows 8 public functions -- a small,
  focused API. Good.
- The module docstring is a single sentence. There is no quickstart, no
  tutorial, no rendered documentation site.
- The README has no installation instructions (just "Dependencies" as a list of
  links). The `pyproject.toml` exists but is not mentioned.
- The Sphinx docs (`doc/index.rst`) reference Python 2.7 and Pyomo version 3/4,
  which are years out of date.

### 2. Installation

```
pip install -e ".[geo,plot]"
```

This works. However:

**Issue: `openpyxl` is a missing dependency.** The `read_excel()` function is
part of the core public API and it requires `openpyxl` to read `.xlsx` files,
but `openpyxl` is not declared in `pyproject.toml`. A researcher hitting this
gets:

```
ImportError: `Import openpyxl` failed. Use pip or conda to install the openpyxl package.
```

This is confusing because `read_excel` is a first-class function -- a
researcher reasonably expects it to work after installing the package.

### 3. Running `rundh.py` (Excel example)

```
python rundh.py
```

**Result: crash.**

```
AttributeError: 'NoneType' object has no attribute 'loc'
```

at `core.py:250`. The root cause: `create_model()` unconditionally accesses
`edge_profile.loc[index, :]` in the `m.scaling_factor` initialization
(line 244-253), but `edge_profile` defaults to `None`. The `rundh.py`
example does not pass an `edge_profile`, and neither does `rundhshp.py`, so
**every invocation of `create_model` crashes**.

This is the single most critical bug -- it makes the entire package unusable.

### 4. Running `rundhshp.py` (Shapefile example)

```
python rundhshp.py
```

**Result: crash** (different error, earlier in the pipeline).

```
ValueError: Length of names must match number of levels in MultiIndex.
```

at `core.py:85`. The `rundhshp.py` script passes a 3-level MultiIndex
`(Edge, Vertex1, Vertex2)` to `create_model`, which immediately tries to set
`index.names = ["Vertex2", "Vertex1"]` (2 names for 3 levels). The `rundh.py`
example calls `edge.reset_index("Edge")` to drop the `Edge` level first, but
`rundhshp.py` does not.

### 5. Trying to construct `edge_profile` manually

Since the parameter is undocumented (the docstring just says "per-edge time
profile series"), I tried to reverse-engineer the expected format from the
source code. After constructing a `pd.Series` of `[(duration, sf)]` tuples
indexed by `(Vertex1, Vertex2)`:

```
edge_profile.loc[(22, 44), :]
```

**Also crashes** with `KeyError`. The code uses `.loc[index, :]` on a Series
(which has no columns), so the `:` slice fails on a MultiIndex. Even with a
correctly-shaped `edge_profile`, the accessor pattern is wrong.

### 6. Data format confusion

- `read_excel()` returns a vertex DataFrame with column `cost_heat`.
- `create_model()` expects columns `c_heatvar` and `c_heatfix`.
- The `rundh.py` example manually adds these columns:
  ```python
  vertex["c_heatvar"] = 0.010
  vertex["c_heatfix"] = 0
  ```
- But the `shp/README.txt` specification says vertices have a `cost_heat`
  column.
- There is no documentation explaining that `read_excel` output needs manual
  column transformations before it can be passed to `create_model`.
- A natural expectation is that `read_excel` returns data that `create_model`
  accepts directly -- this is not the case.

### 7. No tests

There are zero test files in the repository. No `tests/` directory, no
`test_*.py` files, no `conftest.py`. The `Makefile` has no test target. This
means:

- Regressions go undetected (as evidenced by the `create_model` crash).
- A contributor has no way to verify changes don't break anything.
- A researcher has no executable examples of correct API usage.

### 8. Utility functions (untestable)

- `plot_flows_min()` requires a solved model instance, which cannot be created
  (see above).
- `symmetrize()` works on DataFrames independently and is likely functional,
  but there are no tests to confirm.
- `get_entity()`, `get_entities()`, `list_entities()` all require a model
  instance.
- `anf()` is the only function that works:
  ```python
  >>> dhmin.anf(40, 0.06)
  0.0664615359206755
  ```

---

## Bugs found

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **Critical** | `core.py:250` | `create_model` crashes with `AttributeError: 'NoneType' object has no attribute 'loc'` because `edge_profile` is `None` by default but unconditionally accessed |
| 2 | **Critical** | `core.py:250` | Even with a provided `edge_profile` (a Series), `.loc[index, :]` fails because Series does not support column slicing with `:` on a MultiIndex |
| 3 | **High** | `rundhshp.py:32` | Shapefile example passes 3-level MultiIndex but `create_model` expects 2-level; crashes at `core.py:85` |
| 4 | **Medium** | `pyproject.toml` | `openpyxl` is not declared as a dependency despite `read_excel()` requiring it |
| 5 | **Medium** | API design | `read_excel()` returns `cost_heat` column but `create_model()` expects `c_heatvar`/`c_heatfix` -- no adapter or documentation |

## UX / documentation issues

| # | Description |
|---|-------------|
| 1 | No installation instructions in README |
| 2 | No quickstart guide or tutorial |
| 3 | `edge_profile` parameter is completely undocumented -- type, structure, and expected values are unclear |
| 4 | `create_model` docstring says `edges` takes "(Vertex1, Vertex2) MultiIndex" but `read_excel` returns 3-level index |
| 5 | Sphinx docs reference Python 2.7 and Pyomo 3/4 (long obsolete) |
| 6 | No test suite; no way to verify correct behavior |
| 7 | The `shp/README.txt` lists a `demand` column that is not used anywhere in the code |
| 8 | Hardcoded coordinates in `plot_flows_min` make it only usable with the minimal example dataset |

## What works

- `pip install -e .` installs cleanly
- `dhmin.read_excel()` correctly reads the Excel file (after manually installing openpyxl)
- `dhmin.anf()` computes annuity factors correctly
- Data files (`mnl.xlsx`, shapefiles) are present and well-structured
- Code is cleanly organized with type hints and docstrings
- The mathematical formulation (constraints, objective) is clearly structured in the source

## Recommendations

1. **Fix the `edge_profile` bug** -- when `edge_profile is None`, construct a
   default from the global `ts_list` scaling factors for all edges
2. **Fix the `.loc[index, :]` bug** -- use `.loc[index]` (no `:` slice) for
   Series access
3. **Fix `rundhshp.py`** -- add `edge.reset_index("Edge", inplace=True)` before
   calling `create_model`
4. **Add `openpyxl`** as a dependency (or under an `[excel]` extra)
5. **Add a test suite** that at minimum runs both example scripts end-to-end
6. **Add a quickstart** to the README showing the minimal path from install to
   solved model
7. **Document `edge_profile`** with expected type, structure, and an example
8. **Harmonize the data pipeline** so `read_excel` output can flow directly into
   `create_model` without manual column renaming
