import os
import stat


def test_memory_db_is_600(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.memory import db
    db.close()
    conn = db.get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY)")
    conn.commit()
    db_path = db.memory_db_file()
    mode = stat.S_IMODE(db_path.stat().st_mode)
    assert mode == 0o600
