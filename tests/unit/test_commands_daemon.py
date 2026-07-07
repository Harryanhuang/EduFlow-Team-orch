from __future__ import annotations

from dataclasses import dataclass

from helpers import attr_patch, run_cli
from eduflow.commands import daemon as cmd_daemon


@dataclass
class Spec:
    name: str


def test_daemon_heal_noops_when_all_alive():
    specs = [Spec("router"), Spec("watchdog")]
    restarts = []

    with attr_patch(cmd_daemon.watchdog, all_known_specs=lambda: specs), \
            attr_patch(cmd_daemon, _alive=lambda spec: True,
                       _restart_one=lambda spec: restarts.append(spec.name)):
        rc, out, err = run_cli(["daemon", "heal"])

    assert rc == 0
    assert err == ""
    assert restarts == []
    assert "router: alive" in out
    assert "watchdog: alive" in out


def test_daemon_heal_restarts_only_dead_specs():
    specs = [Spec("router"), Spec("watchdog")]
    restarted = []

    def alive(spec):
        return spec.name == "watchdog"

    def restart_one(spec):
        restarted.append(spec.name)
        return (spec.name, "respawned")

    with attr_patch(cmd_daemon.watchdog, all_known_specs=lambda: specs), \
            attr_patch(cmd_daemon, _alive=alive, _restart_one=restart_one):
        rc, out, err = run_cli(["daemon", "heal"])

    assert rc == 0
    assert err == ""
    assert restarted == ["router"]
    assert "router: respawned" in out
    assert "watchdog: alive" in out


def test_daemon_heal_returns_nonzero_when_respawn_fails():
    specs = [Spec("router")]

    with attr_patch(cmd_daemon.watchdog, all_known_specs=lambda: specs), \
            attr_patch(cmd_daemon, _alive=lambda spec: False,
                       _restart_one=lambda spec: (spec.name, "fail: boom")):
        rc, out, err = run_cli(["daemon", "heal"])

    assert rc == 1
    assert err == ""
    assert "router: fail: boom" in out
    assert "1 daemon(s) failed" in out
