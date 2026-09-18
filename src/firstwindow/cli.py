from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import uuid

from .bootstrap import install_command, setup_actions
from .demo_project import create_demo_project
from .durable import append_evidence, create_task, verification_report, write_checkpoint
from .router import choose_lane, detect_lanes
from .runners import agnes_command, hermes_command, run_command
from .system_status import read_hermes_model


def _project(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"not a directory: {path}")
    return path


def _lanes(env: dict[str, str] | None = None):
    return detect_lanes(env or os.environ, hermes_model=read_hermes_model())


def doctor() -> int:
    lanes = _lanes()
    print("FirstWindow doctor")
    for lane in lanes:
        marker = "READY" if lane.available else "WAIT"
        cost = "$0" if lane.zero_cost else "cost-unknown"
        print(f"[{marker}] {lane.name:18} {cost:12} {lane.reason}")

    if not any(lane.available and lane.zero_cost for lane in lanes):
        print("\n$0 Guard active: FirstWindow will not silently use an unknown-cost provider.")
        print("Recommended: install Hermes Desktop, then choose Settings → Providers → Local Models → Use.")
        print("Alternative: configure Agnes with a free provider and explicitly confirm it.")
    return 0


def route(args: argparse.Namespace) -> int:
    lane = choose_lane(_lanes(), zero_cost=not args.allow_unknown_cost, preferred=args.engine)
    print(json.dumps(lane.__dict__, indent=2))
    return 0


def setup(args: argparse.Namespace) -> int:
    agnes_installed = shutil.which("agnes") is not None
    hermes_installed = shutil.which("hermes") is not None

    if args.install:
        command = install_command(platform.system(), args.install)
        print("Installer command:")
        print(" ".join(command))
        if not args.yes:
            print("Not executed. Re-run with --yes after reviewing the command.")
            return 2
        return int(subprocess.run(command, check=False).returncode)

    actions = setup_actions(
        agnes_installed=agnes_installed,
        hermes_installed=hermes_installed,
    )
    if not actions:
        print("Agnes and Hermes are installed.")
    else:
        print("Guided setup plan:")
        for index, action in enumerate(actions, start=1):
            print(f"{index}. {action.label}")
            print("   " + " ".join(action.command))
    print("\nRecommended $0 fallback: Hermes Desktop → Local Models → Install runtime → Download → Use.")
    return 0


def demo(args: argparse.Namespace) -> int:
    path = create_demo_project(Path(args.path))
    print(f"Demo project created: {path}")
    print("Suggested task is in README.md.")
    return 0


def run(args: argparse.Namespace) -> int:
    project = args.project
    task_id = args.task_id or f"fw-{uuid.uuid4().hex[:10]}"
    default_acceptance = args.accept is None
    create_task(
        project,
        task_id,
        args.task,
        args.accept or ["Agent process exits successfully."],
    )
    try:
        lane = choose_lane(
            _lanes(),
            zero_cost=not args.allow_unknown_cost,
            preferred=args.engine,
        )
    except Exception as exc:
        append_evidence(project, task_id, "routing", False, str(exc))
        write_checkpoint(project, task_id, "blocked", "Complete a verified $0 setup, then resume.")
        print(str(exc), file=sys.stderr)
        return 2

    write_checkpoint(project, task_id, "dispatching", f"Run with {lane.name}.")
    if lane.engine == "agnes":
        command = agnes_command(project, task_id, args.task)
    else:
        model = lane.model or args.model or ""
        if not model:
            append_evidence(project, task_id, "routing", False, "No local Hermes model is selected.")
            write_checkpoint(project, task_id, "blocked", "Select a Hermes Local Model, then resume.")
            return 2
        command = hermes_command(project, task_id, args.task, model, provider=lane.provider)

    code = run_command(command, project, dry_run=args.dry_run)
    if args.dry_run:
        append_evidence(project, task_id, "dry-run", False, "Command planned only; agent was not executed.")
        write_checkpoint(project, task_id, "dry-run", "Execute the task without --dry-run to collect runtime evidence.")
        print(f"task_id={task_id}\nlane={lane.name}\ndry_run=true")
        return 0

    append_evidence(
        project,
        task_id,
        "agent-exit",
        code == 0,
        f"{lane.name} exit_code={code}",
        criteria=["AC-001"] if default_acceptance else None,
    )
    write_checkpoint(
        project,
        task_id,
        "agent-finished" if code == 0 else "agent-failed",
        "Review evidence and run firstwindow verify." if code == 0 else "Inspect failure and resume.",
    )
    print(f"task_id={task_id}\nlane={lane.name}")
    return code


def evidence(args: argparse.Namespace) -> int:
    append_evidence(
        args.project,
        args.task_id,
        args.kind,
        not args.fail,
        args.detail,
        criteria=args.criterion,
    )
    state = "FAIL" if args.fail else "PASS"
    refs = ",".join(args.criterion or []) or "none"
    print(f"evidence={state} criteria={refs}")
    return 0


def verify(args: argparse.Namespace) -> int:
    report = verification_report(args.project, args.task_id)
    if report["mode"] == "criteria":
        for item in report["covered"]:
            print(f"COVERED {item['id']}: {item['text']}")
        for item in report["uncovered"]:
            print(f"UNCOVERED {item['id']}: {item['text']}")
        for item in report["failed"]:
            print(f"FAILED {item['id']}: {item['text']}")

    if report["ok"]:
        print("VERIFIED: acceptance criteria are covered by current passing evidence.")
        return 0

    print("NOT VERIFIED")
    for failure in report["failures"]:
        print(f"- {failure}")
    return 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="firstwindow")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")

    s = sub.add_parser("setup")
    s.add_argument("--install", choices=["agnes", "hermes"])
    s.add_argument("--yes", action="store_true")

    d = sub.add_parser("demo")
    d.add_argument("path", nargs="?", default="FirstWindow-Demo")

    r = sub.add_parser("route")
    r.add_argument("--engine", choices=["agnes", "hermes", "agnes-free", "hermes-local"])
    r.add_argument("--allow-unknown-cost", action="store_true")

    x = sub.add_parser("run")
    x.add_argument("task")
    x.add_argument("--project", type=_project, default=Path.cwd())
    x.add_argument("--task-id")
    x.add_argument("--accept", action="append")
    x.add_argument("--engine", choices=["agnes", "hermes", "agnes-free", "hermes-local"])
    x.add_argument("--allow-unknown-cost", action="store_true")
    x.add_argument("--model")
    x.add_argument("--dry-run", action="store_true")

    e = sub.add_parser("evidence")
    e.add_argument("task_id")
    e.add_argument("--project", type=_project, default=Path.cwd())
    e.add_argument("--criterion", action="append")
    e.add_argument("--kind", default="manual")
    e.add_argument("--detail", required=True)
    e.add_argument("--fail", action="store_true")

    v = sub.add_parser("verify")
    v.add_argument("task_id")
    v.add_argument("--project", type=_project, default=Path.cwd())
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "doctor":
        return doctor()
    if args.command == "setup":
        return setup(args)
    if args.command == "demo":
        return demo(args)
    if args.command == "route":
        return route(args)
    if args.command == "run":
        return run(args)
    if args.command == "evidence":
        return evidence(args)
    if args.command == "verify":
        return verify(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
