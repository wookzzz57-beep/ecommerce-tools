from __future__ import annotations

import sys


def self_test() -> int:
    import tkinter  # noqa: F401
    from firstwindow.bootstrap import install_command
    from firstwindow.system_status import parse_hermes_model_json

    assert install_command("windows", "hermes")[0] == "powershell"
    assert parse_hermes_model_json('{"provider":"llamacpp","default":"demo"}')["provider"] == "llamacpp"
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    from firstwindow.gui import main
    raise SystemExit(main())
