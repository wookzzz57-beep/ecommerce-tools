from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

from .durable import append_evidence, create_task, verify_task, write_checkpoint
from .router import choose_lane, detect_lanes
from .runners import agnes_command, hermes_command, local_model_from_env, run_command

def _project(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"not a directory: {path}")
    return path

def doctor() -> int:
    lanes = detect_lanes()
    print("FirstWindow doctor")
    for lane in lanes:
        marker = "READY" if lane.available else "WAIT"
        cost = "$0" if lane.zero_cost else "cost-unknown"
        print(f"[{marker}] {lane.name:18} {cost:12} {lane.reason}")
    if not any(lane.available and lane.zero_cost for lane in lanes):
        print("\n$0 Guard active: no unknown-cost fallback.")
        print("Agnes: configure a free provider, then set FIRSTWINDOW_AGNES_FREE_CONFIRMED=1.")
        print("Hermes local: configure Custom endpoint http://localhost:11434/v1,")
        print("then set FIRSTWINDOW_HERMES_LOCAL_CONFIRMED=1 and FIRSTWINDOW_LOCAL_MODEL=<model>.")
    return 0

def route(args: argparse.Namespace) -> int:
    lane = choose_lane(detect_lanes(), zero_cost=not args.allow_unknown_cost, preferred=args.engine)
    print(json.dumps(lane.__dict__, indent=2))
    return 0

def run(args: argparse.Namespace) -> int:
    project = args.project
    task_id = args.task_id or f"fw-{uuid.uuid4().hex[:10]}"
    create_task(project, task_id, args.task, args.accept or ["Agent exits successfully and reports verification evidence."])
    try:
        lane = choose_lane(detect_lanes(), zero_cost=not args.allow_unknown_cost, preferred=args.engine)
    except Exception as exc:
        append_evidence(project, task_id, "routing", False, str(exc))
        write_checkpoint(project, task_id, "blocked", "Configure a verified $0 lane, then resume.")
        print(str(exc), file=sys.stderr)
        return 2
    write_checkpoint(project, task_id, "dispatching", f"Run with {lane.name}.")
    if lane.engine == "agnes":
        command = agnes_command(project, task_id, args.task)
    else:
        model = local_model_from_env() or (args.model or "")
        if lane.name == "hermes-local" and not model:
            append_evidence(project, task_id, "routing", False, "FIRSTWINDOW_LOCAL_MODEL is missing")
            return 2
        command = hermes_command(project, task_id, args.task, model)
    code = run_command(command, project, dry_run=args.dry_run)
    append_evidence(project, task_id, "agent-exit", code == 0, f"{lane.name} exit_code={code}")
    write_checkpoint(project, task_id, "agent-finished" if code == 0 else "agent-failed",
                     "Review evidence and run firstwindow verify." if code == 0 else "Inspect failure and resume.")
    print(f"task_id={task_id}\nlane={lane.name}")
    return code

def verify(args: argparse.Namespace) -> int:
    ok, failures = verify_task(args.project, args.task_id)
    if ok:
        print("VERIFIED: durable state plus passing evidence are present.")
        return 0
    print("NOT VERIFIED")
    for failure in failures:
        print(f"- {failure}")
    return 1

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="firstwindow")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
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
    v = sub.add_parser("verify")
    v.add_argument("task_id")
    v.add_argument("--project", type=_project, default=Path.cwd())
    return p

def main() -> int:
    args = parser().parse_args()
    if args.command == "doctor": return doctor()
    if args.command == "route": return route(args)
    if args.command == "run": return run(args)
    if args.command == "verify": return verify(args)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
