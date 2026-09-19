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
        "status.automation_unavailable": "automatic runner unavailable",
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
        "setup.installer_timeout": "{target} installer did not finish within {minutes} minutes. FirstWindow stopped waiting instead of claiming success.",
        "setup.installer_nonzero": "{target} installer exited with code {code}; the runtime is still not considered ready.",
        "setup.installer_fallback": "{reason}\n\nFirstWindow will open the official setup page as a safe fallback.",
        "setup.hermes_local_required": "Hermes is installed, but the current model is not a managed local model. In Hermes Desktop choose Settings → Providers → Local Models, click Install runtime, download a model that fits your machine, then click Use. FirstWindow will keep checking automatically.",
        "setup.ready_configured": "A verified $0 route is configured. FirstWindow will now run a small real readiness probe through {lane}.",
        "setup.probe_running": "Running a real $0 readiness probe through {lane}…",
        "setup.probe_passed": "Real $0 readiness probe passed through {lane}.",
        "setup.probe_failed": "Readiness probe failed through {lane}: {reason}",
        "setup.waiting": "Waiting for Hermes Local Models setup…",
        "setup.watch_expired": "Automatic re-check stopped after 10 minutes. Nothing was marked ready. Finish the external setup, then press Make Me Ready again.",
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
        "status.automation_unavailable": "自动执行能力不可用",
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
        "setup.installer_timeout": "{target} 安装在 {minutes} 分钟内没有完成。FirstWindow 已停止等待，不会把它误判为安装成功。",
        "setup.installer_nonzero": "{target} 安装器退出码为 {code}；当前运行时仍不会被视为已就绪。",
        "setup.installer_fallback": "{reason}\n\nFirstWindow 将打开官方设置页面，作为安全的手动降级路径。",
        "setup.hermes_local_required": "Hermes 已安装，但当前模型不是托管本地模型。请在 Hermes Desktop 中进入 Settings → Providers → Local Models，点击 Install runtime，下载适合本机的模型，再点击 Use。FirstWindow 会自动持续检查。",
        "setup.ready_configured": "已配置可验证的 $0 通道。FirstWindow 现在将通过 {lane} 运行一个小型真实就绪探测。",
        "setup.probe_running": "正在通过 {lane} 运行真实 $0 就绪探测…",
        "setup.probe_passed": "{lane} 的真实 $0 就绪探测已通过。",
        "setup.probe_failed": "{lane} 的就绪探测失败：{reason}",
        "setup.waiting": "正在等待 Hermes 本地模型设置完成…",
        "setup.watch_expired": "自动重检已在 10 分钟后停止。当前没有任何通道被标记为已就绪。完成外部设置后，请再点击“一键就绪”。",
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


# FirstWindow v0.4 execution-route terminology. Kept as a post-table update so
# both catalogs stay structurally identical while older keys remain compatible.
TRANSLATIONS["en"].update({
    "runtime.agnes_free": "Agnes API via Hermes",
    "checkbox.agnes_free": "I confirmed this Agnes API route is free for my account",
    "status.agnes_api_ready": "Agnes API profile configured in Hermes ({model}); live probe required",
    "status.agnes_api_setup_needed": "Agnes API isolated profile needs setup",
    "status.hermes_required": "install Hermes first",
    "next.confirm_agnes": "Agnes API is isolated through Hermes. Confirm the current account route is free, then FirstWindow will verify it.",
    "next.prepare_agnes": "Make Me Ready will create or repair an isolated Hermes profile for Agnes API and remove all fallback providers.",
    "confirm.agnes_free.title": "Confirm $0 Agnes route",
    "confirm.agnes_free": "FirstWindow found the official Agnes API route through an isolated Hermes profile. Agnes publicly offers a Free/default API tier, but account billing can vary. Confirm that this API key/account route should be treated as $0 for this run.",
    "setup.agnes_profile_preparing": "Preparing an isolated Hermes profile for Agnes API with fallback providers disabled...",
    "setup.agnes_profile_ready": "Isolated Hermes -> Agnes API profile is ready; fallback providers are disabled.",
    "setup.agnes_profile_failed": "Could not prepare the isolated Agnes API profile: {reason}",
    "setup.agnes_key_title": "Configure Agnes API key",
    "setup.agnes_key_prompt": "Paste your Agnes API key. It is stored only in FirstWindow's isolated Hermes profile; keys are never copied from your default Hermes profile.",
    "setup.agnes_key_saved": "Agnes API key saved only to the isolated FirstWindow Hermes profile.",
    "setup.agnes_key_profile_missing": "The isolated Hermes profile is unavailable. Run Make Me Ready again.",
    "log.usage_attestation_failed": "Execution evidence rejected: Hermes actually used an unexpected provider/model ({reason}).",
    "error.readiness_required": "This exact route has not passed the live readiness probe. Click Make Me Ready first; FirstWindow will not run on configuration alone.",
})
TRANSLATIONS["zh-CN"].update({
    "runtime.agnes_free": 'Agnes API（通过 Hermes）',
    "checkbox.agnes_free": '我已确认当前 Agnes API 通道对本账号为免费',
    "status.agnes_api_ready": 'Agnes API 已配置到 Hermes（{model}）；仍需通过真实探测',
    "status.agnes_api_setup_needed": '需要准备隔离的 Agnes API 执行配置',
    "status.hermes_required": '请先安装 Hermes',
    "next.confirm_agnes": 'Agnes API 已通过 Hermes 隔离。确认当前账号通道为免费后，FirstWindow 将进行真实验证。',
    "next.prepare_agnes": '“一键就绪”将创建或修复 Agnes API 专用 Hermes 配置，并关闭所有 fallback provider。',
    "confirm.agnes_free.title": '确认 $0 Agnes 通道',
    "confirm.agnes_free": 'FirstWindow 已找到通过隔离 Hermes 配置运行的 Agnes 官方 API。Agnes 公开提供 Free/default API 层，但具体账号计费可能不同。请确认本次 API Key/账号通道应按 $0 使用。',
    "setup.agnes_profile_preparing": '正在准备 Agnes API 专用 Hermes 配置，并关闭 fallback provider…',
    "setup.agnes_profile_ready": 'Hermes -> Agnes API 隔离配置已就绪；fallback provider 已关闭。',
    "setup.agnes_profile_failed": '无法准备 Agnes API 隔离配置：{reason}',
    "setup.agnes_key_title": '配置 Agnes API Key',
    "setup.agnes_key_prompt": '粘贴你的 Agnes API Key。它只会保存到 FirstWindow 专用的隔离 Hermes profile；FirstWindow 不会从默认 Hermes profile 复制任何 Key。',
    "setup.agnes_key_saved": 'Agnes API Key 已仅保存到 FirstWindow 专用隔离 Hermes profile。',
    "setup.agnes_key_profile_missing": '找不到 FirstWindow 隔离 Hermes profile，请重新点击“一键就绪”。',
    "log.usage_attestation_failed": '执行证据被拒绝：Hermes 实际使用了非预期 provider/model（{reason}）。',
    "error.readiness_required": '当前执行通道尚未通过真实就绪探测。请先点击“一键就绪”；FirstWindow 不会仅凭配置状态直接执行。',
})


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


def translate(language_code: str, key: str, **values: object) -> str:
    lang = normalize_language(language_code)
    template = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if template is None:
        template = TRANSLATIONS["en"].get(key, key)
    if not values:
        return template
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template
