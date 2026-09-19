from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import uuid

from .bootstrap import INSTALLER_TIMEOUT_SECONDS, install_command, run_installer_command, setup_actions
from .demo_project import create_demo_project
from .durable import (EXECUTION_ACCEPTANCE, append_evidence, create_task, default_acceptance, verification_report, write_checkpoint)
from .hermes_agnes import AGNES_MODEL, agnes_api_key_present, attest_hermes_usage, read_firstwindow_agnes_route, scoped_env
from .resume import build_resume_prompt, discover_resumable_tasks, load_resume_context
from .router import Lane, choose_lane, detect_lanes
from .runners import agnes_command, hermes_command, hermes_usage_path, project_env, run_command
from .system_status import read_agnes_capabilities, read_hermes_model


def _project(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"not a directory: {path}")
    return path


def _lanes(env: dict[str, str] | None = None):
    source = os.environ if env is None else env
    route = read_firstwindow_agnes_route()
    return detect_lanes(
        source,
        hermes_model=read_hermes_model(),
        agnes_route=route,
        agnes_credential_present=agnes_api_key_present(route.profile_home, {}),
        agnes_capabilities=read_agnes_capabilities(),
    )


def _lane_env(
    lane: Lane,
    project: Path,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    base = dict(os.environ if env is None else env)
    scoped = scoped_env(lane.profile_home, base) if lane.profile_home else base
    return project_env(project, scoped)


def _attest_lane_usage(project: Path, task_id: str, lane: Lane):
    if lane.name != "agnes-free":
        return None
    return attest_hermes_usage(
        hermes_usage_path(project, task_id),
        expected_model=lane.model or AGNES_MODEL,
    )


def _agent_command(
    project: Path,
    task_id: str,
    prompt: str,
    lane: Lane,
    model_arg: str | None,
):
    if lane.engine == "agnes":
        return agnes_command(project, task_id, prompt)

    model = lane.model or model_arg or ""
    if not model:
        raise RuntimeError("No local Hermes model is selected.")
    return hermes_command(
        project,
        task_id,
        prompt,
        model,
        provider=lane.provider,
        isolate_user_config=lane.name == "hermes-local",
    )


def _default_exit_criterion(context: dict) -> list[str] | None:
    for item in context.get("acceptance") or []:
        if item.get("text") in {"Agent process exits successfully.", EXECUTION_ACCEPTANCE}:
            return [item["id"]]
    return None


def doctor() -> int:
    lanes = _lanes()
    print("FirstWindow doctor")
    for lane in lanes:
        marker = "READY" if lane.available else "WAIT"
        cost = "$0" if lane.zero_cost else "cost-unknown"
        print(f"[{marker}] {lane.name:18} {cost:12} {lane.reason}")

    if not any(lane.available and lane.zero_cost for lane in lanes):
        print("\n$0 Guard active: FirstWindow will not silently use an unknown-cost provider.")
        print("Primary path: Hermes Agent with the isolated Agnes API provider profile.")
        print("Fallback: a verified Hermes managed local model. Direct Agnes CLI is advanced/optional only.")
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
        outcome = run_installer_command(command)
        if outcome.timed_out:
            print(
                f"Installer timed out after {INSTALLER_TIMEOUT_SECONDS} seconds. "
                "No runtime readiness is assumed.",
                file=sys.stderr,
            )
            return 124
        if outcome.error:
            print(f"Installer failed: {outcome.error}", file=sys.stderr)
            return 1
        return int(outcome.exit_code if outcome.exit_code is not None else 1)

    actions = setup_actions(
        agnes_installed=agnes_installed,
        hermes_installed=hermes_installed,
    )
    if not actions:
        print("Hermes Agent is installed; the beginner path does not require Agnes CLI.")
    else:
        print("Guided setup plan:")
        for index, action in enumerate(actions, start=1):
            print(f"{index}. {action.label}")
            print("   " + " ".join(action.command))
    print("\nPrimary: Make Me Ready configures Agnes API inside an isolated Hermes profile.")
    print("Fallback: Hermes Desktop → Local Models. Direct Agnes CLI is optional/advanced only.")
    return 0


def demo(args: argparse.Namespace) -> int:
    path = create_demo_project(Path(args.path))
    print(f"Demo project created: {path}")
    print("Suggested task is in README.md.")
    return 0


def tasks(args: argparse.Namespace) -> int:
    found = discover_resumable_tasks(args.project)
    if not found:
        print("NO RESUMABLE TASKS")
        return 0
    for item in found:
        print(f"{item.task_id}\t{item.stage}\t{item.next_action}\t{item.objective}")
    return 0


def run(args: argparse.Namespace) -> int:
    project = args.project
    task_id = args.task_id or f"fw-{uuid.uuid4().hex[:10]}"
    uses_default_acceptance = args.accept is None
    create_task(
        project,
        task_id,
        args.task,
        args.accept or default_acceptance(),
    )
    try:
        lane = choose_lane(
            _lanes(),
            zero_cost=not args.allow_unknown_cost,
            preferred=args.engine,
        )
        command = _agent_command(project, task_id, args.task, lane, args.model)
    except Exception as exc:
        append_evidence(project, task_id, "routing", False, str(exc))
        write_checkpoint(project, task_id, "blocked", "Complete a verified $0 setup, then resume.")
        print(str(exc), file=sys.stderr)
        return 2

    write_checkpoint(project, task_id, "dispatching", f"Run with {lane.name}.")
    lane_env = _lane_env(lane, project)
    code = run_command(command, project, dry_run=args.dry_run, env=lane_env)
    if args.dry_run:
        append_evidence(project, task_id, "dry-run", False, "Command planned only; agent was not executed.")
        write_checkpoint(project, task_id, "dry-run", "Execute the task without --dry-run to collect runtime evidence.")
        print(f"task_id={task_id}\nlane={lane.name}\ndry_run=true")
        return 0

    attestation = _attest_lane_usage(project, task_id, lane)
    passed = code == 0 and (attestation is None or attestation.passed)
    detail = f"{lane.name} exit_code={code}"
    if attestation is not None:
        detail += (
            f" provider={attestation.provider} model={attestation.model}"
            f" api_calls={attestation.api_calls} attestation={attestation.reason}"
        )
    append_evidence(
        project,
        task_id,
        "agent-exit",
        passed,
        detail,
        criteria=["AC-001"] if uses_default_acceptance else None,
    )
    write_checkpoint(
        project,
        task_id,
        "agent-finished" if passed else "agent-failed",
        "Collect independent outcome evidence, then run firstwindow verify." if passed else "Inspect failure and resume.",
    )
    print(f"task_id={task_id}\nlane={lane.name}")
    if attestation is not None:
        print(
            f"attestation={attestation.reason} provider={attestation.provider} "
            f"model={attestation.model} api_calls={attestation.api_calls}"
        )
    return code if passed else (code or 3)


def resume(args: argparse.Namespace) -> int:
    try:
        context = load_resume_context(args.project, args.task_id)
        prompt = build_resume_prompt(context)
        lane = choose_lane(
            _lanes(),
            zero_cost=not args.allow_unknown_cost,
            preferred=args.engine,
        )
        command = _agent_command(args.project, args.task_id, prompt, lane, args.model)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    lane_env = _lane_env(lane, args.project)
    if args.dry_run:
        code = run_command(command, args.project, dry_run=True, env=lane_env)
        print(f"task_id={args.task_id}\nlane={lane.name}\nresume=true\ndry_run=true")
        return code

    write_checkpoint(args.project, args.task_id, "resuming", context["next_action"])
    code = run_command(command, args.project, dry_run=False, env=lane_env)
    attestation = _attest_lane_usage(args.project, args.task_id, lane)
    passed = code == 0 and (attestation is None or attestation.passed)
    detail = f"{lane.name} resume_exit_code={code}"
    if attestation is not None:
        detail += (
            f" provider={attestation.provider} model={attestation.model}"
            f" api_calls={attestation.api_calls} attestation={attestation.reason}"
        )
    append_evidence(
        args.project,
        args.task_id,
        "resume-agent-exit",
        passed,
        detail,
        criteria=_default_exit_criterion(context),
    )
    write_checkpoint(
        args.project,
        args.task_id,
        "agent-finished" if passed else "agent-failed",
        "Collect independent outcome evidence, then run firstwindow verify." if passed else "Inspect failure and resume again from the latest checkpoint.",
    )
    print(f"task_id={args.task_id}\nlane={lane.name}\nresume=true")
    if attestation is not None:
        print(
            f"attestation={attestation.reason} provider={attestation.provider} "
            f"model={attestation.model} api_calls={attestation.api_calls}"
        )
    return code if passed else (code or 3)


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

    tl = sub.add_parser("tasks")
    tl.add_argument("--project", type=_project, default=Path.cwd())

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

    rr = sub.add_parser("resume")
    rr.add_argument("task_id")
    rr.add_argument("--project", type=_project, default=Path.cwd())
    rr.add_argument("--engine", choices=["agnes", "hermes", "agnes-free", "hermes-local"])
    rr.add_argument("--allow-unknown-cost", action="store_true")
    rr.add_argument("--model")
    rr.add_argument("--dry-run", action="store_true")

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
    if args.command == "tasks":
        return tasks(args)
    if args.command == "route":
        return route(args)
    if args.command == "run":
        return run(args)
    if args.command == "resume":
        return resume(args)
    if args.command == "evidence":
        return evidence(args)
    if args.command == "verify":
        return verify(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
