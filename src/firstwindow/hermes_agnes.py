from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Callable, Mapping, Sequence

AGNES_PROVIDER = "agnes"
AGNES_MODEL = "agnes-2.5-flash"
AGNES_KEY_ENV = "AGNES_API_KEY"
FIRSTWINDOW_HERMES_PROFILE = "firstwindowzero"
OFFICIAL_AGNES_BASE_URLS = frozenset({
    "https://apihub.agnes-ai.com/v1",
    "https://apihub.agnes-ai.cn/v1",
    "https://api.agnes-ai.cn/v1",
})


@dataclass(frozen=True)
class HermesAgnesRoute:
    hermes_installed: bool
    provider_configured: bool
    selected: bool
    no_fallbacks: bool
    ready: bool
    model: str | None
    base_url: str | None
    key_env: str | None
    profile_home: str | None
    reason: str


@dataclass(frozen=True)
class ProfileSetupResult:
    ready: bool
    created: bool
    profile_home: str | None
    reason: str
    route: HermesAgnesRoute


@dataclass(frozen=True)
class HermesUsageAttestation:
    passed: bool
    provider: str | None
    model: str | None
    api_calls: int
    reason: str


def scoped_env(
    profile_home: str | Path | None,
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    if profile_home:
        # The FirstWindow Agnes profile owns its credential boundary. Do not let
        # an ambient process-level AGNES_API_KEY override the isolated .env.
        env.pop(AGNES_KEY_ENV, None)
        env["HERMES_HOME"] = str(profile_home)
    return env


def _agnes_api_key_value(
    profile_home: str | Path | None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Return the current Agnes key internally without logging it."""
    source = os.environ if env is None else env
    direct = str(source.get(AGNES_KEY_ENV) or "").strip()
    if direct:
        return direct
    if not profile_home:
        return None
    path = Path(profile_home) / ".env"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() != AGNES_KEY_ENV:
            continue
        value = value.strip().strip("\"'")
        if value and value.upper() not in {"YOUR_API_KEY", "YOUR_API_KEY_HERE", "PLACEHOLDER"}:
            return value
        return None
    return None


def agnes_api_key_present(
    profile_home: str | Path | None,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Check credential presence without returning or logging the secret."""
    return _agnes_api_key_value(profile_home, env) is not None


def agnes_api_key_fingerprint(
    profile_home: str | Path | None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Return a non-secret in-memory identity used to invalidate stale route proof.

    The digest is never persisted or logged. It only lets the GUI notice that
    the credential behind a previously verified Agnes route changed.
    """
    secret = _agnes_api_key_value(profile_home, env)
    if secret is None:
        return None
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def save_agnes_api_key(profile_home: str | Path, api_key: str) -> Path:
    """Store an explicitly supplied key only in the isolated Hermes profile.

    This never reads/copies credentials from another Hermes profile. The caller
    must obtain the key directly from the user and must not log it.
    """
    secret = api_key.strip()
    if not secret or any(ch in secret for ch in "\r\n") or any(ch.isspace() for ch in secret):
        raise ValueError("invalid Agnes API key")
    root = Path(profile_home)
    path = root / ".env"
    root.mkdir(parents=True, exist_ok=True)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []

    rendered = f"{AGNES_KEY_ENV}={secret}"
    updated: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key == AGNES_KEY_ENV:
                if not replaced:
                    updated.append(rendered)
                    replaced = True
                continue
        updated.append(line)
    if not replaced:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append(rendered)

    tmp = path.with_name(path.name + ".firstwindow.tmp")
    tmp.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def _run(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    runner: Callable[..., Any] = subprocess.run,
    timeout: int = 30,
):
    return runner(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=None if env is None else dict(env),
        timeout=timeout,
    )


def _json_value(
    key: str,
    *,
    env: Mapping[str, str] | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> Any:
    try:
        completed = _run(["hermes", "config", "get", key, "--json"], env=env, runner=runner, timeout=12)
    except (OSError, subprocess.SubprocessError):
        return None
    if int(getattr(completed, "returncode", 1)) != 0:
        return None
    try:
        return json.loads(str(getattr(completed, "stdout", "") or "").strip())
    except (TypeError, json.JSONDecodeError):
        return None


def read_hermes_agnes_route(
    profile_home: str | Path | None = None,
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., Any] = subprocess.run,
) -> HermesAgnesRoute:
    if which("hermes") is None:
        return HermesAgnesRoute(
            False, False, False, False, False, None, None, None,
            str(profile_home) if profile_home else None, "hermes-not-installed",
        )

    env = scoped_env(profile_home)
    model_cfg = _json_value("model", env=env, runner=runner)
    provider_cfg = _json_value("providers.agnes", env=env, runner=runner)
    fallbacks = _json_value("fallback_providers", env=env, runner=runner)

    model_cfg = model_cfg if isinstance(model_cfg, dict) else {}
    provider_cfg = provider_cfg if isinstance(provider_cfg, dict) else {}
    provider = str(model_cfg.get("provider") or "").strip().lower()
    model = str(model_cfg.get("default") or model_cfg.get("model") or "").strip() or None
    base_url = str(
        provider_cfg.get("api")
        or provider_cfg.get("base_url")
        or model_cfg.get("base_url")
        or ""
    ).strip().rstrip("/") or None
    key_env = str(provider_cfg.get("key_env") or provider_cfg.get("api_key_env") or "").strip() or None
    transport = str(provider_cfg.get("transport") or provider_cfg.get("api_mode") or "").strip().lower()

    provider_configured = bool(
        base_url in OFFICIAL_AGNES_BASE_URLS
        and key_env == AGNES_KEY_ENV
        and transport in {"chat_completions", "chat-completions"}
    )
    selected = bool(provider == AGNES_PROVIDER and model == AGNES_MODEL)
    no_fallbacks = isinstance(fallbacks, list) and len(fallbacks) == 0
    ready = bool(profile_home and provider_configured and selected and no_fallbacks)

    if ready:
        reason = "agnes-hermes-isolated-ready"
    elif not provider_configured:
        reason = "agnes-provider-not-configured"
    elif not selected:
        reason = "agnes-model-not-selected"
    elif profile_home and not no_fallbacks:
        reason = "fallbacks-not-empty"
    else:
        reason = "isolated-profile-not-ready"

    return HermesAgnesRoute(
        True,
        provider_configured,
        selected,
        no_fallbacks,
        ready,
        model,
        base_url,
        key_env,
        str(profile_home) if profile_home else None,
        reason,
    )


_PROFILE_PATH_RE = re.compile(r"^\s*Path:\s*(.+?)\s*$", re.MULTILINE)


def parse_profile_path(text: str) -> str | None:
    match = _PROFILE_PATH_RE.search(text or "")
    return match.group(1).strip() if match else None


def find_firstwindow_profile(
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> str | None:
    try:
        completed = _run(
            ["hermes", "profile", "show", FIRSTWINDOW_HERMES_PROFILE],
            runner=runner,
            timeout=12,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if int(getattr(completed, "returncode", 1)) != 0:
        return None
    return parse_profile_path(str(getattr(completed, "stdout", "") or ""))


def read_firstwindow_agnes_route(
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., Any] = subprocess.run,
) -> HermesAgnesRoute:
    profile_home = find_firstwindow_profile(runner=runner) if which("hermes") else None
    return read_hermes_agnes_route(profile_home, which=which, runner=runner)


def ensure_firstwindow_agnes_profile(
    *,
    runner: Callable[..., Any] = subprocess.run,
    which: Callable[[str], str | None] = shutil.which,
    recreate: bool = False,
) -> ProfileSetupResult:
    if which("hermes") is None:
        route = HermesAgnesRoute(
            False, False, False, False, False, None, None, None, None,
            "hermes-not-installed",
        )
        return ProfileSetupResult(False, False, None, "hermes-not-installed", route)

    existing = find_firstwindow_profile(runner=runner)
    created = False

    if recreate and existing:
        deleted = _run(
            ["hermes", "profile", "delete", FIRSTWINDOW_HERMES_PROFILE, "--yes"],
            runner=runner,
            timeout=45,
        )
        if int(getattr(deleted, "returncode", 1)) != 0:
            route = read_hermes_agnes_route(existing, which=which, runner=runner)
            return ProfileSetupResult(False, False, existing, "profile-delete-failed", route)
        existing = None

    if not existing:
        created_result = _run(
            [
                "hermes", "profile", "create", FIRSTWINDOW_HERMES_PROFILE,
                "--no-alias", "--no-skills",
                "--description", "FirstWindow isolated Agnes API execution profile. No fallback providers or copied credentials.",
            ],
            runner=runner,
            timeout=120,
        )
        if int(getattr(created_result, "returncode", 1)) != 0:
            route = HermesAgnesRoute(
                True, False, False, False, False, None, None, None, None,
                "profile-create-failed",
            )
            return ProfileSetupResult(False, False, None, "profile-create-failed", route)
        created = True
        existing = find_firstwindow_profile(runner=runner)

    if not existing:
        route = HermesAgnesRoute(
            True, False, False, False, False, None, None, None, None,
            "profile-path-unavailable",
        )
        return ProfileSetupResult(False, created, None, "profile-path-unavailable", route)

    env = scoped_env(existing)
    settings = (
        ("model.default", AGNES_MODEL),
        ("model.provider", AGNES_PROVIDER),
        ("model.base_url", "https://apihub.agnes-ai.com/v1"),
        ("providers.agnes.api", "https://apihub.agnes-ai.com/v1"),
        ("providers.agnes.key_env", AGNES_KEY_ENV),
        ("providers.agnes.transport", "chat_completions"),
        ("providers.agnes.default_model", AGNES_MODEL),
        ("fallback_providers", "[]"),
    )
    for key, value in settings:
        try:
            completed = _run(
                ["hermes", "config", "set", key, value, "--force"],
                env=env,
                runner=runner,
                timeout=20,
            )
        except (OSError, subprocess.SubprocessError):
            route = read_hermes_agnes_route(existing, which=which, runner=runner)
            return ProfileSetupResult(False, created, existing, f"config-set-error:{key}", route)
        if int(getattr(completed, "returncode", 1)) != 0:
            route = read_hermes_agnes_route(existing, which=which, runner=runner)
            return ProfileSetupResult(False, created, existing, f"config-set-failed:{key}", route)

    route = read_hermes_agnes_route(existing, which=which, runner=runner)
    return ProfileSetupResult(route.ready, created, existing, route.reason, route)


def attest_hermes_usage(
    path: Path,
    *,
    expected_model: str,
    allowed_providers: frozenset[str] = frozenset({"custom", "agnes"}),
) -> HermesUsageAttestation:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return HermesUsageAttestation(False, None, None, 0, "usage-missing-or-invalid")

    if not isinstance(data, dict):
        return HermesUsageAttestation(False, None, None, 0, "usage-invalid-shape")

    provider = str(data.get("provider") or "").strip().lower() or None
    model = str(data.get("model") or "").strip() or None
    try:
        api_calls = int(data.get("api_calls") or 0)
    except (TypeError, ValueError):
        api_calls = 0

    if data.get("failed") is True or data.get("completed") is not True:
        return HermesUsageAttestation(False, provider, model, api_calls, "usage-not-completed")
    if model != expected_model:
        return HermesUsageAttestation(False, provider, model, api_calls, "unexpected-model")
    if provider not in allowed_providers:
        return HermesUsageAttestation(False, provider, model, api_calls, "unexpected-provider")
    if api_calls < 1:
        return HermesUsageAttestation(False, provider, model, api_calls, "no-api-call")
    return HermesUsageAttestation(True, provider, model, api_calls, "ok")
