from __future__ import annotations

from pathlib import Path
import sys
import tempfile


def self_test() -> int:
    import tkinter  # noqa: F401
    from firstwindow.bootstrap import install_command
    from firstwindow.durable import create_task
    from firstwindow.resume import discover_resumable_tasks
    from firstwindow.system_status import parse_hermes_model_json

    assert install_command("windows", "hermes")[0] == "powershell"
    assert parse_hermes_model_json('{"provider":"llamacpp","default":"demo"}')["provider"] == "llamacpp"
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        create_task(project, "self-test", "resume smoke test", ["Agent process exits successfully."])
        assert discover_resumable_tasks(project)[0].task_id == "self-test"
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    from firstwindow.gui import main
    raise SystemExit(main())
