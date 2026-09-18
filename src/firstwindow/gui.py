from __future__ import annotations

import os
from pathlib import Path
import platform
import queue
import shutil
import subprocess
import threading
import uuid

from .bootstrap import install_command
from .demo_project import create_demo_project
from .durable import append_evidence, create_task, write_checkpoint
from .onboarding import BeginnerState, recommend_next_action
from .resume import build_resume_prompt, discover_resumable_tasks, load_resume_context
from .router import choose_lane, detect_lanes
from .runners import agnes_command, hermes_command
from .system_status import hermes_local_ready, read_hermes_model
from .windows_paths import refresh_runtime_paths


def main() -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class App:
        def __init__(self, root: tk.Tk):
            self.root = root
            self.root.title("FirstWindow")
            self.root.geometry("920x760")
            self.root.minsize(780, 640)
            self.events: queue.Queue[tuple[str, str]] = queue.Queue()
            self.project_var = tk.StringVar()
            self.runtime_var = tk.StringVar(value="Automatic ($0)")
            self.agnes_free_var = tk.BooleanVar(value=False)
            self.status_var = tk.StringVar(value="Checking your computer…")
            self.next_var = tk.StringVar(value="")
            self.resume_var = tk.StringVar(value="No resumable task selected.")
            self.resume_candidate = None
            self.running = False
            self._build()
            self.refresh()
            self.root.after(100, self._poll_events)

        def _build(self) -> None:
            style = ttk.Style()
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

            outer = ttk.Frame(self.root, padding=22)
            outer.pack(fill="both", expand=True)
            ttk.Label(outer, text="FirstWindow", font=("Segoe UI", 22, "bold")).pack(anchor="w")
            ttk.Label(
                outer,
                text="Your first coding agent. Free-first, durable, verified.",
                font=("Segoe UI", 11),
            ).pack(anchor="w", pady=(2, 18))

            status = ttk.LabelFrame(outer, text="1. System check", padding=14)
            status.pack(fill="x")
            ttk.Label(status, textvariable=self.status_var, justify="left").pack(anchor="w")
            ttk.Label(status, textvariable=self.next_var, justify="left").pack(anchor="w", pady=(6, 0))

            buttons = ttk.Frame(status)
            buttons.pack(fill="x", pady=(12, 0))
            ttk.Button(buttons, text="Diagnose", command=self.refresh).pack(side="left")
            ttk.Button(buttons, text="Set Up $0 Path", command=self.setup_zero_path).pack(side="left", padx=8)
            ttk.Button(buttons, text="Install Agnes", command=lambda: self.install("agnes")).pack(side="left", padx=8)
            ttk.Button(buttons, text="Install Hermes", command=lambda: self.install("hermes")).pack(side="left")
            ttk.Button(buttons, text="Hermes Local Models", command=self.open_hermes).pack(side="left", padx=8)

            project_box = ttk.LabelFrame(outer, text="2. Choose a project", padding=14)
            project_box.pack(fill="x", pady=14)
            row = ttk.Frame(project_box)
            row.pack(fill="x")
            ttk.Entry(row, textvariable=self.project_var).pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="Browse…", command=self.choose_project).pack(side="left", padx=(8, 0))
            ttk.Button(row, text="Create Demo", command=self.create_demo).pack(side="left", padx=(8, 0))

            resume_row = ttk.Frame(project_box)
            resume_row.pack(fill="x", pady=(10, 0))
            ttk.Label(resume_row, textvariable=self.resume_var).pack(side="left", fill="x", expand=True)
            ttk.Button(resume_row, text="Refresh Resume", command=self.refresh_resume).pack(side="right")
            self.resume_button = ttk.Button(resume_row, text="Resume", command=self.resume_latest, state="disabled")
            self.resume_button.pack(side="right", padx=(0, 8))

            task_box = ttk.LabelFrame(outer, text="3. Describe what you want", padding=14)
            task_box.pack(fill="both", expand=True)
            self.task = tk.Text(task_box, height=8, wrap="word", font=("Segoe UI", 11))
            self.task.insert("1.0", "Build or improve this project, run the relevant checks, and show evidence before saying it is done.")
            self.task.pack(fill="both", expand=True)

            controls = ttk.Frame(task_box)
            controls.pack(fill="x", pady=(12, 0))
            ttk.Label(controls, text="Runtime:").pack(side="left")
            ttk.Combobox(
                controls,
                textvariable=self.runtime_var,
                state="readonly",
                width=20,
                values=["Automatic ($0)", "Agnes Free", "Hermes Local"],
            ).pack(side="left", padx=8)
            ttk.Checkbutton(
                controls,
                text="I confirmed my Agnes provider is free",
                variable=self.agnes_free_var,
                command=self.refresh,
            ).pack(side="left", padx=8)
            self.start_button = ttk.Button(controls, text="Start Building", command=self.start)
            self.start_button.pack(side="right")

            log_box = ttk.LabelFrame(outer, text="Activity", padding=10)
            log_box.pack(fill="both", expand=True, pady=(14, 0))
            self.log = tk.Text(log_box, height=9, wrap="word", state="disabled", font=("Consolas", 9))
            self.log.pack(fill="both", expand=True)

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
            return state, model

        def refresh(self) -> None:
            state, model = self._state()
            local_name = str(model.get("default") or model.get("model") or "")
            agnes_text = "installed" if state.agnes_installed else "not installed"
            if state.agnes_installed and state.agnes_free_confirmed:
                agnes_text += " · $0 confirmed"
            hermes_text = "not installed"
            if state.hermes_installed:
                hermes_text = "installed"
                if state.hermes_local_ready:
                    hermes_text += f" · local $0 ready ({local_name})"
                else:
                    hermes_text += " · choose a Local Model once"
            self.status_var.set(f"Agnes: {agnes_text}\nHermes: {hermes_text}\n$0 Guard: ON")
            action = recommend_next_action(state)
            self.next_var.set({
                "ready": "Ready. Choose a project and press Start Building.",
                "install": "No runtime detected. “Set Up $0 Path” installs Hermes using its official installer.",
                "configure": "Runtime detected. Finish one-time free/local model setup, then Diagnose again.",
            }[action])
            self.refresh_resume()

        def choose_project(self) -> None:
            path = filedialog.askdirectory(title="Choose your project folder")
            if path:
                self.project_var.set(path)
                self.refresh_resume()

        def create_demo(self) -> None:
            parent = filedialog.askdirectory(title="Choose where to create FirstWindow-Demo")
            if not parent:
                return
            target = Path(parent) / "FirstWindow-Demo"
            try:
                create_demo_project(target)
            except Exception as exc:
                messagebox.showerror("Demo project", str(exc))
                return
            self.project_var.set(str(target))
            self._append(f"Created demo project: {target}")
            self.refresh_resume()

        def refresh_resume(self) -> None:
            project = Path(self.project_var.get()).expanduser()
            self.resume_candidate = None
            self.resume_button.configure(state="disabled")
            if not project.is_dir():
                self.resume_var.set("Choose a project to scan for interrupted tasks.")
                return
            tasks = discover_resumable_tasks(project)
            if not tasks:
                self.resume_var.set("No incomplete durable tasks found.")
                return
            self.resume_candidate = tasks[0]
            item = tasks[0]
            self.resume_var.set(f"Resume {item.task_id} · {item.stage} · next: {item.next_action}")
            if not self.running:
                self.resume_button.configure(state="normal")

        def _creation_flags(self) -> int:
            return subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0

        def install(self, target: str) -> None:
            try:
                command = install_command(platform.system(), target)
            except Exception as exc:
                messagebox.showerror("Setup", str(exc))
                return
            shown = " ".join(command)
            if not messagebox.askyesno(
                "Run official installer?",
                f"FirstWindow will run this documented {target.title()} installer:\n\n{shown}\n\nContinue?",
            ):
                return

            def worker():
                self.events.put(("log", f"Installing {target}…"))
                try:
                    code = subprocess.run(command, check=False, creationflags=self._creation_flags()).returncode
                    if code == 0:
                        added = refresh_runtime_paths(platform.system(), target)
                        if added:
                            self.events.put(("log", "Refreshed runtime PATH for this FirstWindow session."))
                    self.events.put(("log", f"{target} installer exited with code {code}."))
                except Exception as exc:
                    self.events.put(("log", f"{target} installer failed: {exc}"))
                self.events.put(("refresh", ""))

            threading.Thread(target=worker, daemon=True).start()

        def setup_zero_path(self) -> None:
            state, _model = self._state()
            if not state.hermes_installed:
                self.install("hermes")
                return
            if not state.hermes_local_ready:
                self.open_hermes()
                messagebox.showinfo(
                    "Finish local setup",
                    "In Hermes Desktop choose Settings → Providers → Local Models, install the runtime, download a model, then click Use. Return here and press Diagnose.",
                )
                return
            messagebox.showinfo("$0 path", "Hermes Local is already ready.")

        def open_hermes(self) -> None:
            if shutil.which("hermes") is None:
                messagebox.showinfo("Hermes", "Install Hermes first.")
                return
            try:
                subprocess.Popen(["hermes", "desktop"], creationflags=self._creation_flags())
            except Exception as exc:
                messagebox.showerror("Hermes", str(exc))

        def _preferred(self) -> str | None:
            return {"Agnes Free":"agnes-free","Hermes Local":"hermes-local"}.get(self.runtime_var.get())

        def _lane(self, env):
            model = read_hermes_model()
            return choose_lane(
                detect_lanes(env, hermes_model=model),
                zero_cost=True,
                preferred=self._preferred(),
            )

        def _command(self, project: Path, task_id: str, prompt: str, lane):
            if lane.engine == "agnes":
                return list(agnes_command(project, task_id, prompt))
            if not lane.model:
                raise RuntimeError("Select a Hermes Local Model first.")
            return list(hermes_command(project, task_id, prompt, lane.model, provider=lane.provider))

        def _launch(self, project: Path, task_id: str, prompt: str, lane, env, *, resume_mode: bool, criteria):
            try:
                command = self._command(project, task_id, prompt, lane)
            except Exception as exc:
                messagebox.showerror("Runtime", str(exc))
                return

            self.running = True
            self.start_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self._append(f"{'Resume' if resume_mode else 'Task'} {task_id} → {lane.name}")
            self._append("$0 Guard passed. Starting agent…")

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
                        "Review evidence and verify." if code == 0 else "Inspect failure and resume from the latest checkpoint.",
                    )
                    self.events.put(("done", f"{'Finished' if code == 0 else 'Failed'} · exit {code} · task {task_id}"))
                except Exception as exc:
                    append_evidence(project, task_id, "launcher", False, str(exc))
                    write_checkpoint(project, task_id, "launcher-failed", "Fix launcher/runtime issue and resume.")
                    self.events.put(("done", f"Launcher failed: {exc}"))

            threading.Thread(target=worker, daemon=True).start()

        def start(self) -> None:
            if self.running:
                return
            project = Path(self.project_var.get()).expanduser()
            task = self.task.get("1.0", "end").strip()
            if not project.is_dir():
                messagebox.showerror("Project", "Choose an existing project folder.")
                return
            if not task:
                messagebox.showerror("Task", "Describe what you want to build.")
                return
            env = self._env()
            try:
                lane = self._lane(env)
            except Exception as exc:
                messagebox.showerror("$0 Guard", str(exc))
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
                messagebox.showerror("Project", "Choose an existing project folder.")
                return
            self.refresh_resume()
            if self.resume_candidate is None:
                messagebox.showinfo("Resume", "No incomplete durable task is available.")
                return
            try:
                context = load_resume_context(project, self.resume_candidate.task_id)
                prompt = build_resume_prompt(context)
                lane = self._lane(self._env())
            except Exception as exc:
                messagebox.showerror("Resume", str(exc))
                return

            if not messagebox.askyesno(
                "Resume interrupted task?",
                f"Task: {context['task_id']}\nStage: {context['stage']}\nNext: {context['next_action']}\n\nContinue from this checkpoint?",
            ):
                return

            criteria = None
            acceptance = context.get("acceptance") or []
            if len(acceptance) == 1 and acceptance[0].get("text") == "Agent process exits successfully.":
                criteria = [acceptance[0]["id"]]
            write_checkpoint(project, context["task_id"], "resuming", context["next_action"])
            self._launch(project, context["task_id"], prompt, lane, self._env(), resume_mode=True, criteria=criteria)

        def _poll_events(self) -> None:
            try:
                while True:
                    kind, payload = self.events.get_nowait()
                    if kind == "log":
                        self._append(payload)
                    elif kind == "refresh":
                        self.refresh()
                    elif kind == "done":
                        self._append(payload)
                        self.running = False
                        self.start_button.configure(state="normal")
                        self.refresh()
            except queue.Empty:
                pass
            self.root.after(100, self._poll_events)

    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
