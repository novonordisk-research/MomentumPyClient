import pytest

from MomentumPyClient.ws import (
    DEFAULT_NUMBERING_FROM_BOTTOM,
    Momentum,
    resolve_numbering_from_bottom,
)


@pytest.fixture
def ws():
    return Momentum(url="https://host/api/", user_name="u", password="p")


def nest(name, device, is_stack=False, stack_contents=()):
    return {
        "Name": name,
        "DeviceName": device,
        "IsStack": is_stack,
        "Content": None,
        "StackContents": list(stack_contents),
    }


def nests_for(device, n=3):
    return [nest(f"{device}:Column1:Nest {i}", device) for i in range(1, n + 1)]


def order(slots, device):
    return [s["Nest"] for s in slots if s["Name"] == device]


def test_resolve_defaults():
    assert resolve_numbering_from_bottom("Cytomat10_C450") is True
    assert resolve_numbering_from_bottom("Cytomat10_C425") is True
    assert resolve_numbering_from_bottom("Liconic_1") is True
    assert resolve_numbering_from_bottom("Dim4Carousel") is False
    assert resolve_numbering_from_bottom("Carousel") is False
    assert resolve_numbering_from_bottom("Unknown") is None
    assert resolve_numbering_from_bottom("Unknown", None) is None
    assert "Cytomat*" in DEFAULT_NUMBERING_FROM_BOTTOM


def test_resolve_bool_passthrough():
    assert resolve_numbering_from_bottom("anything", True) is True
    assert resolve_numbering_from_bottom("anything", False) is False


def test_resolve_exact_beats_pattern_and_pattern_order():
    setting = {"Cytomat*": True, "Cytomat10_C450": False}
    assert resolve_numbering_from_bottom("Cytomat10_C450", setting) is False
    assert resolve_numbering_from_bottom("Cytomat10_C425", setting) is True
    setting = {"A*": True, "A?": False}
    assert resolve_numbering_from_bottom("Ab", setting) is True
    assert resolve_numbering_from_bottom("Zz", setting) is None


def test_reformat_none_keeps_momentum_order(ws):
    nests = list(reversed(nests_for("Cytomat10_C450")))
    assert order(ws.reformat_container_nests(nests), "Cytomat10_C450") == [3, 2, 1]


@pytest.mark.parametrize(
    "setting, expected",
    [(True, [1, 2, 3]), (False, [3, 2, 1])],
)
def test_reformat_bool_orders_bottom_to_top(ws, setting, expected):
    slots = ws.reformat_container_nests(
        nests_for("Dev"), numbering_from_bottom=setting
    )
    assert order(slots, "Dev") == expected


def test_reformat_mapping_per_device(ws):
    nests = nests_for("Dim4Carousel") + nests_for("Cytomat10_C450")
    slots = ws.reformat_container_nests(nests, numbering_from_bottom={"Cytomat*": True, "Dim4Carousel": False})
    assert order(slots, "Dim4Carousel") == [3, 2, 1]
    assert order(slots, "Cytomat10_C450") == [1, 2, 3]


def test_reformat_mapping_unmatched_device_keeps_order(ws):
    nests = list(reversed(nests_for("Other")))
    slots = ws.reformat_container_nests(nests, numbering_from_bottom={"Cytomat*": True})
    assert order(slots, "Other") == [3, 2, 1]


def test_reformat_stacks_always_ascending(ws):
    contents = [
        {"ContainerName": "T (Id: 1)", "Barcode": f"B{i}", "Position": i}
        for i in (3, 1, 2)
    ]
    nests = [nest("Carousel:Column5_Stack1", "Carousel", True, contents)]
    for setting in (True, False):
        slots = ws.reformat_container_nests(nests, numbering_from_bottom=setting)
        assert order(slots, "Carousel") == [1, 2, 3]
