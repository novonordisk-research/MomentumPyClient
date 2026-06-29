# MomentumPyClient Usage Reference

_Produced in Step 2. Reviewed and corrected by JSQP before use as AI context._
_Describes the MomentumPyClient package version 0.0.5._

---

## What MomentumPyClient does

MomentumPyClient provides a Python interface to the Thermo Scientific Momentum lab automation scheduler REST API. It handles authentication (Bearer token with automatic refresh), wraps the main read/write API endpoints, builds the XML worklist format that Momentum's work-submission endpoint requires, and optionally provides a Streamlit UI layer for inventory visualisation.

It is used to: query system state (status, devices, nests, containers, processes); add and remove inventory items; start processes and experiments; and display interactive hotel/carousel views in Streamlit apps.

---

## Public API

### Installation

```sh
pip install MomentumPyClient           # API client only
pip install MomentumPyClient[streamlit] # API client + Streamlit UI
```

Requires Python >= 3.10.

---

### Credentials and configuration

Credentials are read either from constructor arguments or from a `.env` file in the working directory:

```env
momentum_user=myuser
momentum_passwd=mypassword
momentum_verify=False
momentum_url=https://lpdkhqgm150ntv/api/
```

`momentum_verify` can be `True`, `False`, or a path to a CA bundle.

When `verify=False`, urllib3 `InsecureRequestWarning` is suppressed automatically.

---

### Class `Momentum` (`from MomentumPyClient import Momentum`)

#### `__init__(url, user_name, password, verify, timeout)`

```python
m = Momentum()                          # reads all values from .env
m = Momentum(url="https://host/api/",
             user_name="user",
             password="pass",
             verify=False,
             timeout=5)
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `url` | `str \| None` | from `.env` `momentum_url` | Must end with `/api/`. |
| `user_name` | `str \| None` | from `.env` `momentum_user` | |
| `password` | `str \| None` | from `.env` `momentum_passwd` | |
| `verify` | `str \| bool \| None` | `False` (or from `.env`) | `False` disables SSL verification. Can be a path to a CA bundle. |
| `timeout` | `int` | `5` | HTTP request timeout in seconds. |

Raises `Exception` if username, password, or URL is missing. Does **not** fetch a token at construction time — the first API call triggers token acquisition.

---

#### System control

```python
m.stop()      # POST momentum/automationsystem/stop
m.start()     # POST momentum/automationsystem/start?Mode=Normal
m.simulate()  # POST momentum/automationsystem/start?Mode=Simulate
```

All return the JSON response body or `None` (HTTP 202).

---

#### Read-only queries

```python
version  = m.get_version()    # dict  e.g. {"Version": "7.14.0"}
status   = m.get_status()     # dict  e.g. {"State": "Running", "Attended": False, "Simulated": False}
devices  = m.get_devices()    # list of dicts; each has "Name", "State", "IsInstrument", "Mode", "OnlineState", etc.
nests    = m.get_nests()      # list of dicts; each has "Name", "DeviceName", "Content", "IsStack", "StackContents"
containers = m.get_containers()        # list of dicts; each has "Name", "Barcode", "Location", "State", "Inventory"
definitions = m.get_container_definitions()  # list of dicts; each has "Name", "InventoryTemplateName"
processes = m.get_processes()          # list of dicts; each has "Id", "Name"
experiments = m.get_experiments()      # list of dicts
workqueue = m.get_workqueue()          # list of workunit dicts; each has "Name", "State", "Batches"
```

---

#### `get_template_names() -> list[str]`

Returns a sorted list of unique `InventoryTemplateName` values from `get_container_definitions()`. Filters out empty names.

```python
templates = m.get_template_names()
# e.g. ["T_AC_SINS_Source", "T_DLS_Stability", "T_Displacement_Assay", ...]
```

---

#### `get_process_names() -> list[str]`

Returns a list of process name strings from `get_processes()`.

```python
names = m.get_process_names()
# e.g. ["AC_SINS_EPR Echo Start", "DLS Stability New", ...]
```

---

#### `get_instrument_names() -> list[str]`

Returns names of devices where `IsInstrument == True`.

```python
instruments = m.get_instrument_names()
# e.g. ["Carousel", "Liconic_1", "Liconic_2", "Liconic_3"]
```

---

#### `get_instrument_nests(instrument: str) -> dict`

Returns a dict mapping stack/column names to lists of nest names for a given instrument.

```python
stacks = m.get_instrument_nests("Liconic_1")
# e.g. {"Stack 1": ["Nest 1", "Nest 2", ...], "Stack 2": [...]}
```

Nest names in the returned lists are the final segment of the full colon-separated name (e.g. `"Nest 5"`). Only handles nests whose names match `DeviceName:StackName:Nest N` or `DeviceName:NestName` patterns. Stack-type nests (`Stack1`) and bucket-type nests are not fully handled; see Gotchas.

---

#### `get_process_variables(process_name: str = "", process_id: int = 0) -> list`

Returns the variable definitions for a process. Each entry is a dict with at minimum `"Name"`, `"NativeType"`, `"DefaultValue"`, `"Comments"`.

```python
variables = m.get_process_variables(process_name="DLS Stability New")
```

**Warning:** There is a bug when passing `process_id > 0` — the URL constructed for that branch is discarded and overwritten. Always use `process_name`. See Bugs section.

---

#### `get_barcodes(template_name: str, instrument: str = "") -> list`

Returns `[{"Barcode": ..., "Location": ...}]` for containers matching the template name and (optionally) instrument substring.

```python
plates = m.get_barcodes("T_DLS_Stability", instrument="Liconic_1")
```

**Warning:** Will raise `TypeError` if any container in `get_containers()` has `Inventory == None`. This can happen for containers currently being transported.

---

#### `list_available_nests(location: str) -> list[str]`

Returns full nest name strings for nests whose name contains `location` and whose `Content` is `None`.

```python
empty = m.list_available_nests("Carousel:Column1_Hotel")
# e.g. ["Carousel:Column1_Hotel:Nest 3", "Carousel:Column1_Hotel:Nest 4"]
```

---

#### `reformat_container_nests(nests: Iterable[dict]) -> list[dict]`

Converts the raw `get_nests()` output into a flat list of slot records. Each record has:

```python
{
    "Name":      str,   # device name (e.g. "Carousel", "Liconic_1")
    "Stack":     int,   # column/stack number
    "StackName": str,   # column/stack label
    "Nest":      int,   # nest position
    "Barcode":   str,   # barcode, or "" if empty
    "Template":  str,   # template name, or "" if empty
    "IsStack":   bool,
}
```

Skips nests containing "Waste", "Shovel", or "Transfer" in their name.

```python
slots = m.reformat_container_nests(m.get_nests())
df = pd.DataFrame(slots)
```

---

#### Inventory item attributes

```python
attributes = m.get_item_attribute(itemId=1234)
# Returns list of dicts: [{"Name": "StartDate", "Value": "01/15/2025", "Updated": "..."}, ...]
```

`itemId` is the integer `Inventory.ItemId` field from a container record.

---

#### `get_containers_with_attributes(filter: str = "", flatten: bool = False) -> list`

Fetches all containers and their per-item attributes concurrently (async fan-out). This is significantly faster than calling `get_item_attribute` in a loop.

```python
# All containers, attributes in "Attributes" list per container
containers = m.get_containers_with_attributes()

# Only containers whose Name contains "DLS_Stability"
containers = m.get_containers_with_attributes(filter="DLS_Stability")

# Flatten: each attribute becomes a top-level key
containers = m.get_containers_with_attributes(filter="DLS_Stability", flatten=True)
# container["StartDate"] == "01/15/2025" instead of container["Attributes"][...]["Value"]
```

Containers with `Inventory == None` get an empty `Attributes` list (no crash, unlike `get_barcodes`).

**Important:** The `filter` argument is a substring match on `container["Name"]` (the container type name, e.g. `"T_DLS_Stability"`), not on the barcode or location.

---

#### Inventory management

##### `add_inventyory_items(items: list[dict]) -> list`

**Note: the method name has a typo (double "y") — this is the real name and must be spelled this way.**

Adds one or more inventory items to Momentum. Each item dict must have:

```python
items = [
    {
        "Template": "T_DLS_Stability",      # required: template name
        "Nest": "Liconic_1:Stack 1:Nest 3", # required: full nest name
        "HasLid": False,                     # required
        "Barcode": "NN00012345",             # required
        # Optional additional fields:
        "StartDate": "01/15/2025",
        "IncubationTime": "0.4:30:0",        # days.hours:minutes:seconds
        "IncubationTemperature": 25.0,
        "CentrifugationSpeed": 2000,
        "TotalDaysOfExperiment": 7,
    }
]
result = m.add_inventyory_items(items)
```

Returns a list. Will raise an exception if the nest is already occupied (HTTP 400).

##### `delete_inventory_item(barcode: str = "", template: str = "*")`

Deletes an item by barcode and/or template. Passing `template="*"` without a barcode deletes all items of all templates — use with caution.

```python
m.delete_inventory_item(barcode="NN00012345", template="T_DLS_Stability")
m.delete_inventory_item(barcode="NN00012345")  # template defaults to "*"
```

---

#### Work submission

##### `run_process(process, variables, batch_name, append, iterations, minimum_delay, workunit_name)`

Queues a Momentum process. This is the most commonly used method.

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `process` | `str` | required | Exact process name in Momentum. |
| `variables` | `dict \| list` | `{}` | See below. |
| `batch_name` | `str` | `"batch"` | Label for this batch within the workunit. Use the order/step ID for traceability. |
| `append` | `bool` | `True` | If `True`, appends to the currently Running or Waiting workunit. If `False`, always creates a new workunit. |
| `iterations` | `int` | `1` | Number of iterations (repeats) for this batch. |
| `minimum_delay` | `int` | `0` | Minimum delay in seconds between iterations. |
| `workunit_name` | `str \| None` | auto | If `None`, generates `"Work Unit N"` where N is days since 2020-01-01. If appending, the running workunit's name overrides this. |

**Variables as a dict (recommended):**

```python
# Scalar values
m.run_process("DLS Stability New", variables={"assayBarcode": "NN00012345"})

# Per-iteration values using a list
m.run_process(
    "MyProcess",
    variables={"SourceBarcode": ["NN001", "NN002", "NN003"]},
    iterations=3,
)

# Per-iteration values using a semicolon-separated string (equivalent)
m.run_process(
    "MyProcess",
    variables={"SourceBarcode": "NN001;NN002;NN003"},
    iterations=3,
)
```

**Variables as a list of dicts (less common, used by `run_worklist`):**

Each dict must have `"Name"` and either `"Value"` (scalar) or `"Values"` (list).

```python
m.run_process(
    "MyProcess",
    variables=[
        {"Name": "assayBarcode", "Value": "NN001"},
        {"Name": "SourceBC", "Values": ["NN002", "NN003"]},
    ],
)
```

Returns the JSON response from Momentum, or `None` if the API returns HTTP 202.

---

##### `run_experiment(experiment, variables, workunit_name, batch_name)`

Like `run_process` but submits an experiment (uses `batch[@experiment]` in the XML).

**Warning:** `iterations` is hardcoded to `"15"` regardless of inputs. Do not use this method if you need a specific iteration count.

```python
m.run_experiment(
    experiment="E_ReadersTest",
    variables={"NumberOfLoops": "1"},
    batch_name="TestRun",
)
```

---

##### `run_worklist(worklist: dict, verbose: bool = False)`

Submits a full multi-batch worklist. Prefer `run_process` for single-batch use. The dict format is:

```python
worklist = {
    "Name": "Work Unit 1",
    "auto_load": True,    # optional, default True
    "auto_verify": True,  # optional, default True
    "auto_unload": True,  # optional, default True
    "append": False,      # optional, default False
    "Batches": [
        {
            "Process": "DLS Stability New",
            "Name": "Batch A",
            "Iterations": 1,
            "MinimumDelay": 0,
            "Variables": [
                {"Name": "assayBarcode", "Value": "NN001"},
                # Per-iteration: use "Values" key with a list
                {"Name": "sourceBC", "Values": ["NN002", "NN003"]},
                # Per-iteration with explicit iteration numbers:
                {"Name": "integer1", "Values": [{"Iteration": 2, "Value": 5}, {"Iteration": 3, "Value": 6}]},
            ],
        },
        {
            "Process": "AnotherProcess",
            "Name": "Batch B",
            "Iterations": 2,
            "MinimumDelay": 30,
            "Variables": [],
        },
    ],
}
m.run_worklist(worklist, verbose=True)  # verbose=True prints the XML
```

---

### Module `MomentumPyClient.ui` (Streamlit integration)

Import as:

```python
import MomentumPyClient.ui as stm
```

**Warning:** Importing this module calls `get_container_definitions()` on a live Momentum instance immediately. Do not import this module in a context where the Momentum server is unreachable.

#### Module-level aliases

| Name | Type | Description |
|------|------|-------------|
| `stm.ws` | `Momentum` | The shared `Momentum` instance. Use for any API call. |
| `stm.api` | `Momentum` | Alias for `stm.ws`. |
| `stm.show_store` | Function | See below. |
| `stm.show_process_selector` | Function | See below. |
| `stm.template_colors` | `dict` | Maps template name → colour string. |
| `stm.set_template_colors(d)` | Function | Overrides the colour map with `d`. |
| `stm.set_color_names(lst)` | Function | Resets the colour cycle to `lst` and reassigns template colours. |

#### Module-level cached functions

| Function | TTL | Description |
|----------|-----|-------------|
| `stm.get_template_names()` | 60 s | Cached `ws.get_template_names()`. |
| `stm.get_instrument_nests(instrument)` | 60 s | Cached `ws.get_instrument_nests(instrument)`. |
| `stm.get_container_definitions()` | 60 s | Cached `ws.get_container_definitions()`. |
| `stm.run_process(...)` | — | Pass-through to `ws.run_process(...)`, same parameters. |

**Note:** The module-level `stm.get_nests()` function is broken (passes a spurious argument to `ws.get_nests`). Use `stm.ws.get_nests()` or `stm.cached_get_nests()` (method on `StreamlitMomentum`) instead.

---

#### `stm.show_store(storename, numbering_from_bottom=None) -> list`

Renders a Plotly stacked-bar chart of one storage device (hotel/carousel/incubator) inside a Streamlit page. Fetches nests via the `cached_get_nests` method (TTL 10 s).

```python
selected = stm.show_store("Carousel")
selected = stm.show_store("Liconic_1")   # auto-detects bottom-up numbering
```

Returns a list of selected slot dicts. Each dict contains `stack`, `position`, `barcode`, `template`, `curve_number`. Returns an empty list if nothing is selected or the store is not found.

`numbering_from_bottom` defaults to `True` for stores with "Liconic" in their name and `False` otherwise.

---

#### `stm.show_process_selector()`

Renders a collapsible widget with a process selector, editable variable table, and a "Run process" button. Variables are pre-populated from `get_process_variables()` and can be edited before submission.

---

## Usage patterns

### Pattern 1: Basic status check

```python
from MomentumPyClient import Momentum

m = Momentum()
status = m.get_status()
print(status["State"])  # "Running", "Stopped", "Simulated", etc.
```

### Pattern 2: Start a process with file-path variables

```python
m.run_process(
    process="AC_SINS_EPR Echo Start",
    variables={
        "EchoCSV": "\\\\server\\share\\ST12345.csv",
        "EchoEpr": "\\\\server\\share\\AC-SINS_SAT.epr",
        "FluentGwl": "\\\\server\\share\\ST12345.gwl",
    },
    batch_name="ST12345",
    append=True,
)
```

### Pattern 3: Start a process with per-iteration plate barcodes

```python
m.run_process(
    process="Displacement_RestoreReset_assay",
    variables={},       # no variables needed
    batch_name="Displacement_RestoreReset_assay",
    append=True,
    iterations=3,       # runs 3 iterations
)
```

### Pattern 4: Load a plate into inventory

```python
nests = m.list_available_nests("Liconic_3:Stack 1")
m.add_inventyory_items([{
    "Template": "T_DLS_Stability",
    "Nest": nests[0],
    "HasLid": False,
    "Barcode": "NN00099999",
    "StartDate": "06/08/2025",
    "IncubationTime": "7.0:0:0",       # 7 days
    "IncubationTemperature": 5.0,
}])
```

### Pattern 5: Retrieve containers with attributes efficiently

```python
# Slow (loop over containers calling get_item_attribute individually) — avoid
containers = m.get_containers()
for c in containers:
    attrs = m.get_item_attribute(c["Inventory"]["ItemId"])  # one HTTP call per plate

# Fast (async fan-out, all attributes in one logical call) — prefer
containers = m.get_containers_with_attributes(filter="DLS_Stability", flatten=True)
for c in containers:
    print(c["Barcode"], c.get("StartDate"), c.get("ReadNo"))
```

### Pattern 6: Streamlit store visualisation

```python
import MomentumPyClient.ui as stm

st.header("Inventory")
stm.show_store("Carousel")
for col, store in zip(st.columns(3), ["Liconic_1", "Liconic_2", "Liconic_3"]):
    with col:
        stm.show_store(store)
```

### Pattern 7: Streamlit process selector

```python
import MomentumPyClient.ui as stm

stm.show_process_selector()  # renders full variable-editing UI
```

### Pattern 8: Delete a plate from inventory

```python
m.delete_inventory_item(barcode="NN00012345", template="T_DLS_Stability")
```

### Pattern 9: Multi-batch worklist

```python
m.run_worklist({
    "Name": "Work Unit 1897",
    "Batches": [
        {
            "Process": "Displacement Start",
            "Name": "ST42750",
            "Iterations": 1,
            "MinimumDelay": 0,
            "Variables": [
                {"Name": "EchoCSV",   "Value": "//server/share/ST42750.csv"},
                {"Name": "FluentGwl", "Value": "//server/share/ST42750.gwl"},
            ],
        },
    ],
})
```

---

## What MomentumPyClient does not handle

- Reading or parsing Momentum's local log or audit XML files from the filesystem.
- Querying workunit history from filesystem folders (the `analyze_workunit_xml` / `get_active_workunit_plates` logic in `momentum_obsolete.py`).
- Any Momentum API endpoint not listed in the Public API section (user management, alarm management, etc., if they exist).
- Instrument-specific protocols or commands beyond what Momentum exposes through the scheduler API.
- Re-authentication if the token expires mid-request on a POST (only GET retries on 401).

---

## Gotchas and non-obvious behaviour

1. **`add_inventyory_items` is misspelled.** The method name has a double "y": `add_inventyory_items`. This is the real name; calling it any other way raises `AttributeError`. The misspelling exists in all versions and in the call sites.

2. **Token is not fetched at construction.** `Momentum.__init__` does not call `_get_token()`. The token (`self._token`) is an empty string until the first request. `_send_get_request` handles the 401 response from the first un-authenticated GET by fetching a token and retrying. However, `_send_post_request` and `_send_delete_request` do **not** handle 401 — if the token is empty or has expired during a POST/DELETE, the request will fail with an exception rather than retry.

3. **`get_containers_with_attributes` filter is on the container type name, not the barcode.** The filter checks `filter in c["Name"]` where `c["Name"]` is a container type name like `"T_DLS_Stability"`. A common mistake is to filter by barcode or location substring.

4. **`run_process(append=True)` modifies the workunit name but does not prevent creating a new workunit.** If the work queue contains no Running or Waiting workunit, `append=True` silently falls back to creating a new workunit with the auto-generated name. The caller cannot distinguish this from a successful append.

5. **`run_experiment` hardcodes `iterations="15"`.** The `iterations` parameter is not exposed in `run_experiment`'s signature. If you need a specific iteration count for an experiment batch, use `run_worklist` with a `batch[@experiment]` batch instead.

6. **`_send_post_request` uses different header sets depending on the data type.** Dict data is posted without `Content-Type: text/plain`. List data and raw bytes/string data are posted with `Content-Type: text/plain`. This asymmetry is a workaround for API-version-specific behaviour (noted in a comment about Momentum 7.14). Do not change the data type of arguments without verifying the correct Content-Type for each endpoint.

7. **`ui.py` import triggers a live API call.** `_stm = StreamlitMomentum()` at module-level calls `get_container_definitions()`. This means:
   - Any import failure prints an error about the API before any user code runs.
   - In tests, `import MomentumPyClient.ui` will fail unless the Momentum server is accessible.
   - Streamlit's hot-reload will re-run this import and repeat the API call.

8. **`ui.py::get_nests()` module-level function is broken.** It passes `_stm` as a positional argument to `ws.get_nests()`, which takes no arguments. This raises `TypeError`. Use `stm.ws.get_nests()` directly.

9. **`get_process_variables(process_id=...)` is broken.** When `process_id > 0`, the constructed URL is overwritten and the default URL (with `process_id=0`) is used. Always pass `process_name` instead.

10. **`get_barcodes` will crash if any container has `Inventory == None`.** Containers that are currently being transported by the robot may have `Inventory == None`. `get_barcodes` tries to access `c["Inventory"]["TemplateName"]` without a None check, raising `TypeError`. `get_containers_with_attributes` handles this correctly.

11. **`asyncio.run` inside `get_containers_with_attributes`.** This works from a normal synchronous call site. It will raise `RuntimeError: This event loop is already running` if called from inside an async function or a framework that manages its own event loop (e.g., Jupyter notebooks, some web frameworks). In Streamlit pages, this is fine because Streamlit runs page scripts synchronously.

12. **Streamlit cache TTLs are fixed.** The `cached_get_nests` TTL is 10 seconds; the module-level cached functions (`get_template_names`, etc.) use 60 seconds. These cannot be configured by the caller.

13. **`reformat_container_nests` skips Shovel and Transfer nests with `continue` but still appends to `name` before the `continue`.** This is harmless (the slot is not added to `slots`) but the `name` variable is mutated unnecessarily before the skip.
