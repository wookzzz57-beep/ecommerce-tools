from __future__ import annotations

import json
import locale
import os
from pathlib import Path
from typing import Mapping


SUPPORTED_LANGUAGES = ("en", "zh-CN")
LANGUAGE_NAMES = {"en": "English", "zh-CN": "简体中文"}


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app.subtitle": "Your first coding agent. Free-first, durable, verified.",
        "label.language": "Language",
        "section.system": "1. System check",
        "section.project": "2. Choose a project",
        "section.task": "3. Describe what you want",
        "section.activity": "Activity",
        "button.diagnose": "Diagnose",
        "button.one_click_ready": "Make Me Ready",
        "button.agnes_desktop": "Get Agnes Desktop",
        "button.hermes_desktop": "Get Hermes Desktop",
        "button.hermes_local": "Hermes Local Models",
        "label.advanced": "Advanced CLI fallback:",
        "button.agnes_cli": "Agnes CLI",
        "button.hermes_cli": "Hermes CLI",
        "button.browse": "Browse…",
        "button.create_demo": "Create Demo",
        "button.refresh_resume": "Refresh Resume",
        "button.resume": "Resume",
        "label.runtime": "Runtime:",
        "runtime.auto": "Automatic ($0)",
        "runtime.agnes_free": "Agnes Free",
        "runtime.hermes_local": "Hermes Local",
        "checkbox.agnes_free": "I confirmed my Agnes provider is free",
        "button.start": "Start Building",
        "task.default": "Build or improve this project, run the relevant checks, and show evidence before saying it is done.",
        "status.checking": "Checking your computer…",
        "resume.none_selected": "No resumable task selected.",
        "resume.choose_project": "Choose a project to scan for interrupted tasks.",
        "resume.none_found": "No incomplete durable tasks found.",
        "resume.item": "Resume {task_id} · {stage} · next: {next_action}",
        "status.installed": "installed",
        "status.not_installed": "not installed",
        "status.zero_confirmed": "$0 confirmed",
        "status.local_ready": "local $0 ready ({model})",
        "status.choose_local": "choose a Local Model once",
        "status.guard_on": "$0 Guard: ON",
        "status.summary": "Agnes: {agnes}\nHermes: {hermes}\n{guard}",
        "next.ready": "Route is configured. Press Make Me Ready to run a real $0 readiness probe, or choose a project and start.",
        "next.install": "No safe $0 runtime is ready. Make Me Ready can install Hermes with one explicit confirmation.",
        "next.configure": "Hermes is installed but no managed Local Model is selected. Make Me Ready will open the exact Local Models step.",
        "dialog.setup": "Setup",
        "dialog.project": "Project",
        "dialog.task": "Task",
        "dialog.runtime": "Runtime",
        "dialog.guard": "$0 Guard",
        "dialog.resume": "Resume",
        "dialog.demo": "Demo project",
        "dialog.hermes": "Hermes",
        "dialog.one_click": "One-Click Ready",
        "dialog.verify": "Verify $0 lane",
        "choose.project": "Choose your project folder",
        "choose.demo_parent": "Choose where to create FirstWindow-Demo",
        "error.choose_project": "Choose an existing project folder.",
        "error.describe_task": "Describe what you want to build.",
        "error.no_resume": "No incomplete durable task is available.",
        "error.select_local": "Select a Hermes Local Model first.",
        "error.install_hermes_first": "Install Hermes first.",
        "confirm.resume": "Task: {task_id}\nStage: {stage}\nNext: {next_action}\n\nContinue from this checkpoint?",
        "confirm.installer.title": "Run official installer?",
        "confirm.installer": "FirstWindow will run this documented {target} installer:\n\n{command}\n\nContinue?",
        "confirm.hermes_install": "Hermes is not installed. Run the allowlisted official Hermes installer now?\n\nIf you choose No, FirstWindow will open the official Desktop download page instead.",
        "setup.opened": "Opened official {target} Desktop setup page: {url}",
        "setup.browser_manual": "Your browser did not confirm opening the page. Open this official URL manually:\n\n{url}",
        "setup.installing": "Installing {target}…",
        "setup.path_refreshed": "Refreshed runtime PATH for this FirstWindow session.",
        "setup.installer_exit": "{target} installer exited with code {code}.",
        "setup.installer_failed": "{target} installer failed: {error}",
        "setup.hermes_local_required": "Hermes is installed, but the current model is not a managed local model. In Hermes Desktop choose Settings → Providers → Local Models, click Install runtime, download a model that fits your machine, then click Use. FirstWindow will keep checking automatically.",
        "setup.ready_configured": "A verified $0 route is configured. FirstWindow will now run a small real readiness probe through {lane}.",
        "setup.probe_running": "Running a real $0 readiness probe through {lane}…",
        "setup.probe_passed": "Real $0 readiness probe passed through {lane}.",
        "setup.probe_failed": "Readiness probe failed through {lane}: {reason}",
        "setup.waiting": "Waiting for Hermes Local Models setup…",
        "setup.ready_title": "$0 path verified",
        "setup.ready_message": "The {lane} route completed a real readiness probe successfully.",
        "log.created_demo": "Created demo project: {path}",
        "log.task_route": "{mode} {task_id} → {lane}",
        "log.guard_passed": "$0 Guard passed. Starting agent…",
        "log.finished": "{result} · exit {code} · task {task_id}",
        "result.finished": "Finished",
        "result.failed": "Failed",
        "log.launcher_failed": "Launcher failed: {error}",
        "language.changed": "Language changed to {language}.",
    },
    "zh-CN": {
        "app.subtitle": "你的第一个编程 Agent。免费优先、可恢复、可验证。",
        "label.language": "语言",
        "section.system": "1. 系统检查",
        "section.project": "2. 选择项目",
        "section.task": "3. 描述你想完成的任务",
        "section.activity": "活动记录",
        "button.diagnose": "诊断",
        "button.one_click_ready": "一键就绪",
        "button.agnes_desktop": "获取 Agnes Desktop",
        "button.hermes_desktop": "获取 Hermes Desktop",
        "button.hermes_local": "Hermes 本地模型",
        "label.advanced": "高级 CLI 备用方案：",
        "button.agnes_cli": "Agnes CLI",
        "button.hermes_cli": "Hermes CLI",
        "button.browse": "浏览…",
        "button.create_demo": "创建演示项目",
        "button.refresh_resume": "刷新恢复任务",
        "button.resume": "继续任务",
        "label.runtime": "运行通道：",
        "runtime.auto": "自动（$0）",
        "runtime.agnes_free": "Agnes 免费通道",
        "runtime.hermes_local": "Hermes 本地",
        "checkbox.agnes_free": "我已确认当前 Agnes 提供商免费",
        "button.start": "开始构建",
        "task.default": "构建或改进这个项目，运行相关检查，并在宣称完成前给出可验证证据。",
        "status.checking": "正在检查你的电脑…",
        "resume.none_selected": "尚未选择可恢复任务。",
        "resume.choose_project": "先选择项目文件夹，再扫描中断任务。",
        "resume.none_found": "没有发现未完成的持久化任务。",
        "resume.item": "继续 {task_id} · {stage} · 下一步：{next_action}",
        "status.installed": "已安装",
        "status.not_installed": "未安装",
        "status.zero_confirmed": "已确认 $0",
        "status.local_ready": "本地 $0 已就绪（{model}）",
        "status.choose_local": "需要选择一次本地模型",
        "status.guard_on": "$0 防护：开启",
        "status.summary": "Agnes：{agnes}\nHermes：{hermes}\n{guard}",
        "next.ready": "通道已配置。点击“一键就绪”进行真实 $0 探测，或选择项目后直接开始。",
        "next.install": "当前没有安全的 $0 通道。“一键就绪”可在一次明确确认后安装 Hermes。",
        "next.configure": "Hermes 已安装，但尚未选择托管本地模型。“一键就绪”会打开准确的本地模型设置步骤。",
        "dialog.setup": "设置",
        "dialog.project": "项目",
        "dialog.task": "任务",
        "dialog.runtime": "运行通道",
        "dialog.guard": "$0 防护",
        "dialog.resume": "继续任务",
        "dialog.demo": "演示项目",
        "dialog.hermes": "Hermes",
        "dialog.one_click": "一键就绪",
        "dialog.verify": "验证 $0 通道",
        "choose.project": "选择你的项目文件夹",
        "choose.demo_parent": "选择 FirstWindow-Demo 的创建位置",
        "error.choose_project": "请选择一个已存在的项目文件夹。",
        "error.describe_task": "请描述你想完成的任务。",
        "error.no_resume": "当前没有可恢复的未完成任务。",
        "error.select_local": "请先选择 Hermes 本地模型。",
        "error.install_hermes_first": "请先安装 Hermes。",
        "confirm.resume": "任务：{task_id}\n阶段：{stage}\n下一步：{next_action}\n\n从此检查点继续吗？",
        "confirm.installer.title": "运行官方安装器？",
        "confirm.installer": "FirstWindow 将运行官方记录的 {target} 安装命令：\n\n{command}\n\n继续吗？",
        "confirm.hermes_install": "Hermes 尚未安装。现在运行白名单内的官方 Hermes 安装器吗？\n\n如果选择“否”，FirstWindow 将改为打开官方 Desktop 下载页面。",
        "setup.opened": "已打开官方 {target} Desktop 设置页：{url}",
        "setup.browser_manual": "浏览器未确认已打开页面。请手动打开这个官方地址：\n\n{url}",
        "setup.installing": "正在安装 {target}…",
        "setup.path_refreshed": "已刷新本次 FirstWindow 会话的运行时 PATH。",
        "setup.installer_exit": "{target} 安装器退出码：{code}。",
        "setup.installer_failed": "{target} 安装失败：{error}",
        "setup.hermes_local_required": "Hermes 已安装，但当前模型不是托管本地模型。请在 Hermes Desktop 中进入 Settings → Providers → Local Models，点击 Install runtime，下载适合本机的模型，再点击 Use。FirstWindow 会自动持续检查。",
        "setup.ready_configured": "已配置可验证的 $0 通道。FirstWindow 现在将通过 {lane} 运行一个小型真实就绪探测。",
        "setup.probe_running": "正在通过 {lane} 运行真实 $0 就绪探测…",
        "setup.probe_passed": "{lane} 的真实 $0 就绪探测已通过。",
        "setup.probe_failed": "{lane} 的就绪探测失败：{reason}",
        "setup.waiting": "正在等待 Hermes 本地模型设置完成…",
        "setup.ready_title": "$0 通道已验证",
        "setup.ready_message": "{lane} 已成功完成真实就绪探测。",
        "log.created_demo": "已创建演示项目：{path}",
        "log.task_route": "{mode} {task_id} → {lane}",
        "log.guard_passed": "$0 防护已通过。正在启动 Agent…",
        "log.finished": "{result} · 退出码 {code} · 任务 {task_id}",
        "result.finished": "已完成",
        "result.failed": "失败",
        "log.launcher_failed": "启动器失败：{error}",
        "language.changed": "语言已切换为 {language}。",
    },
}


def normalize_language(value: str | None) -> str:
    normalized = (value or "").strip().replace("_", "-").lower()
    if normalized.startswith("zh"):
        return "zh-CN"
    if normalized.startswith("en"):
        return "en"
    return "en"


def _system_locale() -> str | None:
    try:
        value = locale.getlocale()[0]
    except (ValueError, TypeError):
        value = None
    return value or os.environ.get("LANG")


def default_settings_path() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "FirstWindow" / "settings.json"
    return Path.home() / ".config" / "firstwindow" / "settings.json"


def load_language(path: Path | None = None, *, system_locale: str | None = None) -> str:
    settings_path = path or default_settings_path()
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        saved = data.get("language") if isinstance(data, Mapping) else None
        if saved in SUPPORTED_LANGUAGES:
            return str(saved)
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return normalize_language(system_locale if system_locale is not None else _system_locale())


def save_language(language: str, path: Path | None = None) -> None:
    value = normalize_language(language)
    settings_path = path or default_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, object] = {}
    try:
        parsed = json.loads(settings_path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            existing.update(parsed)
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    existing["language"] = value
    settings_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def translate(language: str, key: str, **values: object) -> str:
    lang = normalize_language(language)
    template = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if template is None:
        template = TRANSLATIONS["en"].get(key, key)
    if not values:
        return template
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template
