from __future__ import annotations

import os
from pathlib import Path
import platform
import queue
import shutil
import subprocess
import tempfile
import threading
import traceback
import uuid
import webbrowser

from .bootstrap import install_command
from .demo_project import create_demo_project
from .distribution import beginner_setup_action
from .durable import append_evidence, create_task, write_checkpoint
from .i18n import LANGUAGE_NAMES, default_settings_path, load_language, save_language, translate
from .onboarding import BeginnerState
from .readiness import build_readiness, probe_command, route_fingerprint
from .resume import build_resume_prompt, discover_resumable_tasks, load_resume_context
from .router import choose_lane, detect_lanes
from .runners import agnes_command, hermes_command
from .system_status import hermes_local_ready, read_hermes_model
from .windows_paths import refresh_runtime_paths


def main(*, ui_self_test: bool = False) -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class App:
        def __init__(self, root: tk.Tk):
            self.root = root
            self.root.title("FirstWindow")
            self.root.geometry("960x800")
            self.root.minsize(820, 680)

            self.language = load_language()
            self.language_var = tk.StringVar(value=LANGUAGE_NAMES[self.language])
            self.runtime_key = "auto"
            self.runtime_var = tk.StringVar()
            self.project_var = tk.StringVar()
            self.agnes_free_var = tk.BooleanVar(value=False)
            self.status_var = tk.StringVar()
            self.next_var = tk.StringVar()
            self.resume_var = tk.StringVar()

            self.events: queue.Queue[tuple[str, object]] = queue.Queue()
            self.resume_candidate = None
            self.running = False
            self.setup_waiting = False
            self.setup_poll_id = None
            self.setup_probe_running = False
            self.verified_lane: str | None = None
            self.verified_route = None

            self._build()
            self._apply_language(initial=True)
            self.refresh()
            self.root.after(100, self._poll_events)

        def _tr(self, key: str, **values: object) -> str:
            return translate(self.language, key, **values)

        def _build(self) -> None:
            style = ttk.Style()
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

            self.outer = ttk.Frame(self.root, padding=22)
            self.outer.pack(fill="both", expand=True)

            header = ttk.Frame(self.outer)
            header.pack(fill="x")
            ttk.Label(header, text="FirstWindow", font=("Segoe UI", 22, "bold")).pack(side="left", anchor="w")
            language_box = ttk.Frame(header)
            language_box.pack(side="right", anchor="e")
            self.language_label = ttk.Label(language_box)
            self.language_label.pack(side="left", padx=(0, 6))
            self.language_combo = ttk.Combobox(
                language_box,
                textvariable=self.language_var,
                state="readonly",
                width=12,
                values=list(LANGUAGE_NAMES.values()),
            )
            self.language_combo.pack(side="left")
            self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)

            self.subtitle_label = ttk.Label(self.outer, font=("Segoe UI", 11))
            self.subtitle_label.pack(anchor="w", pady=(2, 18))

            self.status_box = ttk.LabelFrame(self.outer, padding=14)
            self.status_box.pack(fill="x")
            ttk.Label(self.status_box, textvariable=self.status_var, justify="left").pack(anchor="w")
            ttk.Label(self.status_box, textvariable=self.next_var, justify="left", wraplength=860).pack(
                anchor="w", pady=(6, 0)
            )

            buttons = ttk.Frame(self.status_box)
            buttons.pack(fill="x", pady=(12, 0))
            self.diagnose_button = ttk.Button(buttons, command=self.refresh)
            self.diagnose_button.pack(side="left")
            self.one_click_button = ttk.Button(buttons, command=self.setup_zero_path)
            self.one_click_button.pack(side="left", padx=8)
            self.hermes_local_button = ttk.Button(buttons, command=self.open_hermes)
            self.hermes_local_button.pack(side="left")

            manual = ttk.Frame(self.status_box)
            manual.pack(fill="x", pady=(8, 0))
            self.agnes_desktop_button = ttk.Button(
                manual, command=lambda: self.open_beginner_setup("agnes")
            )
            self.agnes_desktop_button.pack(side="left")
            self.hermes_desktop_button = ttk.Button(
                manual, command=lambda: self.open_beginner_setup("hermes")
            )
            self.hermes_desktop_button.pack(side="left", padx=8)

            advanced = ttk.Frame(self.status_box)
            advanced.pack(fill="x", pady=(8, 0))
            self.advanced_label = ttk.Label(advanced)
            self.advanced_label.pack(side="left")
            self.agnes_cli_button = ttk.Button(advanced, command=lambda: self.install("agnes"))
            self.agnes_cli_button.pack(side="left", padx=8)
            self.hermes_cli_button = ttk.Button(advanced, command=lambda: self.install("hermes"))
            self.hermes_cli_button.pack(side="left")

            self.project_box = ttk.LabelFrame(self.outer, padding=14)
            self.project_box.pack(fill="x", pady=14)
            row = ttk.Frame(self.project_box)
            row.pack(fill="x")
            ttk.Entry(row, textvariable=self.project_var).pack(side="left", fill="x", expand=True)
            self.browse_button = ttk.Button(row, command=self.choose_project)
            self.browse_button.pack(side="left", padx=(8, 0))
            self.demo_button = ttk.Button(row, command=self.create_demo)
            self.demo_button.pack(side="left", padx=(8, 0))

            resume_row = ttk.Frame(self.project_box)
            resume_row.pack(fill="x", pady=(10, 0))
            ttk.Label(resume_row, textvariable=self.resume_var).pack(side="left", fill="x", expand=True)
            self.refresh_resume_button = ttk.Button(resume_row, command=self.refresh_resume)
            self.refresh_resume_button.pack(side="right")
            self.resume_button = ttk.Button(resume_row, command=self.resume_latest, state="disabled")
            self.resume_button.pack(side="right", padx=(0, 8))

            self.task_box = ttk.LabelFrame(self.outer, padding=14)
            self.task_box.pack(fill="both", expand=True)
            self.task = tk.Text(self.task_box, height=8, wrap="word", font=("Segoe UI", 11))
            self.task.pack(fill="both", expand=True)

            controls = ttk.Frame(self.task_box)
            controls.pack(fill="x", pady=(12, 0))
            self.runtime_label = ttk.Label(controls)
            self.runtime_label.pack(side="left")
            self.runtime_combo = ttk.Combobox(
                controls,
                textvariable=self.runtime_var,
                state="readonly",
                width=22,
            )
            self.runtime_combo.pack(side="left", padx=8)
            self.runtime_combo.bind("<<ComboboxSelected>>", self._on_runtime_change)
            self.agnes_check = ttk.Checkbutton(
                controls,
                variable=self.agnes_free_var,
                command=self.refresh,
            )
            self.agnes_check.pack(side="left", padx=8)
            self.start_button = ttk.Button(controls, command=self.start)
            self.start_button.pack(side="right")

            self.log_box = ttk.LabelFrame(self.outer, padding=10)
            self.log_box.pack(fill="both", expand=True, pady=(14, 0))
            self.log = tk.Text(self.log_box, height=9, wrap="word", state="disabled", font=("Consolas", 9))
            self.log.pack(fill="both", expand=True)

        def _runtime_labels(self) -> dict[str, str]:
            return {
                "auto": self._tr("runtime.auto"),
                "agnes-free": self._tr("runtime.agnes_free"),
                "hermes-local": self._tr("runtime.hermes_local"),
            }

        def _apply_language(self, *, initial: bool = False) -> None:
            self.language_label.configure(text=self._tr("label.language"))
            self.subtitle_label.configure(text=self._tr("app.subtitle"))
            self.status_box.configure(text=self._tr("section.system"))
            self.project_box.configure(text=self._tr("section.project"))
            self.task_box.configure(text=self._tr("section.task"))
            self.log_box.configure(text=self._tr("section.activity"))
            self.diagnose_button.configure(text=self._tr("button.diagnose"))
            self.one_click_button.configure(text=self._tr("button.one_click_ready"))
            self.agnes_desktop_button.configure(text=self._tr("button.agnes_desktop"))
            self.hermes_desktop_button.configure(text=self._tr("button.hermes_desktop"))
            self.hermes_local_button.configure(text=self._tr("button.hermes_local"))
            self.advanced_label.configure(text=self._tr("label.advanced"))
            self.agnes_cli_button.configure(text=self._tr("button.agnes_cli"))
            self.hermes_cli_button.configure(text=self._tr("button.hermes_cli"))
            self.browse_button.configure(text=self._tr("button.browse"))
            self.demo_button.configure(text=self._tr("button.create_demo"))
            self.refresh_resume_button.configure(text=self._tr("button.refresh_resume"))
            self.resume_button.configure(text=self._tr("button.resume"))
            self.runtime_label.configure(text=self._tr("label.runtime"))
            self.agnes_check.configure(text=self._tr("checkbox.agnes_free"))
            self.start_button.configure(text=self._tr("button.start"))

            labels = self._runtime_labels()
            self.runtime_combo.configure(values=[labels["auto"], labels["agnes-free"], labels["hermes-local"]])
            self.runtime_var.set(labels[self.runtime_key])

            if initial and not self.task.get("1.0", "end").strip():
                self.task.insert("1.0", self._tr("task.default"))
            if initial:
                self.resume_var.set(self._tr("resume.none_selected"))
                self.status_var.set(self._tr("status.checking"))

        def _on_language_change(self, _event=None) -> None:
            selected = self.language_var.get()
            reverse = {name: code for code, name in LANGUAGE_NAMES.items()}
            new_language = reverse.get(selected, "en")
            if new_language == self.language:
                return

            old_default = self._tr("task.default")
            current_task = self.task.get("1.0", "end").strip()
            self.language = new_language
            try:
                save_language(new_language)
            except OSError as exc:
                self._append(str(exc))

            if current_task == old_default:
                self.task.delete("1.0", "end")
                self.task.insert("1.0", self._tr("task.default"))

            self._apply_language()
            self._append(self._tr("language.changed", language=LANGUAGE_NAMES[self.language]))
            self.refresh()

        def _on_runtime_change(self, _event=None) -> None:
            reverse = {label: key for key, label in self._runtime_labels().items()}
            self.runtime_key = reverse.get(self.runtime_var.get(), "auto")

        def _append(self, text: str) -> None:
            self.log.configure(state="normal")
            self.log.insert("end", text.rstrip() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        def _env(self) -> dict[str, str]:
            env = dict(os.environ)
            if self.agnes_free_var.get():
                env["FIRSTWINDOW_AGNES_FREE_CONFIRMED"] = "1"
            else:
                env.pop("FIRSTWINDOW_AGNES_FREE_CONFIRMED", None)
            return env

        def _state(self):
            model = read_hermes_model()
            state = BeginnerState(
                agnes_installed=shutil.which("agnes") is not None,
                agnes_free_confirmed=bool(self.agnes_free_var.get()),
                hermes_installed=shutil.which("hermes") is not None,
                hermes_local_ready=hermes_local_ready(model),
            )
            report = build_readiness(
                agnes_installed=state.agnes_installed,
                agnes_free_confirmed=state.agnes_free_confirmed,
                hermes_installed=state.hermes_installed,
                hermes_model=model,
            )
            return state, model, report

        def _refresh_runtime_paths(self) -> None:
            for target in ("hermes", "agnes"):
                try:
                    refresh_runtime_paths(platform.system(), target)
                except Exception:
                    pass

        def refresh(self) -> None:
            self._refresh_runtime_paths()
            state, model, report = self._state()
            if self.verified_lane:
                current_route = route_fingerprint(report, self.verified_lane)
                if current_route != self.verified_route:
                    self.verified_lane = None
                    self.verified_route = None
            local_name = str(model.get("default") or model.get("model") or "")
            agnes_text = self._tr("status.installed") if state.agnes_installed else self._tr("status.not_installed")
            if state.agnes_installed and state.agnes_free_confirmed:
                agnes_text += " · " + self._tr("status.zero_confirmed")

            hermes_text = self._tr("status.not_installed")
            if state.hermes_installed:
                hermes_text = self._tr("status.installed")
                if state.hermes_local_ready:
                    hermes_text += " · " + self._tr("status.local_ready", model=local_name)
                else:
                    provider = str(model.get("provider") or "").strip()
                    configured_model = str(model.get("default") or model.get("model") or "").strip()
                    if provider and configured_model:
                        hermes_text += f" · {provider}/{configured_model}"
                    hermes_text += " · " + self._tr("status.choose_local")

            status_text = self._tr(
                "status.summary",
                agnes=agnes_text,
                hermes=hermes_text,
                guard=self._tr("status.guard_on"),
            )
            if self.verified_lane:
                status_text += "\n" + self._tr("setup.probe_passed", lane=self.verified_lane)
            self.status_var.set(status_text)

            if report.action == "verify":
                self.next_var.set(self._tr("next.ready"))
            elif report.action == "install-hermes":
                self.next_var.set(self._tr("next.install"))
            else:
                self.next_var.set(self._tr("next.configure"))

            self.refresh_resume()

        def choose_project(self) -> None:
            path = filedialog.askdirectory(title=self._tr("choose.project"))
            if path:
                self.project_var.set(path)
                self.refresh_resume()

        def create_demo(self) -> None:
            parent = filedialog.askdirectory(title=self._tr("choose.demo_parent"))
            if not parent:
                return
            target = Path(parent) / "FirstWindow-Demo"
            try:
                create_demo_project(target)
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.demo"), str(exc))
                return
            self.project_var.set(str(target))
            self._append(self._tr("log.created_demo", path=target))
            self.refresh_resume()

        def refresh_resume(self) -> None:
            project = Path(self.project_var.get()).expanduser()
            self.resume_candidate = None
            self.resume_button.configure(state="disabled")
            if not project.is_dir():
                self.resume_var.set(self._tr("resume.choose_project"))
                return
            tasks = discover_resumable_tasks(project)
            if not tasks:
                self.resume_var.set(self._tr("resume.none_found"))
                return
            self.resume_candidate = tasks[0]
            item = tasks[0]
            self.resume_var.set(
                self._tr(
                    "resume.item",
                    task_id=item.task_id,
                    stage=item.stage,
                    next_action=item.next_action,
                )
            )
            if not self.running:
                self.resume_button.configure(state="normal")

        def _creation_flags(self) -> int:
            return subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0

        def open_beginner_setup(self, target: str) -> None:
            try:
                action = beginner_setup_action(target)
                opened = webbrowser.open(action.target)
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.setup"), str(exc))
                return
            self._append(
                self._tr(
                    "setup.opened",
                    target=target.title(),
                    url=action.target,
                )
            )
            if not opened:
                messagebox.showinfo(
                    self._tr("dialog.setup"),
                    self._tr("setup.browser_manual", url=action.target),
                )

        def _run_installer(self, target: str, *, confirmed: bool = False, continue_setup: bool = False) -> None:
            try:
                command = install_command(platform.system(), target)
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.setup"), str(exc))
                return

            if not confirmed:
                shown = " ".join(command)
                if not messagebox.askyesno(
                    self._tr("confirm.installer.title"),
                    self._tr("confirm.installer", target=target.title(), command=shown),
                ):
                    return

            self.one_click_button.configure(state="disabled")

            def worker():
                self.events.put(("log", self._tr("setup.installing", target=target.title())))
                try:
                    code = subprocess.run(
                        command,
                        check=False,
                        creationflags=self._creation_flags(),
                    ).returncode
                    if code == 0:
                        added = refresh_runtime_paths(platform.system(), target)
                        if added:
                            self.events.put(("log", self._tr("setup.path_refreshed")))
                    self.events.put(("log", self._tr("setup.installer_exit", target=target.title(), code=code)))
                    if code == 0 and continue_setup:
                        self.events.put(("continue_setup", ""))
                except Exception as exc:
                    self.events.put(
                        ("log", self._tr("setup.installer_failed", target=target.title(), error=exc))
                    )
                self.events.put(("refresh", ""))

            threading.Thread(target=worker, daemon=True).start()

        def install(self, target: str) -> None:
            self._run_installer(target)

        def setup_zero_path(self) -> None:
            if self.setup_probe_running:
                return
            self._refresh_runtime_paths()
            _state, _model, report = self._state()

            if report.zero_cost_ready:
                self.setup_waiting = False
                self._start_ready_probe(report)
                return

            if report.action == "install-hermes":
                if messagebox.askyesno(
                    self._tr("dialog.one_click"),
                    self._tr("confirm.hermes_install"),
                ):
                    self._run_installer("hermes", confirmed=True, continue_setup=True)
                else:
                    self.open_beginner_setup("hermes")
                return

            self.setup_waiting = True
            self._append(self._tr("setup.waiting"))
            self.open_hermes()
            messagebox.showinfo(
                self._tr("dialog.one_click"),
                self._tr("setup.hermes_local_required"),
            )
            self._schedule_setup_poll()

        def _schedule_setup_poll(self) -> None:
            if self.setup_poll_id is None and self.setup_waiting:
                self.setup_poll_id = self.root.after(3000, self._poll_setup_progress)

        def _poll_setup_progress(self) -> None:
            self.setup_poll_id = None
            if not self.setup_waiting:
                return
            self._refresh_runtime_paths()
            _state, _model, report = self._state()
            if report.zero_cost_ready:
                self.setup_waiting = False
                self.refresh()
                self._start_ready_probe(report)
                return
            self._schedule_setup_poll()

        def open_hermes(self) -> None:
            self._refresh_runtime_paths()
            if shutil.which("hermes") is None:
                messagebox.showinfo(self._tr("dialog.hermes"), self._tr("error.install_hermes_first"))
                return
            try:
                subprocess.Popen(["hermes", "desktop", "--local"], creationflags=self._creation_flags())
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.hermes"), str(exc))

        def _preferred(self) -> str | None:
            return None if self.runtime_key == "auto" else self.runtime_key

        def _lane(self, env, *, preferred: str | None = None):
            model = read_hermes_model()
            return choose_lane(
                detect_lanes(env, hermes_model=model),
                zero_cost=True,
                preferred=preferred if preferred is not None else self._preferred(),
            )

        def _command(self, project: Path, task_id: str, prompt: str, lane):
            if lane.engine == "agnes":
                return list(agnes_command(project, task_id, prompt))
            if not lane.model:
                raise RuntimeError(self._tr("error.select_local"))
            return list(hermes_command(project, task_id, prompt, lane.model, provider=lane.provider))

        def _start_ready_probe(self, report=None) -> None:
            if self.setup_probe_running or self.running:
                return
            if report is None:
                _state, _model, report = self._state()
            if not report.zero_cost_ready or not report.ready_lane:
                self.refresh()
                return

            env = self._env()
            try:
                lane = self._lane(env, preferred=report.ready_lane)
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.guard"), str(exc))
                return

            self.setup_probe_running = True
            self.one_click_button.configure(state="disabled")
            self._append(self._tr("setup.probe_running", lane=lane.name))

            def worker():
                try:
                    with tempfile.TemporaryDirectory(prefix="firstwindow-readiness-") as tmp:
                        project = Path(tmp)
                        (project / "AGENTS.md").write_text(
                            "FirstWindow readiness probe only. Do not modify files. "
                            "Reply exactly FIRSTWINDOW_READY and exit.\n",
                            encoding="utf-8",
                        )
                        command = self._command(
                            project,
                            "readiness-probe",
                            "Do not modify files. Reply exactly FIRSTWINDOW_READY and exit.",
                            lane,
                        )
                        result = probe_command(
                            command,
                            project,
                            env=env,
                            timeout=300,
                            expected_text="FIRSTWINDOW_READY",
                        )
                except Exception as exc:
                    self.events.put(("probe_error", (lane.name, str(exc))))
                    return
                self.events.put(("probe_done", (lane.name, result)))

            threading.Thread(target=worker, daemon=True).start()

        def _launch(self, project: Path, task_id: str, prompt: str, lane, env, *, resume_mode: bool, criteria):
            try:
                command = self._command(project, task_id, prompt, lane)
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.runtime"), str(exc))
                return

            self.running = True
            self.start_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            mode = self._tr("button.resume") if resume_mode else self._tr("button.start")
            self._append(self._tr("log.task_route", mode=mode, task_id=task_id, lane=lane.name))
            self._append(self._tr("log.guard_passed"))

            def worker():
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=project,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        env=env,
                    )
                    if process.stdout:
                        for line in process.stdout:
                            self.events.put(("log", line.rstrip()))
                    code = process.wait()
                    append_evidence(
                        project,
                        task_id,
                        "resume-agent-exit" if resume_mode else "agent-exit",
                        code == 0,
                        f"{lane.name} {'resume_' if resume_mode else ''}exit_code={code}",
                        criteria=criteria,
                    )
                    write_checkpoint(
                        project,
                        task_id,
                        "agent-finished" if code == 0 else "agent-failed",
                        "Review evidence and verify."
                        if code == 0
                        else "Inspect failure and resume from the latest checkpoint.",
                    )
                    result_text = self._tr("result.finished") if code == 0 else self._tr("result.failed")
                    self.events.put(
                        (
                            "done",
                            self._tr("log.finished", result=result_text, code=code, task_id=task_id),
                        )
                    )
                except Exception as exc:
                    append_evidence(project, task_id, "launcher", False, str(exc))
                    write_checkpoint(
                        project,
                        task_id,
                        "launcher-failed",
                        "Fix launcher/runtime issue and resume.",
                    )
                    self.events.put(("done", self._tr("log.launcher_failed", error=exc)))

            threading.Thread(target=worker, daemon=True).start()

        def start(self) -> None:
            if self.running:
                return
            project = Path(self.project_var.get()).expanduser()
            task = self.task.get("1.0", "end").strip()
            if not project.is_dir():
                messagebox.showerror(self._tr("dialog.project"), self._tr("error.choose_project"))
                return
            if not task:
                messagebox.showerror(self._tr("dialog.task"), self._tr("error.describe_task"))
                return
            env = self._env()
            try:
                lane = self._lane(env)
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.guard"), str(exc))
                return

            task_id = f"fw-{uuid.uuid4().hex[:10]}"
            create_task(project, task_id, task, ["Agent process exits successfully."])
            write_checkpoint(project, task_id, "dispatching", f"Run with {lane.name}.")
            self._launch(project, task_id, task, lane, env, resume_mode=False, criteria=["AC-001"])

        def resume_latest(self) -> None:
            if self.running:
                return
            project = Path(self.project_var.get()).expanduser()
            if not project.is_dir():
                messagebox.showerror(self._tr("dialog.project"), self._tr("error.choose_project"))
                return
            self.refresh_resume()
            if self.resume_candidate is None:
                messagebox.showinfo(self._tr("dialog.resume"), self._tr("error.no_resume"))
                return
            try:
                context = load_resume_context(project, self.resume_candidate.task_id)
                prompt = build_resume_prompt(context)
                lane = self._lane(self._env())
            except Exception as exc:
                messagebox.showerror(self._tr("dialog.resume"), str(exc))
                return

            if not messagebox.askyesno(
                self._tr("dialog.resume"),
                self._tr(
                    "confirm.resume",
                    task_id=context["task_id"],
                    stage=context["stage"],
                    next_action=context["next_action"],
                ),
            ):
                return

            criteria = None
            acceptance = context.get("acceptance") or []
            if len(acceptance) == 1 and acceptance[0].get("text") == "Agent process exits successfully.":
                criteria = [acceptance[0]["id"]]
            write_checkpoint(project, context["task_id"], "resuming", context["next_action"])
            self._launch(
                project,
                context["task_id"],
                prompt,
                lane,
                self._env(),
                resume_mode=True,
                criteria=criteria,
            )

        def _poll_events(self) -> None:
            try:
                while True:
                    kind, payload = self.events.get_nowait()
                    if kind == "log":
                        self._append(str(payload))
                    elif kind == "refresh":
                        self.one_click_button.configure(state="normal")
                        self.refresh()
                    elif kind == "continue_setup":
                        self.one_click_button.configure(state="normal")
                        self.root.after(100, self.setup_zero_path)
                    elif kind == "probe_done":
                        lane_name, result = payload
                        self.setup_probe_running = False
                        self.one_click_button.configure(state="normal")
                        if result.output:
                            self._append(result.output)
                        if result.passed:
                            self.verified_lane = str(lane_name)
                            _state, _model, current_report = self._state()
                            self.verified_route = route_fingerprint(current_report, self.verified_lane)
                            self._append(self._tr("setup.probe_passed", lane=lane_name))
                            messagebox.showinfo(
                                self._tr("setup.ready_title"),
                                self._tr("setup.ready_message", lane=lane_name),
                            )
                        else:
                            self.verified_lane = None
                            self.verified_route = None
                            reason = result.reason
                            self._append(self._tr("setup.probe_failed", lane=lane_name, reason=reason))
                            messagebox.showerror(
                                self._tr("dialog.verify"),
                                self._tr("setup.probe_failed", lane=lane_name, reason=reason),
                            )
                        self.refresh()
                    elif kind == "probe_error":
                        lane_name, error = payload
                        self.setup_probe_running = False
                        self.one_click_button.configure(state="normal")
                        self.verified_lane = None
                        self.verified_route = None
                        self._append(self._tr("setup.probe_failed", lane=lane_name, reason=error))
                        messagebox.showerror(self._tr("dialog.verify"), str(error))
                        self.refresh()
                    elif kind == "done":
                        self._append(str(payload))
                        self.running = False
                        self.start_button.configure(state="normal")
                        self.refresh()
            except queue.Empty:
                pass
            self.root.after(100, self._poll_events)

    def run_ui_self_test() -> int:
        settings_path = default_settings_path()
        existed = settings_path.exists()
        original = settings_path.read_bytes() if existed else None
        roots = []
        try:
            root = tk.Tk()
            roots.append(root)
            app = App(root)
            root.update_idletasks()

            app.language_var.set(LANGUAGE_NAMES["zh-CN"])
            app._on_language_change()
            root.update_idletasks()
            assert app.language == "zh-CN"
            assert app.one_click_button.cget("text") == translate("zh-CN", "button.one_click_ready")
            assert app.language_label.cget("text") == translate("zh-CN", "label.language")
            assert load_language(settings_path, system_locale="en") == "zh-CN"
            root.destroy()

            root2 = tk.Tk()
            roots.append(root2)
            app2 = App(root2)
            root2.update_idletasks()
            assert app2.language == "zh-CN"
            assert app2.one_click_button.cget("text") == translate("zh-CN", "button.one_click_ready")
            root2.destroy()
            return 0
        except Exception:
            traceback.print_exc()
            return 1
        finally:
            for item in roots:
                try:
                    item.destroy()
                except Exception:
                    pass
            if existed and original is not None:
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                settings_path.write_bytes(original)
            elif not existed:
                settings_path.unlink(missing_ok=True)

    if ui_self_test:
        return run_ui_self_test()

    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
