from __future__ import annotations

from pathlib import Path
import sys
import tempfile


def self_test() -> int:
    import tkinter  # noqa: F401
    from firstwindow.bootstrap import install_command
    from firstwindow.distribution import beginner_setup_action
    from firstwindow.durable import create_task, default_acceptance
    from firstwindow.hermes_agnes import HermesAgnesRoute
    from firstwindow.i18n import translate
    from firstwindow.readiness import build_readiness
    from firstwindow.resume import discover_resumable_tasks
    from firstwindow.system_status import parse_hermes_model_json

    assert install_command("windows", "hermes")[0] == "powershell"
    assert beginner_setup_action("hermes").kind == "open_url"
    assert "hermes-agent.nousresearch.com" in beginner_setup_action("hermes").target
    assert parse_hermes_model_json('{"provider":"llamacpp","default":"demo"}')["provider"] == "llamacpp"
    assert translate("zh-CN", "button.one_click_ready") == "一键就绪"
    blocked_route = HermesAgnesRoute(
        hermes_installed=True,
        provider_configured=False,
        selected=False,
        no_fallbacks=False,
        ready=False,
        model=None,
        base_url=None,
        key_env=None,
        profile_home=None,
        reason="self-test-not-configured",
    )
    report = build_readiness(
        agnes_free_confirmed=False,
        agnes_route=blocked_route,
        hermes_installed=True,
        hermes_model={"provider": "agnes", "default": "cloud"},
    )
    assert report.zero_cost_ready is False and report.action == "prepare-agnes-profile"
    acceptance = default_acceptance()
    assert len(acceptance) == 2 and "independently verified" in acceptance[1]
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        create_task(project, "self-test", "resume smoke test", acceptance)
        assert discover_resumable_tasks(project)[0].task_id == "self-test"
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    from firstwindow.gui import main
    if "--ui-self-test" in sys.argv:
        raise SystemExit(main(ui_self_test=True))
    raise SystemExit(main())
