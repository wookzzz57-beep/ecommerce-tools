from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "schema_version",
    "project",
    "phase",
    "status",
    "canonical_branch",
    "current_release",
    "primary_objective",
    "active_engineering_issue",
    "engineering_queue",
    "launch_track",
    "wip_limit",
    "resume_point",
    "last_verified_main_sha",
)


def validate_project_state(state: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in state:
            failures.append(f"missing required field: {field}")

    if failures:
        return failures

    if state["schema_version"] != 1:
        failures.append("schema_version must be 1")
    if state["project"] != "FirstWindow":
        failures.append("project must be FirstWindow")
    if state["canonical_branch"] != "main":
        failures.append("canonical_branch must be main")
    if state["status"] not in {"active", "blocked", "release-candidate", "released", "post-release"}:
        failures.append("status is not recognized")
    if state["wip_limit"] != 1:
        failures.append("wip_limit must remain 1 for primary engineering work")

    queue = state["engineering_queue"]
    active = state["active_engineering_issue"]
    status = state["status"]

    if not isinstance(queue, list):
        failures.append("engineering_queue must be a list")
    elif status in {"released", "post-release"}:
        if queue:
            failures.append(f"{status} state must have an empty engineering_queue")
        if active is not None:
            failures.append(f"{status} state must not have an active_engineering_issue")
    else:
        if not queue:
            failures.append("engineering_queue must be a non-empty list")
        elif active not in queue:
            failures.append("active_engineering_issue must appear in engineering_queue")
        elif queue[0] != active:
            failures.append("active_engineering_issue must be first in engineering_queue")

    if isinstance(queue, list) and len(queue) != len(set(queue)):
        failures.append("engineering_queue must not contain duplicates")

    launch_track = state["launch_track"]
    if not isinstance(launch_track, list):
        failures.append("launch_track must be a list")
    else:
        if len(launch_track) != len(set(launch_track)):
            failures.append("launch_track must not contain duplicates")
        if status == "released" and launch_track:
            failures.append("released state must have an empty launch_track")
        if status == "post-release" and not launch_track:
            failures.append("post-release state must have a non-empty launch_track")

    if status == "post-release":
        launch_control = state.get("launch_control")
        if not isinstance(launch_control, dict):
            failures.append("post-release state must define launch_control")
        else:
            active_launch = launch_control.get("active_issue")
            if not isinstance(active_launch, int) or active_launch <= 0:
                failures.append("launch_control.active_issue must be a positive issue number")
            elif isinstance(launch_track, list) and launch_track and active_launch != launch_track[0]:
                failures.append("launch_control.active_issue must be first in launch_track")

            if launch_control.get("experiment_wip_limit") != 1:
                failures.append("launch_control.experiment_wip_limit must be 1")
            if launch_control.get("product_baseline_frozen") is not True:
                failures.append("launch_control.product_baseline_frozen must be true")

    blockers = state.get("external_blockers", [])
    if status in {"released", "post-release"}:
        if not isinstance(blockers, list):
            failures.append("external_blockers must be a list")
        elif status == "released" and blockers:
            failures.append("released state must have no external_blockers")

    for field in ("phase", "current_release", "primary_objective", "resume_point", "last_verified_main_sha"):
        value = state[field]
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{field} must be a non-empty string")

    sha = state["last_verified_main_sha"]
    if isinstance(sha, str) and not (7 <= len(sha) <= 40 and all(c in "0123456789abcdef" for c in sha.lower())):
        failures.append("last_verified_main_sha must look like a Git commit SHA")

    return failures


def load_project_state(path: Path = Path("PROJECT_STATE.json")) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    path = Path("PROJECT_STATE.json")
    if not path.is_file():
        print("project state missing: PROJECT_STATE.json")
        return 1

    try:
        state = load_project_state(path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid project state: {exc}")
        return 1

    failures = validate_project_state(state)
    if failures:
        print("project state validation failed:")
        print("\n".join(f"- {item}" for item in failures))
        return 1

    active_issue = state["active_engineering_issue"]
    active_display = f"#{active_issue}" if active_issue is not None else "none"
    launch_display = "none"
    launch_control = state.get("launch_control")
    if isinstance(launch_control, dict) and launch_control.get("active_issue"):
        launch_display = f"#{launch_control['active_issue']}"

    print(
        "project state ok: "
        f"phase={state['phase']} status={state['status']} active_issue={active_display} "
        f"launch_issue={launch_display} resume={state['resume_point']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
