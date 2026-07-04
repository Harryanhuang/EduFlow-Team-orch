from eduflow.runtime import loop_specs


def test_code_repair_spec_is_explicit():
    spec = loop_specs.resolve("code-repair")
    assert spec["name"] == "code-repair"
    assert ["pytest", "-q"] in spec["commands"]
    assert ["python3", "-m", "compileall", "-q", "src"] in spec["commands"]


def test_unknown_spec_rejected():
    try:
        loop_specs.resolve("content-review")
    except ValueError as e:
        assert "unknown loop spec" in str(e)
    else:
        raise AssertionError("expected ValueError")
