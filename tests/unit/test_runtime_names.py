import pytest
from eduflow.runtime.names import validate_agent_name, validate_model_name


def test_validate_agent_name_accepts_valid():
    assert validate_agent_name("worker_cc") == "worker_cc"
    assert validate_agent_name("manager-1") == "manager-1"


def test_validate_agent_name_rejects_invalid():
    for bad in ["../etc", "a;b", "", "a b", "a\t"]:
        with pytest.raises(ValueError):
            validate_agent_name(bad)


def test_validate_model_name_accepts_valid():
    assert validate_model_name("claude-sonnet-5") == "claude-sonnet-5"


def test_validate_model_name_rejects_invalid():
    for bad in ["../etc", "a;b", "", "a b"]:
        with pytest.raises(ValueError):
            validate_model_name(bad)
