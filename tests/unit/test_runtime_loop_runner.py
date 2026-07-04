from eduflow.runtime import loop_runner


class Proc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_checker_cycle_passes(tmp_path):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return Proc(0, stdout="ok")

    result = loop_runner.run_checker_cycle(
        commands=[["pytest", "-q"]],
        cwd=tmp_path,
        run=fake_run,
    )

    assert result["passed"] is True
    assert result["failed_commands"] == []
    assert result["check_mode"] == "self_check"
    assert calls == [["pytest", "-q"]]


def test_run_checker_cycle_records_review_check_mode(tmp_path):
    def fake_run(args, **kwargs):
        return Proc(0, stdout="ok")

    result = loop_runner.run_checker_cycle(
        commands=[["pytest", "-q"]],
        cwd=tmp_path,
        run=fake_run,
        check_mode="review_check",
    )

    assert result["check_mode"] == "review_check"


def test_same_failure_repeated_stops():
    previous = {"failed_commands": ["pytest -q"], "failure_fingerprint": "abc"}
    current = {"failed_commands": ["pytest -q"], "failure_fingerprint": "abc"}

    decision = loop_runner.decide_stop(current, previous, cycle=2, max_cycles=5)
    assert decision["status"] == "stopped"
    assert decision["stop_reason"] == "same_failure_repeated"


def test_max_cycles_stops():
    current = {"failed_commands": ["pytest -q"], "failure_fingerprint": "abc"}
    decision = loop_runner.decide_stop(current, None, cycle=3, max_cycles=3)
    assert decision["status"] == "stopped"
    assert decision["stop_reason"] == "max_cycles"


def test_no_failure_reduction_stops():
    previous = {"failed_commands": ["pytest -q"], "failure_fingerprint": "abc"}
    current = {"failed_commands": ["compileall"], "failure_fingerprint": "def"}
    decision = loop_runner.decide_stop(current, previous, cycle=2, max_cycles=5)
    assert decision["status"] == "stopped"
    assert decision["stop_reason"] == "no_failure_reduction"


def test_regression_detected_stops():
    previous = {"failed_commands": ["pytest -q"], "passed_commands": ["compileall"]}
    current = {"failed_commands": ["compileall"], "failure_fingerprint": "def"}
    decision = loop_runner.decide_stop(current, previous, cycle=2, max_cycles=5)
    assert decision["status"] == "stopped"
    assert decision["stop_reason"] == "regression_detected"


def test_fingerprint_normalizes_paths_timestamps_and_line_numbers():
    a = loop_runner.fingerprint_failure(
        "FAILED /Users/a/repo/tests/test_x.py::test_case\n"
        "  File '/Users/a/repo/src/foo.py', line 42\n"
        "2026-07-04 12:09:33 ERROR object=0xabc123"
    )
    b = loop_runner.fingerprint_failure(
        "FAILED /Users/b/repo/tests/test_x.py::test_case\n"
        "  File '/Users/b/repo/src/foo.py', line 99\n"
        "2026-07-04 14:22:01 ERROR object=0xdef456"
    )
    assert a == b
