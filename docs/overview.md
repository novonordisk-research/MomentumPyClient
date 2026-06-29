# MomentumPyClient Overview

_Produced in Step 2. Reviewed by JSQP and a Biophysics group member before use._

## System overview

MomentumPyClient is an in-house Python wrapper (version 0.0.5, MIT licence, hosted at github.com/novonordisk-research/MomentumPyClient) around the REST/Swagger API exposed by the Thermo Scientific Momentum lab automation scheduler. Momentum is a lab automation scheduler used to orchestrate robotic platforms, controlling instruments such as incubators, plate hotels, liquid handlers, and plate readers.

**What it wraps.** The package covers the following Momentum API surface:

- Authentication (`token/accesstoken` — Bearer-token flow).
- Automation-system control: `start`, `stop`, `simulate`.
- Read-only queries: system version, system status, devices, containers, nests, container definitions (templates), processes, work queue, process variables, experiments.
- Inventory management: bulk-add items (`momentum/inventory/bulkitems`), delete items by barcode/template, read per-item attributes.
- Work submission: submitting worklists (one or more batches in one workunit) as XML via `momentum/worklist`; the `run_process` and `run_experiment` helpers build the XML automatically.
- A Streamlit UI layer (`ui.py`) with a colour-coded store visualisation and a process-selector widget.

**What it does NOT cover.**

- The Momentum logs/audit XML files (parsed separately in `momentum_obsolete.py::analyze_workunit_xml` and `pages/09_analyze_logs.py`).
- Retrieving individual workunit XML files from the filesystem (`momentum_obsolete.py::get_active_workunit_plates`).
- Any Momentum API endpoints beyond those described above (e.g., user management, alarm management, resource scheduling queries, if such endpoints exist).
- Direct instrument control or any non-Momentum API.

**Application context.** The package is the primary interface between any Python application and a Momentum-controlled robotic platform. It is the recommended replacement for hand-rolled REST integrations such as the older `integrations/momentum_obsolete.py` pattern.

---

## Module map

### `src/MomentumPyClient/__init__.py`
Re-exports `Momentum` from `ws.py`. The `StreamlitMomentum` import is commented out, so `ui.py` is not exported from the package namespace.

```
from .ws import Momentum
__all__ = ["Momentum"]
```

---

### `src/MomentumPyClient/ws.py` — class `Momentum`

The single core class. All methods are synchronous except the `async_*` and `fetch_all_attributes` helpers (which are only called from within `get_containers_with_attributes`, itself synchronous).

| Method | Responsibility | Key dependencies |
|--------|---------------|-----------------|
| `__init__(url, user_name, password, verify, timeout)` | Reads credentials from arguments or `.env` file via `python-dotenv`. Disables urllib3 SSL warnings when `verify=False`. | `dotenv_values`, `disable_warnings` |
| `_send_get_request(url)` | GET with one automatic token-refresh retry on HTTP 401. | `requests` |
| `_send_post_request(url, data)` | POST; uses different headers depending on whether data is `dict` (no Content-Type), `list` (text/plain), or raw bytes/string (text/plain). Returns `None` on HTTP 202. | `requests` |
| `_send_delete_request(url)` | DELETE; returns `None` on HTTP 204, dict on HTTP 200. | `requests` |
| `_get_token()` | POSTs credentials to `token/accesstoken`. Raises a human-readable `HTTPError` on "Invalid username or password". | `requests` |
| `stop()` | POST `momentum/automationsystem/stop`. | — |
| `start()` | POST `momentum/automationsystem/start?Mode=Normal`. | — |
| `simulate()` | POST `momentum/automationsystem/start?Mode=Simulate`. | — |
| `get_version()` | GET `momentum/version`. | — |
| `get_status()` | GET `momentum/automationsystem`. | — |
| `get_devices()` | GET `momentum/devices`. | — |
| `get_containers()` | GET `momentum/containers`. | — |
| `add_inventyory_items(items)` | POST list of dicts to `momentum/inventory/bulkitems`. (Note: method name is a typo — "inventory" is misspelled.) | — |
| `delete_inventory_item(barcode, template)` | DELETE `momentum/inventory/items?template=...&barcode=...`. | — |
| `get_item_attribute(itemId)` | GET attributes for one inventory item by its numeric ID. | — |
| `async_get_item_attribute(itemId)` | Wraps `get_item_attribute` in `asyncio.to_thread`. | `asyncio` |
| `get_container_attributes(container)` | Async: fetches attributes for one container dict and adds them as `container["Attributes"]`. Gracefully skips containers with no `Inventory`. | `asyncio` |
| `fetch_all_attributes(containers)` | Async: gathers attribute fetches for all containers concurrently. | `asyncio` |
| `get_containers_with_attributes(filter, flatten)` | Sync wrapper: calls `get_containers`, optionally name-filters, runs `fetch_all_attributes` via `asyncio.run`, optionally flattens attributes into top-level keys. | `asyncio` |
| `get_experiments()` | GET `momentum/experiments`. | — |
| `get_container_definitions()` | GET `momentum/containers/definition`. | — |
| `get_nests()` | GET `momentum/nests`. | — |
| `get_processes()` | GET `momentum/processes`. | — |
| `get_workqueue()` | GET `momentum/workqueue/workunits?batches=true`. | — |
| `get_process_variables(process_name, process_id)` | GET process variables. Contains a URL-construction bug when `process_id > 0` (see Bugs section). | — |
| `create_worklist_xml(worklist)` | Converts a Python dict describing a multi-batch worklist into the Momentum XML format. Returns bytes. | `xml.etree.ElementTree` |
| `run_worklist(worklist, verbose)` | Calls `create_worklist_xml` then POSTs to `momentum/worklist`. | — |
| `run_process(process, variables, batch_name, append, iterations, minimum_delay, workunit_name)` | Builds a single-batch worklist XML and POSTs it. If `append=True`, looks up the running/waiting workunit by name and appends to it. Accepts `variables` as a dict (recommended) or a list of dicts. | `xml.etree.ElementTree`, `datetime` |
| `run_experiment(experiment, variables, workunit_name, batch_name)` | Like `run_process` but uses a `batch[@experiment]` node instead of `batch[@process]`. Hardcodes `iterations="15"`. | `xml.etree.ElementTree`, `datetime` |
| `get_template_names()` | Returns a sorted deduplicated list of `InventoryTemplateName` strings from `get_container_definitions()`. | — |
| `get_process_names()` | Returns list of process name strings from `get_processes()`. | — |
| `get_instrument_names()` | Returns list of device names where `IsInstrument == True`. | — |
| `get_instrument_nests(instrument)` | Returns a dict of `stack_name -> [nest_names]` for a given instrument. Handles two-part and three-part nest names; partially handles bucket-style nests. | `re` |
| `get_barcodes(template_name, instrument)` | Filters `get_containers()` by template name and location substring. Returns list of `{Barcode, Location}` dicts. Crashes if any container lacks an `Inventory` key. | — |
| `list_available_nests(location)` | Returns list of nest names matching `location` substring where `Content` is `None`. | — |
| `reformat_container_nests(nests)` | Converts raw nest JSON from `get_nests()` into a flat list of slot dicts with `Name`, `Stack`, `StackName`, `Nest`, `Barcode`, `Template`, `IsStack`. Skips Waste, Shovel, Transfer nests. | — |

---

### `src/MomentumPyClient/ui.py` — class `StreamlitMomentum` and module-level convenience aliases

**Note:** This module is commented out of `__init__.py` and must be imported as `import MomentumPyClient.ui as stm`. It has a critical defect: lines 279–287 execute `_stm = StreamlitMomentum()` at **import time**, which immediately calls `get_container_definitions()` against the live API. Any import of this module in a context without a reachable Momentum server will raise an exception.

| Symbol | Type | Responsibility |
|--------|------|---------------|
| `StreamlitMomentum` | Class | Wraps `Momentum`; owns colour assignment and UI rendering. |
| `StreamlitMomentum.__init__` | Method | Creates a `Momentum` instance, assigns colours to all container templates by cycling through a fixed colour list. |
| `StreamlitMomentum.set_color_names(value)` | Method | Replaces the colour cycle with a new list; re-initialises colour assignments. Calls `get_container_definitions()`. |
| `StreamlitMomentum.set_template_colors(color_dict)` | Method | Overrides the colour dict directly, bypassing the cycle. |
| `StreamlitMomentum.get_container_color(container_name)` | Method | Returns a colour for a template, assigning one from the cycle if not yet seen. |
| `StreamlitMomentum.show_process_selector()` | Method | Renders an `st.expander` with a process dropdown, editable variable table, and a run button. |
| `StreamlitMomentum.cached_get_nests(_self)` | Method (cached) | `st.cache_data(ttl=10)` wrapper around `ws.get_nests()`. |
| `StreamlitMomentum.show_store(storename, numbering_from_bottom)` | Method | Renders a Plotly stacked-bar chart of one store's slots, coloured by template. Returns a list of selected slot dicts from Streamlit point-selection events. |
| `stm.ws` / `stm.api` | `Momentum` | The module-level `Momentum` instance. |
| `stm.show_store` | Function alias | Module-level alias for `_stm.show_store`. |
| `stm.show_process_selector` | Function alias | Module-level alias for `_stm.show_process_selector`. |
| `stm.template_colors` | Dict alias | Module-level alias for `_stm.color_dict`. |
| `stm.set_template_colors` | Function alias | Module-level alias for `_stm.set_template_colors`. |
| `stm.set_color_names` | Function alias | Module-level alias for `_stm.set_color_names`. |
| `get_nests()` | Cached function | `st.cache_data(ttl=60)` — **contains a bug**: calls `_stm.ws.get_nests(_stm)` with a spurious argument; `get_nests` takes no arguments. |
| `get_template_names()` | Cached function | `st.cache_data(ttl=60)` wrapper. |
| `get_instrument_nests(instrument)` | Cached function | `st.cache_data(ttl=60)` wrapper. |
| `get_container_definitions()` | Cached function | `st.cache_data(ttl=60)` wrapper. |
| `run_process(...)` | Function | Thin pass-through to `_stm.ws.run_process(...)`. |

---

## Design decision register

| Decision | Problem it solves | Worth carrying forward? |
|----------|------------------|------------------------|
| Bearer-token with one auto-retry on 401 (`_send_get_request`) | Momentum tokens expire; callers should not need to handle token refresh manually. | Yes — this is the right pattern. |
| Async fan-out for attribute fetching (`fetch_all_attributes`) | Fetching attributes one-by-one for a large inventory is very slow (one HTTP round-trip per plate). Async `to_thread` allows concurrent requests without restructuring the synchronous API. | Yes — but note `asyncio.run` nested inside a synchronous method means the caller cannot use this from an already-running event loop (e.g., from `asyncio.run` again). Relevant if future integrations use async frameworks. |
| `.env` file fallback for credentials | Keeps secrets out of source code; allows deployment without code changes. | Yes. |
| XML worklist construction via `xml.etree.ElementTree` | Momentum's work-submission endpoint accepts only an XML text body; the Python API presents a dict/parameter interface. | Yes — preferable to string concatenation. |
| `run_process(append=True)` auto-detects running workunit | Callers should not need to know the workunit name to append work to it; the method looks it up. | Yes — this is valued by consumers. |
| Module-level singleton in `ui.py` (`_stm = StreamlitMomentum()`) | Convenience — one import gives access to `stm.ws`, `stm.show_store`, etc. | Questionable. The side-effect at import time (live API call) makes the module non-importable when the API is unreachable, and hinders testing. A lazy-initialisation pattern would be safer. |
| `st.cache_data` wrappers in `StreamlitMomentum` | Streamlit re-runs scripts on every user interaction; caching prevents redundant API calls. | Yes, though TTL values (10s for nests, 60s for definitions) are reasonable defaults but not configurable by callers. |
| Separate `ui.py` module with optional `streamlit`/`plotly`/`pandas` dependencies | Users who only need the API client do not need to install Streamlit. | Yes — the optional dependency group `[streamlit]` in `pyproject.toml` enforces this correctly. |

---

## Coverage table

Pages that do not import or call MomentumPyClient at all: `09_analyze_logs.py`, `10_Gantt2.py`, `14_Barcodes.py`, `15_EchoFiles.py`, `16_OrangeG.py`, `17_DLSPreset.py`, `18_statistics.py`, `22_liconics.py`, `24_statistics_old.py`. These are excluded from the table.

| Call site | File / Line | What it does | Coverage |
|-----------|-------------|-------------|----------|
| `Momentum()` construction | `01_Live_status.py:9` | Instantiates client from `.env`. | Well covered. |
| `momentum.get_workqueue()` | `01_Live_status.py:13` | Retrieves active work units. | Well covered. |
| `momentum.get_devices()` | `01_Live_status.py:16` | Lists all devices and their states. | Well covered. |
| `momentum.get_nests()` | `01_Live_status.py:40, 58` | Lists all nests and their contents. | Well covered. |
| `import MomentumPyClient.ui as stm` | `02_inventory.py:2` | Uses module-level singleton. | Works, but fragile (see Design decisions). |
| `stm.show_store("Carousel")` etc. | `02_inventory.py:8–18` | Renders inventory visualisation for four stores. | Well covered. |
| `stm.ws.get_containers()` | `02_inventory.py:21` | Lists all containers with location info. | Well covered. |
| `stm.ws.delete_inventory_item(barcode, template)` | `02_inventory.py:58` | Removes a plate from the system. | Well covered. |
| `Momentum()` construction | `03_orders.py:160` | Instantiates client. | Well covered. |
| `momentum.get_containers()` | `03_orders.py:244` | Used to check which barcodes are already on system. | Well covered. |
| `momentum.get_template_names()` | `03_orders.py:272` | Populates plate-type dropdown. | Well covered. |
| `momentum.list_available_nests(location)` | `03_orders.py:307` | Finds empty nest positions for loading a plate. | Well covered. |
| `momentum.add_inventyory_items(items)` | `03_orders.py:343` | Adds missing plate to inventory. | Well covered (note typo in method name). |
| `momentum.run_process(process, variables, batch_name, append)` | `03_orders.py:449, 481, 487` | Queues assay processes with Echo/Fluent file paths and barcodes. | Well covered. |
| `Momentum()` construction | `04_startwork.py:50` | Instantiates client. | Well covered. |
| `momentum.get_containers()` | `04_startwork.py:52` | Lists containers. | Well covered. |
| `momentum.get_nests()` | `04_startwork.py:53` | Lists nests. | Well covered. |
| `momentum.get_processes()` | `04_startwork.py:54` | Lists processes. | Well covered. |
| `momentum.run_process(process, variables)` | `04_startwork.py:123, 127` | Starts a process, with or without append. | Well covered. |
| `Momentum()` construction | `05_Fluent.py:13` | Instantiates client. | Well covered. |
| `momentum.run_process("SetFluentDeckSetup", ...)` | `05_Fluent.py:60` | Triggers a Momentum process to push deck config. | Well covered. |
| `momentum.run_process("GetFluentDeckSetup", ...)` | `05_Fluent.py:66` | Triggers a Momentum process to pull deck config. | Well covered. |
| `Momentum()` construction | `06_CompleteTestRun.py:8` | Instantiates client. | Well covered. |
| `stm.ws.get_containers_with_attributes(filter)` | `06_CompleteTestRun.py:30, 43` | Retrieves containers with per-plate attributes. | Well covered. |
| `momentum.get_item_attribute(itemId)` | `06_CompleteTestRun.py:51` | Re-fetches attributes individually (redundant given line 43). | Well covered but redundant. |
| `momentum.run_process("CompleteTestRun", ...)` | `06_CompleteTestRun.py:85` | Starts complete test run process. | Well covered. |
| `stm.ws.get_containers_with_attributes(filter="DLS_Stability")` | `12_DLS_stability.py:29` | Retrieves DLS stability plates with attributes. | Well covered. |
| `stm.run_process("DLS Stability New", ...)` | `12_DLS_stability.py:99` | Starts a DLS read cycle. | Well covered. |
| `stm.run_process("DLS Set Plate Attributes", ...)` | `12_DLS_stability.py:132` | Updates incubation parameters on a plate. | Well covered. |
| `stm.ws.get_containers_with_attributes(filter="pH_screen_DLS")` | `13_pH_screen_restart.py:28` | Retrieves pH screen DLS plates with attributes. | Well covered. |
| `stm.run_process("pH Screen Continue Workflow", ...)` | `13_pH_screen_restart.py:85` | Continues a pH screen run. | Well covered. |
| `stm.run_process("DLS Set Plate Attributes", ...)` | `13_pH_screen_restart.py:113` | Updates plate attributes. | Well covered. |
| `stm.ws.get_template_names()` | `19_ScanBarcodes.py:10` | Populates template dropdown. | Well covered. |
| `stm.show_store(instrument)` | `19_ScanBarcodes.py:16` | Renders store visualisation. | Well covered. |
| `stm.get_instrument_nests(instrument)` | `19_ScanBarcodes.py:23` | Gets nest layout for stack/column selection. | Well covered. |
| `scan_barcodes(instrument, template, nests, lidded)` via `Momentum().run_process("ScanBarcodes2", ...)` | `utils/scan_barcodes.py:12`, called from `19_ScanBarcodes.py:32` and `03_orders.py:366` | Runs a barcode scanning process. | Well covered. |
| `Momentum()` construction | `20_ABS_RestoreReset.py:8` | Instantiates client. | Well covered. |
| `momentum.get_containers()` + `get_item_attribute(itemId)` | `20_ABS_RestoreReset.py:17–23` | Loads all containers and attributes for filtering. | Covered; but fetching attributes synchronously per container in a loop is slow — `get_containers_with_attributes` exists for this. Partial gap: the page doesn't use the faster async method. |
| `momentum.run_process(...)` (×2) | `20_ABS_RestoreReset.py:96, 103` | Starts restore/reset processes for ABS plates. | Well covered. |
| `Momentum()` construction | `21_ACSINS_RestoreReset.py:8` | Instantiates client. | Well covered. |
| `momentum.get_containers()` + `get_item_attribute(itemId)` | `21_ACSINS_RestoreReset.py:17–23` | Same slow per-container attribute fetch. | Same partial gap as page 20. |
| `momentum.run_process(...)` (×2) | `21_ACSINS_RestoreReset.py:93, 100` | Starts restore/reset processes for AC-SINS plates. | Well covered. |
| `Momentum()` construction | `23_pHAdjustment.py:7` | Instantiates client. | Well covered. |
| (no further Momentum calls in page 23 — `runExperiment` call is commented out) | `23_pHAdjustment.py:22–23` | — | N/A. |
| `Momentum()` construction | `25_test.py:8` | Instantiates client. | Well covered. |
| `stm.ws.get_containers_with_attributes()` | `25_test.py:22, 36` | Retrieves containers with attributes. | Well covered (called with empty filter — retrieves all containers). |
| `momentum.get_item_attribute(itemId)` | `25_test.py:44` | Again redundant re-fetch after `get_containers_with_attributes`. | Well covered but redundant pattern. |
| `momentum.run_process("EchoTest", ...)` | `25_test.py:77` | Starts Echo test process. | Well covered. |

**Capabilities in `momentum_obsolete.py` not covered by MomentumPyClient:**

| Capability | Location in obsolete file | Covered by MomentumPyClient? |
|------------|--------------------------|------------------------------|
| Parse workunit audit XML log from filesystem | `analyze_workunit_xml()` lines 315–381 | No — this reads local files, not the API. Not needed for API client. |
| Find active workunit plates by cross-referencing workunit folders | `get_active_workunit_plates()` lines 383–420 | No — same filesystem-based approach. |
| `addWork()` — low-level experiment-batch submission | `addWork()` lines 193–217 | Superseded by `run_experiment()` in MomentumPyClient. |
| `@st.cache_resource` class-level caching | Decorator on class at line 15–16 | Not used in MomentumPyClient; caching is at method level in `ui.py`. |

---

## Quality assessment

**Test coverage.** There are no tests at all. The `pyproject.toml` lists `pytest > 8.3.3` as a dev dependency but the repository contains zero test files. Every change to the package must be manually validated against a live Momentum instance.

**Documentation quality.** The class docstring in `ws.py` is accurate but only a method-listing stub. Individual method docstrings exist for most methods but do not document return-value shapes (i.e., which keys are present in the dicts returned by `get_containers()`, `get_nests()`, etc.). The README is minimal. No type annotations on return values beyond `-> list`, `-> dict`, `-> str`.

**Known issues.**
- `add_inventyory_items` has a persistent typo in the method name (double-`y`). Both `ws.py` and `momentum_obsolete.py` carry this typo, and call sites in the Streamlit app (`03_orders.py:343`) call the misspelled name, so renaming it would be a breaking change.
- `get_process_variables` has a URL-construction bug when `process_id > 0`: the local variable `url` is assigned on line 409 but then unconditionally reassigned on line 415, discarding the earlier assignment. The `process_id > 0` branch is therefore dead code.
- `run_experiment` hardcodes `iterations="15"` on line 630 regardless of the caller's intent.
- `ui.py::get_nests()` (module-level cached function, line 292) passes `_stm` as a positional argument to `get_nests()`, which accepts no arguments. This will raise `TypeError` at runtime. However, the app pages use `stm.ws.get_nests()` or `stm.cached_get_nests()` directly, so this broken function is apparently never called.
- Module-level execution in `ui.py` (lines 279–287) calls the Momentum API at import time, making the module non-importable in environments without API access.

**Maintenance status.** The repository has ~20 commits since inception; recent commits (PR #13, #14) addressed caching and colour-scale issues, suggesting active maintenance at the time of writing. Version remains `0.0.5` (Development Status :: 3 - Alpha).

**Dependency risks.** The package pins no version bounds on `requests` or `python-dotenv`; only a lower Python bound (`>=3.10`) is set. The `streamlit` extras have no version caps, which could cause breakage if Streamlit's API changes. SSL verification is disabled by default (`verify=False`), which is a risk on any network where MITM is possible.

---

## Recommendation

**Use MomentumPyClient as-is for the majority of Momentum integration work, with targeted extensions.**

The package covers all actively-used Momentum API interactions correctly. The main areas requiring attention before depending on it in a production application:

1. **Fix the `get_process_variables` URL bug** (trivial — remove dead branch or restructure condition). This method is not currently called in the app but will be needed for dynamic variable inspection.
2. **Fix `ui.py::get_nests()` spurious argument** (trivial).
3. **Eliminate module-level API call in `ui.py`** by switching to lazy initialisation (moderate effort — restructure `_stm` and aliases). This is important for testability.
4. **Add at minimum smoke-test stubs with mocked `requests`** so the package can be validated without a live Momentum instance.
5. **Document return-value schemas** for the main query methods (`get_containers`, `get_nests`, `get_devices`), as downstream code makes many assumptions about key names.
6. **Do not replace** with `momentum_obsolete.py`; the obsolete file has no token-refresh logic, silent error swallowing, and `st.write` calls embedded in business logic. MomentumPyClient is clearly the right direction.
